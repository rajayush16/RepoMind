# Development Log

Chronological record of feature-by-feature delivery. Each entry corresponds to one pushed commit.

## 2026-11-20 — Monorepo scaffold and project docs

- **Summary**: Initialized the repo, docs, and env/gitignore scaffolding.
- **Backend**: none yet.
- **Frontend**: none yet.
- **Database**: none yet.
- **Tests run**: n/a.
- **Commit**: `8eefd79` — `chore: initialize monorepo scaffold and project docs`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: none.

## 2026-11-20 — FastAPI backend foundation with real health checks

- **Summary**: FastAPI app factory, pydantic-settings config, structured logging,
  exception handlers, and a `/api/health` endpoint that performs real connection
  attempts against Postgres, Redis, Neo4j and Qdrant. Added Docker Compose for the
  four infra services plus backend, backend Dockerfile, and a CI job running backend
  tests.
- **Backend components added**: `app/main.py`, `app/core/{config,logging,exceptions}.py`,
  `app/api/routes/health.py`, `app/services/health.py`.
- **Frontend**: none yet.
- **Database**: none yet (no models/migrations — deferred to Phase 4).
- **Tests run**: `pytest` — 1 passed. Manually verified `uvicorn app.main:app` boots and
  `curl /api/health` returns real per-dependency status (`unreachable: TimeoutError` /
  `unreachable: ConnectTimeout` for all four, since no Docker services are running in
  this environment).
- **Commit**: `fbb22f2` — `feat: add FastAPI backend foundation with real health checks`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: Postgres/Redis/Neo4j/Qdrant connectivity not verified against real
  running containers (Docker not installed locally).

## 2026-11-20 — Next.js frontend foundation, design system, app shell, landing page

- **Summary**: Scaffolded Next.js 15 (App Router, TypeScript strict, Tailwind v4,
  shadcn/ui on Radix). Customized the dark theme tokens in `globals.css` to the spec's
  palette (background #090B10, surfaces #11151D/#151A23, violet/indigo primary, cyan
  secondary, restrained emerald/amber/red), set dark mode as default, and fixed a
  `--font-sans` self-reference bug left by the shadcn preset generator. Built the
  persistent app shell (sidebar with the full nav list, topbar with breadcrumb + user
  menu, collapsible right contextual panel via a Zustand store) and a working Cmd/Ctrl+K
  command palette that navigates real routes. Built the marketing landing page (navbar,
  hero with an illustrative product-preview mockup, features, how-it-works, architecture
  showcase, supported languages, use cases, security, CTA, footer). Added a stub page for
  every sidebar section (`/overview`, `/repositories`, `/explorer`, `/architecture`,
  `/assistant`, `/investigations`, `/impact`, `/pull-requests`, `/tests`, `/analytics`,
  `/settings`) using a shared `EmptyState` component — each states plainly which
  IMPLEMENTATION_PLAN phase it depends on, with no fake data and no non-functional
  buttons. Added the frontend Dockerfile (multi-stage) and wired it + a frontend CI job
  (lint + build) in.
- **Backend**: none.
- **Frontend components added**: `components/layout/{sidebar,topbar,right-panel,
  command-palette,app-shell}.tsx`, `components/shared/empty-state.tsx`,
  `components/marketing/*.tsx`, `stores/ui-store.ts`, `lib/{nav-items,route-labels}.ts`,
  13 routes under `src/app/`.
- **Database**: none.
- **Tests run**: `npm run lint` — clean. `npm run build` — succeeds, all 13 routes
  prerendered as static content. Manually started `npm run dev` and curled every route
  (all return 200, no server errors in the dev log); verified landing page contains
  "Finally understood" and `/overview` contains the real empty-state copy.
- **Commit**: `900fe87` — `feat: add Next.js frontend foundation, design system, app shell, landing page`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: no demo workspace with seeded sample data yet; no authentication, so
  `(app)` routes are reachable without being signed in (expected until Phase 3 lands).

