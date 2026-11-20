# RepoMind

**Understand. Investigate. Improve.**

RepoMind is an AI-powered codebase intelligence platform that helps software engineers understand, navigate, debug, analyse and improve unfamiliar codebases. It combines AST parsing, semantic retrieval, a code knowledge graph, multi-agent orchestration, and sandboxed execution into one developer tool.

> **Status**: early, actively developed. See [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for exactly what is implemented vs. pending, and [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md) for the feature-by-feature delivery history. Nothing marked "pending" there exists yet — this README does not claim otherwise.

## Architecture

```
repomind/
  frontend/          Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui
  backend/
    app/
      main.py         FastAPI app factory
      core/           config, structured logging, exceptions
      api/routes/     HTTP routes (thin; logic lives in services/)
      models/         SQLAlchemy models
      schemas/        Pydantic schemas
      services/       business logic (github/, indexing/, parsing/, graph/, retrieval/, llm/, agents/, security/)
      workers/        Celery tasks
      mcp/            MCP server & tools
    tests/
  infrastructure/
    docker/           Dockerfiles for backend, worker, frontend
    nginx/            reverse proxy config (added when deployment phase lands)
  scripts/
  docs/
  docker-compose.yml
```

Data ownership (no duplication of source of truth):
- **PostgreSQL** — application metadata: users, workspaces, repositories, indexing jobs, conversations, investigations, PR reviews, usage records.
- **Neo4j** — the code knowledge graph: files, symbols, calls, imports, inheritance.
- **Qdrant** — vector embeddings for semantic code retrieval.
- **Redis** — cache and Celery broker/result backend.

## Tech stack

- **Frontend**: Next.js, React, TypeScript (strict), Tailwind CSS, shadcn/ui, Radix UI, TanStack Query, Zustand, React Flow, Monaco Editor, Recharts, Zod.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Celery.
- **Data**: PostgreSQL, Redis, Neo4j, Qdrant.
- **AI**: LangGraph, MCP, provider adapters for OpenAI/Anthropic/Gemini/Ollama, Tree-sitter for AST parsing.
- **Infra**: Docker, Docker Compose, GitHub Actions.

## Local development setup

### Prerequisites

- Node.js 20+ (developed against v22)
- Python 3.12+
- `git` CLI on PATH — the indexing pipeline shells out to it to clone repositories and list tracked files; it never executes anything from a cloned repo
- Docker Desktop (for Postgres/Redis/Neo4j/Qdrant) — **not yet verified in this repo's primary dev environment**; see Troubleshooting.

### 1. Clone and configure environment

```bash
git clone https://github.com/rajayush16/RepoMind.git
cd RepoMind
cp .env.example .env
# fill in real secrets in .env — never commit it
```

### 2. Start infrastructure (Postgres, Redis, Neo4j, Qdrant)

```bash
docker compose up -d postgres redis neo4j qdrant
```

### 3. Backend

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate   # Windows (Git Bash: source .venv/Scripts/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/health` — reports the real connectivity status of each dependency (Postgres/Redis/Neo4j/Qdrant), not a hardcoded "ok".

In a second terminal, start the Celery worker (required for `POST /repositories/{id}/index` to actually run — the route only enqueues the job):

```bash
cd backend
. .venv/Scripts/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`.

### 5. Full stack via Docker Compose (once all phases land)

```bash
docker compose up --build
```

## Environment variables

See [`.env.example`](.env.example) for the full list (app secrets, Postgres/Redis/Neo4j/Qdrant connection strings, GitHub OAuth credentials, LLM provider keys, observability keys). Copy it to `.env` and fill in real values — placeholders only are committed to the repo.

## Running tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run lint && npm run build
```

## Sandboxed test execution

Test Generation runs LLM-generated test code only inside ephemeral, network-disabled Docker containers (`app/services/sandbox/docker_runner.py`) -- never in the backend/worker process itself. Build the sandbox images once before using it:

```bash
docker build -t repomind-sandbox-python -f infrastructure/docker/sandbox-python.Dockerfile .
docker build -t repomind-sandbox-node -f infrastructure/docker/sandbox-node.Dockerfile .
```

Both images run as a non-root user with dependencies (pytest / Jest) pre-installed, so no package install happens at test-run time. If Docker (or these images) aren't available, execution honestly reports `sandbox_unavailable` instead of ever claiming a test passed without actually running it. Only `pytest` and `jest` are supported; JUnit (which needs a compile step) is not implemented yet.

## Troubleshooting

- **Docker not installed / `docker compose` not found**: install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows and ensure the `docker` CLI is on PATH. Until then, the backend will boot but `/api/health` will report Postgres/Redis/Neo4j/Qdrant as `unreachable`.
- **`/api/health` shows services as `unreachable`**: expected if the corresponding container/service isn't running. Start it with `docker compose up -d <service>` and retry.
- **GitHub OAuth not working**: register a GitHub OAuth App at <https://github.com/settings/developers> and set `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `GITHUB_OAUTH_CALLBACK_URL` in `.env`. The callback URL must point at the **backend** (`http://localhost:8000/api/auth/github/callback`), not the frontend.
- **LLM features return errors**: at least one of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` must be set, or `OLLAMA_BASE_URL` pointed at a running Ollama instance. The full provider-agnostic LLM abstraction lands in Phase 6.
- **`POST /repositories/{id}/index` returns 503**: the Celery broker (Redis) or no worker process is running. Start Redis and the worker (see step 3 above).
- **Indexing succeeds but shows 0 "graph relationships" or 0 "embeddings"**: expected when Neo4j isn't running or `OPENAI_API_KEY` isn't set — both are best-effort steps that never fail the job; the Postgres-backed file/symbol index (`file_count`/`symbol_count` on the repository) is what must succeed. Start Neo4j and/or set `OPENAI_API_KEY`, then re-index.
- **Test execution shows `sandbox_unavailable`**: Docker isn't reachable from the backend/worker process, or the `repomind-sandbox-python`/`repomind-sandbox-node` images haven't been built yet (see "Sandboxed test execution" above).
- **Bug Investigation / PR Review / Test Generation return 422 "No LLM provider configured"**: same requirement as the AI Assistant — set at least one LLM provider's API key in `.env`.

## Deployment

Deployment documentation will be added once the application reaches production readiness (Phase 9 of `IMPLEMENTATION_PLAN.md`).

## Contributing

Work proceeds feature-by-feature on the `develop` branch, with each feature committed and pushed only after it is actually implemented and tested. See `DEVELOPMENT_LOG.md` for history.
