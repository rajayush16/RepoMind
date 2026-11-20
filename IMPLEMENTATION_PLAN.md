# RepoMind — Implementation Plan

Tracks progress against the full product spec, phase by phase. Checked items have been implemented, tested where applicable, and pushed to `develop`. Unchecked items are not started — no code for them exists yet, and nothing below should be read as "mocked" or "simulated."

Local dev environment note: Docker Desktop is not currently installed in the primary dev environment used so far, so Postgres/Redis/Neo4j/Qdrant containers have not been booted or verified end-to-end. All config is written to the real spec; verification of actual container startup and DB connectivity is pending Docker installation.

## Phase 1 — Architecture & Foundation
- [x] Monorepo structure (`frontend/`, `backend/`, `infrastructure/`, `scripts/`, `docs/`)
- [x] `docker-compose.yml` for Postgres, Redis, Neo4j, Qdrant, backend, worker, frontend
- [x] Backend Dockerfile, worker Dockerfile, frontend Dockerfile
- [x] `.env.example` with all required variables
- [x] FastAPI app factory, structured JSON logging, exception handlers
- [x] Real `/api/health` endpoint (checks Postgres/Redis/Neo4j/Qdrant connectivity, reports actual status per dependency)
- [x] Backend test for health endpoint
- [ ] Verified `docker compose up` boots all services (blocked: Docker not installed locally)

## Phase 2 — Frontend Application Shell
- [x] Next.js 15 App Router + TypeScript strict + Tailwind + shadcn/ui scaffold
- [x] Design tokens / dark theme matching spec (colors, fonts)
- [x] Persistent app shell: sidebar, topbar, collapsible right panel
- [x] Command palette (Cmd/Ctrl+K)
- [x] Landing page (marketing, static content only)
- [x] Stub pages for all sidebar sections with honest empty states (no fake data)
- [ ] Demo workspace with seeded sample data

## Phase 3 — Authentication & GitHub Integration
- [x] Email/password auth (registration, login, logout, session handling via httpOnly
      JWT cookies)
- [x] GitHub OAuth (authorize redirect, CSRF state cookie, code exchange, account
      upsert)
- [x] Workspace + workspace membership model (personal workspace auto-created per user)
- [x] Repository discovery via GitHub API (`GET /repositories/github/available`)
- [x] Secure (Fernet-encrypted) GitHub token storage at rest
- [x] Repository connect / list / delete
- [x] Frontend: login/register pages, GitHub OAuth button, auth guard on `(app)`
      routes, repositories page wired to real connect/discover/delete, topbar +
      settings show the real signed-in user with a working logout
- [ ] Workspace switching UI (multiple workspaces per user) — only a personal
      workspace exists so far
- [ ] End-to-end verification against a real Postgres instance (blocked: Docker not
      installed locally; verified instead via an in-memory SQLite test harness — see
      DEVELOPMENT_LOG.md)
- [ ] Live GitHub OAuth round-trip verification (blocked: no registered GitHub OAuth
      App / real client credentials in this environment; URL building, CSRF state,
      and callback logic are unit-tested with mocked GitHub responses)

## Phase 4 — Indexing Pipeline
- [x] Celery worker setup (`app/workers/celery_app.py` + `tasks.py`, Redis broker;
      verified the worker process boots and registers the `index_repository` task)
- [x] Repository clone/fetch in a controlled environment (shallow `git clone` via
      subprocess only -- never executes anything from the cloned repo; branch name
      validated, tokens redacted from error messages, temp dir always cleaned up)
- [x] File filtering (exclusion dirs/filenames, 1MB size limit, `.gitignore`
      respected via `git ls-files`)
- [x] Tree-sitter AST parsing for all 6 target languages (Python, JS, TS, Java,
      C++, Go), via a pluggable per-language registry so more languages can be
      added without touching the pipeline
- [x] Symbol extraction (functions/methods/classes/interfaces/structs, with
      parent/signature/line range) and import extraction for all 6 languages;
      call extraction with best-effort syntactic (not fully semantic) caller
      resolution
- [x] PostgreSQL persistence of indexing metadata (`indexing_jobs`,
      `indexed_files`, `code_symbols` -- see Alembic migration `a35bbb58389e`)
- [x] Qdrant embedding storage (code written and real against a configured OpenAI
      key; **not exercised** in this environment -- no `OPENAI_API_KEY` configured,
      and no running Qdrant -- fails gracefully, job still succeeds, 0 embeddings
      recorded honestly rather than faked)
- [x] Neo4j graph construction (code written and real; **not exercised** in this
      environment -- no running Neo4j -- fails gracefully, job still succeeds, 0
      relationships recorded honestly rather than faked)
- [x] Indexing progress reporting via polling (`GET
      /repositories/{id}/indexing-jobs/latest`; frontend polls every 2s while a job
      is queued/running)
- [ ] True incremental (commit-diff-aware) re-indexing -- not implemented. Every
      index/re-index currently does a full delete-and-reinsert of that repository's
      `indexed_files`/`code_symbols` rows (and Neo4j subgraph), which is correct and
      idempotent (verified: re-running produces no duplicate rows) but always
      re-parses every file rather than only changed ones. The spec explicitly
      allows full re-index as a fallback; recorded here as a real scope cut, not an
      oversight.
- [ ] Live end-to-end verification against real Postgres/Neo4j/Qdrant/Redis+worker
      (blocked: Docker not installed locally). What **is** verified for real,
      without any mocking, in this environment: git cloning a repository (against a
      local git fixture, since there's no outbound network access here either),
      `.gitignore`-respecting file filtering, Tree-sitter parsing for all 6
      languages, and the full pipeline (clone → parse → persist → idempotent
      re-index → failure handling) against an in-memory SQLite harness. GitHub API
      calls and the Celery broker call are mocked in the relevant route/pipeline
      tests; everything else in this phase is exercised against real local
      processes (git, tree-sitter, a real Celery worker boot).

## Phase 5 — Code Intelligence
- [ ] Code explorer (file tree, Monaco, symbol navigation)
- [ ] Hybrid retrieval (lexical + vector + symbol + graph, RRF fusion)
- [ ] Architecture graph visualization (React Flow, backed by Neo4j)
- [ ] Source citations wired to retrieval results

## Phase 6 — AI Assistant
- [ ] LLM provider abstraction (OpenAI/Anthropic/Gemini/Ollama)
- [ ] Streaming responses (SSE)
- [ ] LangGraph planner/router workflow
- [ ] Conversation persistence
- [ ] Evidence verification / "insufficient evidence" handling

## Phase 7 — Advanced Agents
- [ ] Bug investigation agent + timeline UI
- [ ] Change impact analysis (Neo4j-driven)
- [ ] Pull request review agent (preview + explicit publish approval)
- [ ] Test generation agent
- [ ] Sandboxed Docker test execution

## Phase 8 — MCP & Observability
- [ ] MCP server with scoped tools
- [ ] Langfuse tracing
- [ ] OpenTelemetry traces
- [ ] Prometheus-compatible metrics
- [ ] Audit logging

## Phase 9 — Quality & Production Readiness
- [ ] Full automated test suites (backend/frontend/e2e)
- [ ] Security audit pass
- [ ] Performance benchmark suite
- [ ] CI/CD (GitHub Actions) — lightweight version added in Phase 1; full matrix pending later phases
- [ ] Deployment documentation
