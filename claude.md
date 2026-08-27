# Project Progress Log

A running record of work done with Claude on the Digital Payment Wallet, so
context survives across sessions. Newest entries at the top.

---

## Phase 2 — Deployment migration: AWS EC2 → distributed free tier

**Branch:** `feature/nextjs-frontend` (continues from Phase 1)
**Status:** code + config + docs done; local Docker stack re-verified. Nothing
deployed to the cloud yet — that's a manual, account-gated set of steps in
`deployment_guide.md`.

### Goal
Move off the single EC2 box to: **Vercel** (Next.js frontend), **Render**
(FastAPI + Celery), **Neon/Supabase** (Postgres), **Upstash** (Redis). Drive
deploys from GitHub, delete `deploy.sh`.

### What was done

**Backend — now fully environment-driven**
- `app/core/database.py` — `_normalize_database_url()` upgrades a plain
  `postgres://` / `postgresql://` string (what Neon/Supabase/Render hand out) to
  `postgresql+psycopg_async://`. Added `pool_pre_ping=True` for free-tier DBs
  that drop idle connections. Local compose URL (already `+psycopg_async`) passes
  through untouched.
- `app/worker.py` — reads `REDIS_URL`; when it's `rediss://` (Upstash TLS) sets
  `broker_use_ssl` / `redis_backend_use_ssl` (CERT_REQUIRED, or CERT_NONE if the
  URL says so). Added `broker_connection_retry_on_startup = True`. Removed the
  unused `asyncio` import.
- `app/main.py` — CORS now builds its allow-list from `FRONTEND_URL` (+ always
  localhost:3000) and an `allow_origin_regex` defaulting to
  `https://.*\.vercel\.app` (Vercel preview deploys); override via
  `FRONTEND_URL_REGEX`. Replaces the old `CORS_ORIGINS` var.
- `app/core/security.py` — `SECRET_KEY` from env (dev fallback kept);
  `ACCESS_TOKEN_EXPIRE_MINUTES` from env.

**Deploy config (new files)**
- `render.yaml` — Render Blueprint: one **free** Web Service `wallet-api`,
  `startCommand: honcho start`, `healthCheckPath: /openapi.json`,
  `SECRET_KEY` auto-generated, `DATABASE_URL`/`REDIS_URL`/`FRONTEND_URL` as
  dashboard secrets, `autoDeploy: true` on `main`.
- `Procfile` — `web:` uvicorn + `worker:` celery. `honcho` runs both in the one
  free Render service (Render's dedicated worker type is paid — documented as
  "Option B"). `honcho` added to `requirements.txt`.
- `.env.example` (repo root) — backend env vars; `!.env.example` added to root
  `.gitignore`.
- `frontend/next.config.mjs` — the `/api/*` dev proxy rewrite is skipped when
  `process.env.VERCEL` is set (prod calls the absolute Render URL directly).
- `frontend/.env.example` — documents `NEXT_PUBLIC_API_BASE` = absolute Render
  URL for Vercel.

**Docs**
- `deployment_guide.md` — full step-by-step: Neon → Upstash → Render → Vercel →
  wire CORS, env-var reference tables, CI/CD behaviour, troubleshooting.
- `README.md` — split architecture into "Production" (new distributed diagram)
  and "Local development" (compose diagram); deployment section points to the
  guide.
- Deleted `deploy.sh`.

