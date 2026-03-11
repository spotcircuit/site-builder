# Site Builder

> Search any business on Google Maps, get a premium React website in 60 seconds.

## Overview

Site Builder scrapes a Google Maps business listing, generates AI content with Claude, builds a React + Tailwind site from templates, deploys it to Cloudflare Pages or Vercel, and provides an inline editor so you can customize the site before selling it to clients.

**Ports:** Backend `9405`, Frontend `5177`

## Quick Start

```bash
# Backend (FastAPI, port 9405)
cd apps/site_builder
./start_be.sh

# Frontend (Vue 3, port 5177)
cd apps/site_builder
./start_fe.sh
```

Open `http://localhost:5177`, paste or search for a Google Maps business, click Generate Site.

## Architecture Diagram

```
User Input (Google Maps URL or Places search)
        |
        v
[Vue 3 Frontend :5177]
  - PlacesAutocomplete
  - ProgressPanel (WebSocket)
  - DevicePreview (iframe)
  - EditorPanel (13 sections)
        |
        | REST + WebSocket
        v
[FastAPI Backend :9405]
        |
   Pipeline (async)
        |
   +-----------+
   | 1. Parse  | maps_url_parser.py
   +-----------+
        |
   +------------------+
   | 2. Scrape Maps   | maps_scraper.py (Playwright)
   +------------------+
        |
   +---------------------+
   | 3. Scrape Website   | website_scraper.py (optional)
   +---------------------+
        |
   +----------------------+
   | 4. Generate Content  | site_generator.py (Claude)
   +----------------------+
        |
   +----------------------+
   | 5. Generate Images   | image_generator.py (Gemini)
   +----------------------+
        |
   +------------------+
   | 6. Build Site    | react_builder.py (npm build)
   +------------------+
        |
   +------------------+
   | 7. Deploy        | cloudflare_deployer.py / vercel_deployer.py
   +------------------+
        |
   Live URL + Inline Editor
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, TypeScript, Pinia, Tailwind CSS |
| Backend | FastAPI, Python 3.13, asyncio |
| Scraping | Playwright (async) |
| AI Content | Claude Sonnet (`claude-sonnet-4-20250514`) |
| AI Images | Gemini 2.5 Flash Image |
| Site Template | React 18 + Tailwind CSS (Vite build) |
| Deploy: Sites | Cloudflare Pages (via wrangler CLI) |
| Deploy: Fallback | Vercel REST API |
| Real-time | WebSocket (`/ws`) |
| Backend Deploy | Railway |
| Frontend Deploy | Vercel |

## Documentation

| Document | Contents |
|----------|---------|
| [docs/architecture.md](docs/architecture.md) | Full system architecture, module breakdown, data flow, React template system |
| [docs/api.md](docs/api.md) | All REST API endpoints with request/response examples |
| [docs/editor.md](docs/editor.md) | Inline editor: sections, theme presets, AI generation, rebuild flow |
| [docs/testing.md](docs/testing.md) | pytest, vitest, Playwright E2E, test verifier agent, ACT→LEARN→REUSE |
| [docs/deployment.md](docs/deployment.md) | Cloudflare Pages, Vercel, Railway, CI/CD pipeline, standalone repo sync |

## Pipeline Steps

| Step | Status Key | Module |
|------|-----------|--------|
| Parse Google Maps URL | `parsing_url` | `maps_url_parser.py` |
| Scrape business profile | `scraping_profile` | `maps_scraper.py` |
| Scrape business website | `scraping_website` | `website_scraper.py` |
| Generate AI content | `generating_content` | `site_generator.py` |
| Generate AI images | `generating_images` | `image_generator.py` |
| Build React site | `building_site` | `react_builder.py` |
| Deploy | `deploying` | `cloudflare_deployer.py` / `vercel_deployer.py` |

## Environment Variables

### Backend

| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API for content generation | Yes |
| `GEMINI_API_KEY` | Gemini for AI image generation | No |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Pages deployment | One of these |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier | One of these |
| `VERCEL_TOKEN` | Vercel deployment | One of these |
| `VERCEL_TEAM_ID` | Vercel team identifier | No |
| `SITE_BUILDER_PORT` | Server port (default: 9405) | No |
| `SITE_BUILDER_HOST` | Server host (default: 0.0.0.0) | No |

### Frontend

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Backend URL (Railway production) |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Places Autocomplete |

## Project Structure

```
apps/site_builder/
├── README.md                          # This file
├── docs/                              # Detailed documentation
│   ├── architecture.md
│   ├── api.md
│   ├── editor.md
│   ├── testing.md
│   └── deployment.md
├── backend/
│   ├── main.py                        # FastAPI app, all endpoints, job management
│   ├── Dockerfile                     # Railway container
│   ├── pyproject.toml                 # Python dependencies (uv)
│   ├── pytest.ini                     # pytest configuration
│   ├── modules/
│   │   ├── maps_url_parser.py         # Google Maps URL parsing (293 lines)
│   │   ├── maps_scraper.py            # Playwright business scraper (1137 lines)
│   │   ├── website_scraper.py         # Business website scraper (475 lines)
│   │   ├── site_generator.py          # Claude content generation (1039 lines)
│   │   ├── image_generator.py         # Gemini image generation (302 lines)
│   │   ├── react_builder.py           # React site assembly + build (471 lines)
│   │   ├── cloudflare_deployer.py     # Cloudflare Pages deploy (258 lines)
│   │   ├── vercel_deployer.py         # Vercel deploy (157 lines)
│   │   └── websocket_manager.py       # WebSocket broadcasting (197 lines)
│   ├── templates/react/               # React + Tailwind site template
│   │   └── src/components/            # Hero, About, Services, FAQ, etc.
│   ├── tests/
│   │   ├── conftest.py                # Fixtures (client, sample jobs)
│   │   ├── test_api.py                # API endpoint tests (26 tests)
│   │   └── test_models.py             # Pydantic model tests (7 test classes)
│   └── uploads/                       # User-uploaded images (served at /uploads/)
├── frontend/
│   ├── src/
│   │   ├── App.vue                    # Main app (input/progress/result/error phases)
│   │   ├── components/
│   │   │   ├── DevicePreview.vue      # iframe preview with device switching
│   │   │   ├── PlacesAutocomplete.vue # Google Places search
│   │   │   ├── ProgressPanel.vue      # Pipeline step tracker
│   │   │   ├── SiteHistory.vue        # Previously generated sites
│   │   │   ├── SeoScorePanel.vue      # SEO metrics panel
│   │   │   └── editor/                # 17 editor components
│   │   ├── stores/
│   │   │   └── siteBuilderStore.ts    # Pinia store (all state + actions)
│   │   └── services/
│   │       ├── api.ts                 # REST API client
│   │       ├── websocket.ts           # WebSocket client
│   │       └── mapsLoader.ts          # Google Maps JS API loader
│   └── e2e/
│       ├── site-builder.spec.ts       # Fast E2E tests (21 tests)
│       └── full-generation.spec.ts    # Full generation E2E (11 tests, ~5 min)
├── start_be.sh                        # Start backend locally
└── start_fe.sh                        # Start frontend locally
```

## Deployment Overview

- **Backend**: Railway, auto-deploys from `spotcircuit/site-builder` standalone repo
- **Frontend**: Vercel, auto-deploys from the same standalone repo (`frontend/` root)
- **Sync**: GitHub Action syncs `apps/site_builder/` from this monorepo to the standalone repo on every push to `main`

See [docs/deployment.md](docs/deployment.md) for full details.

## Expert System

The site-builder expert lives in `.claude/commands/experts/site-builder/`:

| File | Purpose |
|------|---------|
| `expertise.yaml` | Accumulated knowledge base |
| `test-learn.md` | Run all tests + self-improve expertise (ACT→LEARN→REUSE) |
| `test-verify.md` | Full E2E + verifier agent workflow |
| `self-improve.md` | Standalone self-improvement command |

The test verifier agent is at `.claude/agents/site-builder-test-verifier.md`.
