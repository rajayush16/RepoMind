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
- [ ] Email/password auth (registration, login, logout, session handling)
- [ ] GitHub OAuth
- [ ] Workspace + workspace membership model
- [ ] Repository discovery via GitHub API
- [ ] Secure (encrypted) GitHub token storage
- [ ] Repository connect / list / delete

## Phase 4 — Indexing Pipeline
- [ ] Celery worker setup
- [ ] Repository clone/fetch in controlled environment
- [ ] File filtering (exclusions, size limits, .gitignore respect)
- [ ] Tree-sitter AST parsing (Python, JS, TS, Java, C++, Go)
- [ ] Symbol/import/call/inheritance extraction
- [ ] PostgreSQL persistence of indexing metadata
- [ ] Qdrant embedding storage
- [ ] Neo4j graph construction
- [ ] Indexing progress reporting (SSE/polling)
- [ ] Incremental (commit-aware) re-indexing

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
