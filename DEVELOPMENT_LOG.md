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
- **Commit**: pending (this entry is written just before committing).
- **Push status**: pending.
- **Limitations**: no demo workspace with seeded sample data yet; no authentication, so
  `(app)` routes are reachable without being signed in (expected until Phase 3 lands).