## 2026-11-20 — Backend: auth, GitHub OAuth, workspaces, repository connect/discover

- **Summary**: SQLAlchemy models for `users`, `workspaces`, `workspace_members`,
  `repositories` (portable `GUID` type: native UUID on Postgres, `CHAR(36)` on
  SQLite for tests), plus a hand-written Alembic migration (autogenerate needs a
  live DB, which isn't available). Email/password auth with bcrypt password hashing
  and httpOnly JWT access/refresh cookies. Real GitHub OAuth: authorize redirect
  with a CSRF state cookie, code exchange, user upsert (matched by `github_id` then
  email), Fernet-encrypted access token stored at rest and never exposed via any API
  response. Repository discovery via the GitHub API, connect/list/delete endpoints,
  all scoped through a workspace-membership dependency to the user's auto-created
  personal workspace.
- **Backend components added**: `models/{base,user,workspace,repository}.py`,
  `core/{database,security}.py`, `api/deps.py`,
  `api/routes/{auth,repositories,workspaces}.py`,
  `services/auth/{user_service,workspace_service}.py`,
  `services/github/{oauth,client}.py`, Alembic migration `9c48096e893a`.
- **Frontend**: none in this commit.
- **Database**: `users`, `workspaces`, `workspace_members`, `repositories` tables
  defined via Alembic migration `9c48096e893a`. **Not yet applied to a real
  Postgres instance** (Docker still isn't installed here) — migration syntax was
  checked (`alembic history` parses it, and the file's AST was validated), but
  `alembic upgrade head` has not been run against a live database.
- **Tests run**: `pytest` — 14 passed, against an in-memory SQLite harness
  (`tests/conftest.py`) with dependency overrides for `get_db`/`get_settings`
  (production code still only ever targets Postgres; SQLite is test-only). Covers
  register/login/logout/me, GitHub OAuth authorize-URL + CSRF-state construction,
  and repository connect/list/delete/discovery with the GitHub HTTP calls mocked.
  Also booted the real server with no `.env` present and confirmed
  `POST /api/auth/register` fails with a genuine `ConnectionRefusedError` from
  asyncpg (not a fabricated success), and `GET /api/auth/github/login` correctly
  reports GitHub OAuth as unconfigured rather than redirecting with fake
  credentials. Caught and fixed one real bug in this pass: cookies were marked
  `Secure` whenever `environment != "development"`, which silently broke the test
  client's cookie jar over plain HTTP in the `"test"` environment.
- **Commit**: `01cc331` — `feat: add auth, GitHub OAuth, workspaces and repository connect/discover`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: no live Postgres verification (Docker not installed); no live
  GitHub OAuth round-trip (no registered GitHub OAuth App / real credentials in this
  environment) — URL building, state CSRF, and callback logic are unit-tested with
  mocked GitHub responses only; only a personal workspace exists (no multi-workspace
  switching).

## 2026-11-20 — Frontend: auth pages, GitHub OAuth button, protected routes

- **Summary**: TanStack Query provider wired into the root layout. `/login` and
  `/register` pages (Zod-validated forms, GitHub OAuth button linking straight to
  the backend's real `/api/auth/github/login`). `AuthGuard` client component
  protecting every `(app)` route by calling `/api/auth/me` and redirecting to
  `/login` when unauthenticated. Repositories page rewritten to call the real
  backend: lists connected repositories, and — once GitHub is connected — lists
  available GitHub repos with working Connect/Disconnect actions. Topbar and a new
  Settings page now show the real signed-in user (name, email, GitHub connection
  status) with a working Log out action. Sidebar workspace selector now shows the
  real workspace name via a new `GET /api/workspaces/current` endpoint instead of a
  hardcoded "Personal Workspace" label. Landing-page CTAs ("Connect GitHub" /
  "Explore Demo") were corrected: "Connect GitHub" now links directly to the real
  OAuth flow, and "Explore Demo" was renamed to "Sign in" since no demo workspace
  exists yet and the old label would have been misleading now that `(app)` routes
  require real authentication.
- **Backend**: none in this commit — the sidebar now calls `GET
  /api/workspaces/current`, which was already added and tested in the previous
  backend commit (`01cc331`).
- **Frontend components added**: `app/providers.tsx`, `app/(auth)/{layout,login,
  register}`, `components/auth/{login-form,github-button,auth-guard}.tsx`,
  `components/repositories/{repository-card,available-repo-row}.tsx`,
  `components/shared/github-icon.tsx` (lucide-react v1 dropped brand icons, so this
  is a small inline SVG), `lib/api-client.ts`, `lib/types.ts`,
  `lib/queries/{auth,repositories,workspace}.ts`, `lib/validation/auth.ts`.
- **Database**: none.
- **Tests run**: `npm run lint` — clean. `npm run build` — succeeds, all 15 routes.
  Caught and fixed two real build-time bugs in this pass: `lucide-react`'s installed
  major version no longer exports a `Github` icon (replaced with a local inline SVG
  everywhere it was used), and `/login`'s `useSearchParams()` call needed a
  `Suspense` boundary (moved the page's content into `LoginForm` and wrapped it).
- **Commit**: `ed299bb` — `feat: wire frontend to real auth, GitHub OAuth, and repositories API`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: the full auth flow has not been exercised against a real running
  backend+Postgres+browser in this environment (Docker not installed); verified via
  `npm run build`/`lint` and by reading the request/response contract against the
  backend's own passing tests. No demo/workspace-switching UI yet.

## 2026-11-20 — Backend: indexing pipeline (clone, Tree-sitter parsing, Celery, Neo4j/Qdrant best-effort)

- **Summary**: The full Phase 4 indexing pipeline. A shallow `git clone` service
  (subprocess only, branch name validated against a strict pattern, access tokens
  redacted from any error output, temp dir always cleaned up). File filtering that
  excludes common build/dependency/secret paths and respects `.gitignore` via `git
  ls-files`. A pluggable Tree-sitter parsing registry covering all 6 target
  languages (Python, JavaScript, TypeScript, Java, C++, Go) that extracts
  functions/methods/classes/interfaces/structs (with parent/signature/line range),
  imports, and best-effort syntactic call references. Three new Postgres tables
  (`indexing_jobs`, `indexed_files`, `code_symbols`) with deterministic
  `stable_symbol_id`s so re-indexing the same commit never creates duplicate rows.
  A Celery app + thin task wrapper around the real orchestration function
  (`run_indexing`), which the task just calls via `asyncio.run` -- the fat, testable
  logic lives in a plain async function, not inside the Celery task itself. Neo4j
  graph writing and Qdrant embedding writing (via a new `EmbeddingProvider`
  abstraction, OpenAI-backed) are both best-effort: either being unreachable, or no
  embedding provider being configured, is recorded honestly as 0 written / a skip
  reason, and never fails the overall job -- only the Postgres symbol index has to
  succeed. New endpoints: `POST /repositories/{id}/index` (enqueues the task, 409 if
  already in progress, 503 if the broker is unreachable) and `GET
  /repositories/{id}/indexing-jobs/latest` (for polling).
- **Backend components added**: `models/indexing.py`
  (IndexingJob/IndexedFile/CodeSymbol), `services/indexing/{clone,filters,
  pipeline}.py`, `services/parsing/{types,languages,extractor}.py`,
  `services/graph/builder.py`, `services/retrieval/qdrant_store.py`,
  `services/llm/embeddings.py`, `workers/{celery_app,tasks}.py`, new routes on
  `api/routes/repositories.py`, `core/exceptions.py` additions (`ConflictError`,
  `ServiceUnavailableError`), Alembic migration `a35bbb58389e`.
- **Frontend**: `lib/queries/indexing.ts` (polling hook with a 2s interval while a
  job is queued/running), and `RepositoryCard` now has a real Index/Re-index button
  with live progress and error display.
- **Database**: `indexing_jobs`, `indexed_files`, `code_symbols` tables defined via
  Alembic migration `a35bbb58389e`. **Not yet applied to a real Postgres instance**
  (Docker still isn't installed here).
- **Tests run**: `pytest` — 32 passed (18 new: 6 parsing tests covering real
  Tree-sitter extraction for every target language with no mocking; 4 clone/filter
  tests against a real local git fixture repo, including rejecting a malicious
  `--upload-pack=` branch name; 3 full-pipeline tests -- clone→parse→persist,
  idempotent re-index producing no duplicate rows, and failure handling -- against
  the SQLite harness with only the clone source swapped to the local fixture; 5
  route tests for trigger/conflict/broker-unavailable/polling with the Celery
  `.delay()` call and GitHub API mocked). Also booted a real `celery -A
  app.workers.celery_app worker` process and the real FastAPI server to confirm
  both come up cleanly with every new route/task registered.
  Caught and fixed three real bugs in this pass, none related to missing
  infrastructure: (1) `redis==5.2.1` is incompatible with Celery 5.4.0's Redis
  transport, which requires redis-py ≥6.1.0 -- the worker crashed with
  `VersionMismatch` on startup; bumped to `redis==6.4.0`. (2) The Celery app never
  imported `tasks.py`, so `index_repository` wasn't registered with the worker at
  all (`[tasks]` printed empty) -- fixed via `include=["app.workers.tasks"]`. (3)
  `shutil.rmtree(..., ignore_errors=True)` silently left cloned repos behind on
  Windows because git marks pack files read-only; switched to an `onerror` handler
  that clears the read-only bit and retries.
- **Commit**: `d04d293` — `feat: add repository indexing pipeline (clone, Tree-sitter parsing, Celery)`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: no live verification against real Postgres, Neo4j, Qdrant, or
  Redis+worker (Docker not installed); no outbound network access in this
  environment either, so GitHub cloning was verified against a local git fixture
  rather than a real GitHub repo, and GitHub API calls are mocked in tests. No
  OpenAI API key configured, so embedding generation code is written but has never
  actually produced an embedding. True incremental (commit-diff) re-indexing is not
  implemented -- every run is a full re-index (idempotent, but not incremental).

## 2026-11-20 — Frontend: wire repository cards to the indexing pipeline

- **Summary**: `RepositoryCard` now has a real Index/Re-index button, polls the
  indexing-job endpoint every 2s while a job is in progress, and surfaces the real
  error message on failure.
- **Frontend components added**: `lib/queries/indexing.ts`.
- **Tests run**: `npm run lint` clean, `npm run build` succeeds.
- **Commit**: `9153120` — `feat: wire frontend repository cards to the real indexing pipeline`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: none beyond what Phase 4's backend entry already notes.

## 2026-11-20 — Backend + frontend: Code Explorer, hybrid retrieval, architecture graph

- **Summary**: Added a `content` column to `indexed_files` (capped at the same 1MB
  indexing limit) so the Code Explorer can serve real source without re-cloning or
  re-hitting the GitHub API per file view -- see Alembic migration `1f2ae4ba51cc`.
  Built hybrid retrieval (`services/retrieval/hybrid.py`): lexical (portable
  `ILIKE`, not Postgres-only `tsvector`, so it's testable on SQLite too) + symbol
  (prefix match) + vector (Qdrant, best-effort) + graph (Neo4j, best-effort),
  fused via Reciprocal Rank Fusion. New Neo4j query helpers
  (`services/graph/queries.py`): `get_repository_graph` (nodes/edges for the
  architecture view, honestly reporting `available: false` with a reason when
  Neo4j is unreachable instead of returning fake data), `get_callers`,
  `get_dependents` (the latter two will be reused for Phase 7 impact analysis).
  New endpoints: `GET /repositories/{id}/files`, `GET
  /repositories/{id}/files/content`, `GET /repositories/{id}/symbols`, `GET
  /repositories/{id}/search`, `GET /repositories/{id}/graph`. Frontend: a real Code
  Explorer (file tree built from indexed files, Monaco showing real stored source,
  a symbol outline with jump-to-line, a search box backed by the real hybrid-search
  endpoint) and a real Architecture Graph page (React Flow, fetching real nodes/
  edges, with an honest empty state when Neo4j is unreachable rather than a fake
  diagram). Added a shared repository-selector (Zustand store) used by both pages.
- **Backend components added**: `services/retrieval/hybrid.py`,
  `services/graph/queries.py`, `api/routes/{code,search,architecture}.py`,
  `schemas/{code,search,graph}.py`, Alembic migration `1f2ae4ba51cc`.
- **Frontend components added**: `app/(app)/explorer/page.tsx` (rewritten),
  `app/(app)/architecture/page.tsx` (rewritten),
  `components/explorer/{file-tree-view,symbol-outline}.tsx`,
  `components/repositories/repository-selector.tsx`, `lib/{file-tree,
  graph-layout,monaco-language}.ts`, `lib/queries/code.ts`,
  `stores/repository-store.ts`.
- **Database**: `indexed_files.content` column added via migration `1f2ae4ba51cc`.
  Not yet applied to a real Postgres instance (Docker still isn't installed here).
- **Tests run**: `pytest` — 38 passed (6 new: 5 Code Explorer/search/architecture
  route tests running the real pipeline against the SQLite harness + a local git
  fixture, confirming file listing, file content retrieval, symbol filtering,
  lexical/symbol search results, and the architecture endpoint's honest
  `available: false` when Neo4j is unreachable; 1 test with a mocked Neo4j driver
  verifying `get_repository_graph`'s node/edge ID construction). `npm run lint`
  clean, `npm run build` succeeds (15 routes). Caught and fixed one real bug in
  this pass (not an infra-availability issue): the backend's CALLS edges
  referenced node IDs (`name:{caller}`/`name:{callee}`) that never matched any
  node the endpoint actually returns (`symbol:{file}:{name}`), which would have
  made every call edge silently invisible in the rendered graph; also hit (and
  worked around) a missing `colorMode` prop on the installed `@xyflow/react`
  version during the frontend build.
- **Commit**: `de4243b` — `feat: add Code Explorer, hybrid retrieval, and architecture graph`
- **Push status**: pushed to `origin/develop`.
- **Limitations**: the vector and graph retrieval paths, and the architecture
  graph's real data, are not exercised against a live Qdrant/Neo4j (Docker not
  installed) -- verified instead via the SQLite-backed lexical/symbol paths and a
  mocked-driver unit test for the graph-shaping logic. No demo/sample repository;
  Code Explorer and Architecture Graph only show data for a repository you've
  actually connected and indexed yourself.

## 2026-11-20 — Backend + frontend: AI Assistant (LLM providers, SSE, conversations)

- **Summary**: A common `LLMProvider` interface (`generate`, `generate_stream`,
  `generate_structured`, `count_tokens`) with one real httpx-based adapter each for
  OpenAI, Anthropic, Gemini, and Ollama (no heavy SDKs -- consistent with how
  GitHub/Qdrant are called elsewhere in this codebase). Each adapter takes an
  injectable `httpx.Transport` purely for testability. The registry
  (`get_llm_provider`) never silently falls back to a different provider than
  `DEFAULT_LLM_PROVIDER` -- a missing API key raises instead of guessing another
  provider. New `conversations`/`messages` tables (migration `da32ba5a8376`), each
  message recording which provider/model actually produced it. The orchestrator
  (`services/assistant/orchestrator.py`) retrieves evidence via Phase 5's hybrid
  search, and -- critically -- the citations persisted are that real retrieved
  evidence, never anything the model claims about itself, so they can't be
  hallucinated; when retrieval finds nothing, the model is never even called, and
  a deterministic "insufficient evidence" message is returned instead. Real
  Server-Sent Events streaming over a POST endpoint (`token`/`done`/`error`
  events). Frontend: a working chat UI (conversation list, streaming message
  bubbles, citation chips that deep-link to the Code Explorer at the cited
  file/line via a new `?file=&line=` query param on that page) using a hand-rolled
  SSE-over-fetch parser, since the browser's `EventSource` API can't send POST
  requests.
- **Backend components added**: `services/llm/base.py`,
  `services/llm/providers/{openai,anthropic,gemini,ollama}.py`,
  `services/llm/registry.py`, `services/assistant/orchestrator.py`,
  `models/conversation.py`, `api/routes/assistant.py`,
  `schemas/conversation.py`, `core/database.get_session_factory`, Alembic
  migration `da32ba5a8376`. Also fixed `default_llm_model`'s config default, which
  was hardcoded to an Anthropic model name and would have been silently (and
  wrongly) applied to whichever provider was actually selected.
- **Frontend components added**: `app/(app)/assistant/page.tsx` (rewritten),
  `components/assistant/{conversation-list,message-bubble,citation-chip}.tsx`,
  `components/explorer/explorer-view.tsx` (Explorer page's content moved here so
  it could read a `?file=` deep-link query param), `lib/{stream-ask}.ts`,
  `lib/queries/assistant.ts`.
- **Database**: `conversations`, `messages` tables added via migration
  `da32ba5a8376`. Not yet applied to a real Postgres instance (Docker still isn't
  installed here).
- **Tests run**: `pytest` — 51 passed (13 new: 10 provider-adapter tests against
  `httpx.MockTransport` covering OpenAI/Anthropic/Gemini/Ollama request
  construction and streaming-response parsing plus the registry's
  never-silently-falls-back behavior, and 3 full assistant-flow tests -- streaming
  an answer and persisting real citations, skipping the model entirely when
  retrieval finds nothing, and rejecting the request when no provider is
  configured -- against the SQLite harness with a repository actually indexed
  from a local git fixture, using a deterministic fake provider in place of a real
  one. Also ran the complete suite against a from-scratch virtual environment
  installing only from `requirements.txt` (51 passed), to confirm the newly added
  `langgraph`/`langchain-core` pins don't conflict with anything else. `npm run
  lint` clean, `npm run build` succeeds (15 routes). Caught and fixed a real bug in
  this pass: a `Depends(get_db)` session closes right after a route function
  *returns*, which happens before a `StreamingResponse` body is actually consumed
  by the client -- the streaming generator would have been committing to an
  already-closed session. Fixed with an injectable session-factory dependency that
  the generator opens its own session from, scoped to its own lifetime; this was
  caught by the SQLite-backed assistant-flow tests actually exercising the full
  streaming path, not by inspection.
- **Commit**: `c07607c` — `feat: add AI Assistant (LLM provider abstraction, SSE streaming, conversations)`
  (backend) and `7e07d7a` — `feat: add real AI Assistant chat UI with streaming and citations` (frontend)
- **Push status**: both pushed to `origin/develop`.
- **Limitations**: none of the four provider adapters have been verified against
  a real, live API (no API keys configured, no outbound network access in this
  environment) -- they're built to match each provider's publicly documented
  request/response shape from training knowledge, which may not exactly match the
  current real API. The Assistant's retrieve-then-stream flow is a direct async
  function, not a LangGraph graph (LangGraph is used for Phase 7's Bug
  Investigation agent instead, where the orchestration genuinely has multiple
  stages) -- see IMPLEMENTATION_PLAN.md for the reasoning.

## 2026-11-20 — Backend + frontend: Phase 7 advanced agents (bug investigation, impact analysis, PR review, test generation + sandbox)

- **Summary**: **Bug Investigation** -- a real LangGraph `StateGraph` (parse_issue
  → find_related_symbols → trace_execution → evaluate_causes → prepare_findings),
  the first genuine use of LangGraph in this project. Each stage persists an
  `InvestigationStep` row for the timeline UI; if hybrid search finds no evidence
  at all, the model is never called. **Impact Analysis** -- direct callers and
  their files from the Neo4j graph only, with a plain caller-count risk heuristic;
  no speculative AI commentary layered on top. **PR Review** -- fetches real PR
  metadata/diffs via new GitHub API client functions, one structured LLM call
  produces categorized findings, persisted as a preview; publishing is a
  *separate* endpoint requiring `confirm: true`, never automatic. **Test
  Generation + sandboxed execution** -- generates tests for a real, already-
  indexed symbol, then runs them in ephemeral, network-disabled Docker containers
  (non-root, read-only root FS, memory/CPU limits) built from two new prebuilt
  sandbox images with pytest/Jest pre-installed; a test is never reported
  "passed" unless a real container actually ran it and exited 0 -- when Docker
  isn't reachable, it honestly reports `sandbox_unavailable`.
- **Backend components added**: `models/{investigation,pull_request,
  generated_test}.py`, `services/agents/{stack_trace,bug_investigation,pr_review,
  test_generation,test_execution}.py`, `services/graph/impact.py`,
  `services/sandbox/docker_runner.py`, `api/routes/{investigations,impact,
  pull_requests,tests}.py`, `schemas/{investigation,impact,pull_request,
  test_generation}.py`, new GitHub client functions (`get_pull_request`,
  `get_pull_request_files`, `post_issue_comment`), 3 new Celery tasks, Alembic
  migration `6cdb346f2ed4`, two new sandbox Dockerfiles.
- **Frontend components added**: `app/(app)/{investigations,impact,pull-requests,
  tests}/page.tsx` (all rewritten with real functionality),
  `components/investigations/investigation-timeline.tsx`,
  `components/pull-requests/finding-card.tsx`,
  `lib/queries/{investigations,impact,pull-requests,test-generation}.ts`.
- **Database**: `investigations`, `investigation_steps`, `pull_request_reviews`,
  `review_findings`, `generated_tests`, `test_executions` tables added via
  migration `6cdb346f2ed4`. Not yet applied to a real Postgres instance (Docker
  still isn't installed here).
- **Tests run**: `pytest` — 78 passed (27 new, across 8 new test files) covering
  all four agents against the SQLite harness with a repository actually indexed
  from a local git fixture, a deterministic fake LLM provider, and mocked GitHub
  API calls; plus a genuinely real (not mocked) test of the sandbox's honest
  degradation, since Docker truly isn't installed in this environment. Also
  re-ran the complete suite against a from-scratch virtual environment installing
  only from `requirements.txt` (confirmed the new `docker` SDK pin doesn't
  conflict with anything). `npm run lint` clean, `npm run build` succeeds (15
  routes). Caught and fixed three real bugs, none related to missing
  infrastructure: (1) a Neo4j query parameter named `query` collided with
  `AsyncSession.run()`'s own first positional argument of the same name, raising
  a `TypeError` -- caught by a mocked-driver regression test, not live Neo4j. (2)
  Joining multiple extracted stack-trace search terms into one space-separated
  string for hybrid search, which could never match anything since the lexical/
  symbol paths do substring matching -- fixed by querying each term
  independently and merging/deduping results. (3) Assigning directly to an
  unloaded SQLAlchemy relationship collection (`investigation.steps = []`)
  implicitly lazy-loads the *existing* collection first (to diff against), which
  is itself async I/O outside the async-aware context that requires, raising
  `MissingGreenlet` -- fixed by constructing the response schema explicitly from
  plain column attributes instead of touching the ORM relationship.
- **Commit**: pending (written just before committing).
- **Push status**: pending.
- **Limitations**: none of the four agents' LLM-backed steps, nor PR review's
  publish-to-GitHub call, have been verified against a real API (no API keys, no
  outbound network access in this environment). JUnit test generation/execution
  is not implemented (would need a compile step) -- requesting it returns
  `unsupported_framework` honestly. The sandbox images
  (`repomind-sandbox-python`/`repomind-sandbox-node`) have never actually been
  built or run, since Docker isn't installed here.