### Not done / follow-ups
- No live cloud deployment performed (needs the user's accounts).
- `render.yaml` `branch: main` — Phase 1/2 work is on `feature/nextjs-frontend`;
  merge to `main` before the first Render deploy, or change the branch.
- In-memory reset tokens (`app/api/routes/auth.py`) still lost on the free
  service's frequent restarts — fine given the demo_token fallback.
- Backend `pytest` suite still has the pre-existing failures noted in Phase 1.

---

## Phase 1 — Frontend migration: Streamlit → Next.js

**Branch:** `feature/nextjs-frontend` (off `feature/async-and-scale`)
**Status:** implementation complete; full stack verified via Docker + Playwright.

### Goal
Replace the Streamlit UI with a production-looking Next.js (React) + Tailwind
frontend, wired to the existing FastAPI backend, served through Nginx.

### What was done

**Frontend — new `frontend/` app**
- Next.js 14 (App Router), TypeScript, Tailwind CSS v3, `output: standalone`.
- `src/lib/api.ts` — typed client for every backend route. Base path
  `NEXT_PUBLIC_API_BASE` (default `/api`).
- `src/lib/auth.tsx` — `AuthProvider` / `useAuth()`. JWT stored in
  `localStorage`, decoded client-side for `sub` + `exp`; loads user + wallet.
- Route groups:
  - `(auth)/` — `login`, `register` (shows generated UPI ID), `forgot-password`
    (recover + reset). Redirects to `/dashboard` when already signed in.
  - `(app)/` — `dashboard`, `add-funds`, `transfer`, `history`, `settings`.
    Guarded; wrapped in `AppShell` (responsive sidebar, balance card).
- Features wired: OAuth2 login, registration, password recover/reset/change,
  delete account (email confirm), balance, UPI lookup w/ debounced verify,
  recent contacts, P2P transfer, cursor-paginated history ("Load more").

**Backend**
- `app/main.py` — added `CORSMiddleware` (origins from `CORS_ORIGINS`, default
  `localhost:3000`). Only needed when the frontend runs standalone in dev;
  behind Nginx everything is same-origin.
- `requirements.txt` — dropped `streamlit`, `pandas`, `requests`.

**Infra**
- Deleted `frontend.py`, `Dockerfile.frontend`.
- `frontend/Dockerfile` — multi-stage, runs Next standalone server on `:3000`.
- `docker-compose.yml` — `frontend` service builds `./frontend`, exposes `3000`,
  `NEXT_PUBLIC_API_BASE=/api` build arg. Added healthchecks + `depends_on:
  condition: service_healthy` for db/redis/api/frontend, and
  `restart: unless-stopped` on all services.
- `nginx/nginx.conf` — `/` → `frontend:3000`, `/api/` → `api:8000` (prefix
  stripped). **Uses `resolver 127.0.0.11` + a variable in `proxy_pass`** so
  Nginx re-resolves service DNS at request time.
- New root `.dockerignore` (keeps `frontend/`, venvs, `.git` out of the API
  image).

### Bug fixed this session: 502 Bad Gateway on `/api/*`
Nginx's `upstream` block resolved the `api` container's IP once at startup.
After `docker compose up -d --build` recreated `api` at a new IP, Nginx kept
proxying to the dead address → `connect() failed (111: Connection refused)`.
Fix: runtime DNS resolution in `nginx.conf` (see above). Also switched
healthchecks from `localhost` to `127.0.0.1` (Alpine `localhost` resolved to
`::1` first, where the servers don't listen).

### Tests
- **Playwright E2E** in `frontend/e2e/` (`auth.spec.ts`, `wallet.spec.ts`,
  `helpers.ts`). `playwright.config.ts` targets `E2E_BASE_URL` (default
  `http://localhost`, the Nginx entrypoint).
- Run: `docker compose up -d --build`, then `cd frontend && npm run test:e2e`.
- Covers: auth redirect guard, register→UPI, login + balance, bad credentials,
  logout, add funds (+ over-limit rejection), P2P transfer with balance/history
  assertions, invalid-UPI block, change password. **10/10 green.**
- **CI:** `.github/workflows/ci.yml` — job 1 runs frontend lint/typecheck/build;
  job 2 brings up the Docker stack with `--wait` and runs the Playwright suite.

**Backend `pytest` suite (`tests/`) — pre-existing failures, NOT caused by this
work.** Verified by re-running with the `app/main.py` change stashed: identical
results. `tests/test_auth.py::test_register_user` and both
`tests/test_transactions.py` tests fail with `sqlalchemy.exc.MissingGreenlet`
(session-scoped async fixtures + module-level engine under pytest-asyncio 1.4).
`tests/test_transactions.py` also has stale assumptions (hard-coded UPI IDs like
`alice.smith@wallet`, a `GET /wallets/{id}` route that doesn't exist). Left
alone — fixing it is a separate task. The Playwright suite covers the same
backend behaviour end-to-end over real HTTP.
Run backend tests (host): create `wallet_test_db` in the db container, then
`./walletEnv/bin/python -m pytest tests/`.

### How to run the stack
```bash
docker compose up -d --build        # http://localhost
# API docs: http://localhost:8000/docs
```
Frontend-only dev: `cd frontend && npm install && npm run dev` (proxies
`/api/*` to `API_PROXY_TARGET`, default `http://localhost:8000`).

### Follow-ups / not done
- No CI workflow yet (would run `pytest`, `next build`, `playwright test`).
- `SECRET_KEY` in `app/core/security.py` is still hard-coded.
- Backend still creates schema via `Base.metadata.create_all` (no Alembic).
- Reset-password / recovery tokens are in-memory (`auth.py`), lost on restart.
