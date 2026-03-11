# Site Builder — Deployment

## Overview

Site Builder has three deployment targets:

| Target | What | Platform |
|--------|------|---------|
| Backend | FastAPI API server | Railway |
| Frontend (app UI) | Vue 3 app | Vercel |
| Generated sites | React + Tailwind sites | Cloudflare Pages or Vercel |

The monorepo auto-syncs `apps/site_builder/` to a standalone `spotcircuit/site-builder` repo via GitHub Actions. Railway and Vercel watch the standalone repo for deployments.

---

## Generated Sites (Cloudflare Pages)

### How Cloudflare Pages Deployment Works

1. `react_builder.py` builds the React site into `dist/`
2. `cloudflare_deployer.py` calls `npx wrangler pages deploy`:
   ```bash
   npx wrangler pages deploy /tmp/site_build_JOBID_/dist \
     --project-name=site-{slug}-{job_id[:6]} \
     --branch=main \
     --commit-dirty=true
   ```
3. Wrangler uploads the `dist/` files and returns a deployment URL
4. The stable production URL is `https://{project_name}.pages.dev`

### Project Naming

Project names are derived from the business name:
- Lowercased and slugified: `"Joe's Plumbing"` → `joes-plumbing`
- Truncated to 40 chars
- Appended with first 6 chars of job ID: `site-joes-plumbing-f47ac1`

### Project Limit Management

Cloudflare Pages has an account-level project limit. When the limit is hit (error code 8000027), the deployer automatically:
1. Lists all existing projects (sorted by `created_on` ascending)
2. Deletes the oldest project
3. Retries project creation

### Required Env Vars

```
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
```

### Deleting Deployed Sites

Via API:
```bash
DELETE /api/site/{project-name}
```

Via Cloudflare dashboard: Pages → select project → Settings → Delete project.

---

## Generated Sites (Vercel)

Vercel is the fallback when Cloudflare is not configured or fails.

### How Vercel Deployment Works

1. `vercel_deployer.py` walks `dist/`, base64-encodes all files
2. POSTs to `POST https://api.vercel.com/v13/deployments`:
   ```json
   {
     "name": "site-joes-plumbing-f47ac1",
     "files": [{ "file": "index.html", "data": "base64...", "encoding": "base64" }],
     "projectSettings": { "framework": null, "buildCommand": "", "outputDirectory": "." },
     "target": "production"
   }
   ```
3. Returns the deployment URL from the API response

### Required Env Vars

```
VERCEL_TOKEN=your_token
VERCEL_TEAM_ID=your_team_id  # Optional, for team deployments
```

---

## Deploy Target Selection

When `deploy_target` is not specified (or is `"auto"`):

```
Cloudflare configured? → use Cloudflare → if fails → try Vercel
Vercel configured (but not Cloudflare)? → use Vercel → if fails → try Cloudflare
Neither configured? → build without deploying
```

The frontend always passes `deploy_target: null` (auto-detect).

---

## Backend — Railway

### Architecture

The backend runs as a Docker container on Railway. The `Dockerfile` is at `backend/Dockerfile`.

### `railway.toml` (in standalone repo root)

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"
watchPatterns = ["backend/**"]

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Required Environment Variables on Railway

Set these in the Railway dashboard under Variables:

```
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
VERCEL_TOKEN=...          # optional
VERCEL_TEAM_ID=...        # optional
```

Port is auto-detected by Railway (uses `PORT` env var, falls back to 9405).

### Health Check

Railway pings `GET /health` every 30 seconds. The endpoint returns:
```json
{ "status": "healthy", "service": "site-builder", ... }
```

---

## Frontend (App UI) — Vercel

The Vue 3 frontend is deployed to Vercel from the standalone repo with root directory set to `frontend/`.

### Environment Variables on Vercel

```
VITE_API_BASE_URL=https://your-railway-backend.railway.app
VITE_GOOGLE_MAPS_API_KEY=AIza...
```

`VITE_API_BASE_URL` must point to the Railway backend. Without it, the frontend defaults to `http://localhost:9405`.

### Build Settings

- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Root directory: `frontend`

---

## CI/CD Pipeline

### GitHub Actions: `test-site-builder.yml`

Runs on every push/PR that touches `apps/site_builder/**`:
1. Backend pytest (Python 3.13, uv)
2. Frontend vitest + TypeScript check

Tests must pass before the sync job runs (enforce by having sync depend on test jobs, or run independently).

### GitHub Actions: `sync-standalone.yml`

Runs on every push to `main` that touches `apps/site_builder/**`:

```
monorepo: apps/site_builder/
    │
    │  rsync --delete (excludes: .git, node_modules, .venv, __pycache__, .env, dist, *.tsbuildinfo, .claude, logs)
    ▼
standalone: github.com/spotcircuit/site-builder
    │
    ├── Railway watches this repo → auto-deploys backend on changes to backend/**
    └── Vercel watches this repo → auto-deploys frontend on any change
```

The sync uses `STANDALONE_DEPLOY_TOKEN` (a GitHub PAT with repo write access to the standalone repo), stored as a repository secret.

**Sync behavior:**
- Only runs when `apps/site_builder/` files changed
- Uses `rsync -av --delete` to fully mirror the app directory
- Restores `railway.toml` if it doesn't exist in the standalone repo (it's not in the monorepo)
- Commits with the original monorepo commit message: `sync: {original message}`
- If no files changed (idempotent rsync), skips the commit

---

## Local Development

```bash
# Backend
cd apps/site_builder
./start_be.sh
# Starts uvicorn on port 9405

# Frontend
cd apps/site_builder
./start_fe.sh
# Starts Vite dev server on port 5177
```

Copy `.env` from project root if needed:
```bash
cp ../../.env apps/site_builder/backend/.env
```

### `start_be.sh`

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 9405 --reload
```

### `start_fe.sh`

```bash
cd frontend
npm run dev
```

---

## Standalone Repo Structure

The `spotcircuit/site-builder` standalone repo mirrors `apps/site_builder/` from the monorepo:

```
site-builder/                     ← standalone repo root
├── railway.toml                  ← Railway config (only in standalone, not in monorepo)
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── modules/
│   ├── templates/
│   └── tests/
└── frontend/
    ├── package.json
    ├── src/
    └── e2e/
```

Railway deploys from the `backend/Dockerfile` path. Vercel deploys from the `frontend/` root.

---

## Node.js Dependency Caching for Site Builds

The React template's `node_modules` should be pre-installed in the backend Docker image for fast site builds. When `backend/templates/react/node_modules/` exists, `react_builder.py` copies it instead of running `npm install` (saves ~30-60 seconds per build).

Check the `Dockerfile` to ensure the template dependencies are installed during the Docker build:
```dockerfile
RUN cd backend/templates/react && npm install
```

---

## Monitoring

- **Railway logs**: View in Railway dashboard → Deployments → Logs
- **Health check**: `GET https://your-railway-url.railway.app/health`
- **Active jobs**: The health endpoint reports `active_jobs` count
- **WebSocket connections**: Health endpoint reports `websocket_connections` count

Jobs are stored in memory only. A Railway restart clears all jobs. Job TTL cleanup runs hourly:
- Undeployed jobs expire after 3 days
- Deployed jobs expire after 6 days
