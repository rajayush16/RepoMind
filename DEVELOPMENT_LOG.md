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
- **Commit**: pending (written just before committing).
- **Push status**: pending.
- **Limitations**: the full auth flow has not been exercised against a real running
  backend+Postgres+browser in this environment (Docker not installed); verified via
  `npm run build`/`lint` and by reading the request/response contract against the
  backend's own passing tests. No demo/workspace-switching UI yet.

