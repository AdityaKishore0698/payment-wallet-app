# Digital Wallet — Frontend

Next.js 14 (App Router) + TypeScript + Tailwind CSS. Replaces the previous
Streamlit UI.

## Scripts

| Command         | Description                                  |
| --------------- | -------------------------------------------- |
| `npm run dev`       | Dev server on http://localhost:3000      |
| `npm run build`     | Production build (`output: standalone`)  |
| `npm run lint`      | ESLint (`next/core-web-vitals`)          |
| `npm run typecheck` | `tsc --noEmit`                           |
| `npm run test:e2e`  | Playwright E2E (needs the stack running) |

## End-to-end tests

Playwright specs live in `e2e/`. They exercise the full stack, so bring it up
first:

```bash
docker compose up -d --build   # from the repo root
cd frontend && npm run test:e2e
```

Target something other than Nginx with `E2E_BASE_URL` (e.g.
`E2E_BASE_URL=http://localhost:3000` against `npm run dev`).

## Environment

| Variable               | Default                 | Purpose                                                        |
| ---------------------- | ----------------------- | ------------------------------------------------------------- |
| `NEXT_PUBLIC_API_BASE` | `/api`                  | Base path the browser uses for API calls (baked at build).   |
| `API_PROXY_TARGET`     | `http://localhost:8000` | Where the Next server rewrites `/api/*` (dev / non-Nginx).   |

In production, Nginx serves this app on `/` and routes `/api/` to FastAPI, so
the defaults require no changes.

## Structure

```
src/
  app/
    (auth)/        login, register, forgot-password  — redirects to /dashboard when signed in
    (app)/         dashboard, add-funds, transfer, history, settings — guarded, wrapped in AppShell
  components/      UI primitives, AppShell, Logo
  lib/
    api.ts         typed FastAPI client
    auth.tsx       AuthProvider (JWT in localStorage) + useAuth()
    format.ts      currency / date helpers
```
