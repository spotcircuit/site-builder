# Site Builder

> Search any business, get a premium website in 60 seconds.

## Overview

Site Builder takes a Google Maps business listing and generates a fully deployable React + Tailwind website with AI-generated content and images. The entire pipeline -- from scraping to deployment -- runs in under 60 seconds with real-time WebSocket progress updates.

- Paste a Google Maps URL or search by business name (Google Places Autocomplete)
- Scrapes business data (name, address, hours, reviews, photos, services) via Playwright
- AI generates website content via Claude and images via Gemini
- Builds a React + Tailwind site from templates
- Auto-deploys to Cloudflare Pages or Vercel
- Real-time step-by-step progress via WebSocket

## Architecture

| Layer | Stack | Deployment |
|-------|-------|------------|
| Backend | FastAPI + Python (port 9405) | Railway |
| Frontend | Vue 3 + TypeScript + Pinia | Vercel |
| Generated sites | React + Tailwind | Cloudflare Pages |
| AI Content | Claude (Anthropic) | -- |
| AI Images | Gemini 2.5 Flash | -- |
| Real-time | WebSocket | -- |

## Features

- **Google Places Autocomplete** -- type a business name and select from suggestions
- **Google Maps URL paste** -- drop any Maps URL directly
- **Business profile scraping** -- full Playwright scrape of name, address, hours, reviews, photos, services
- **Website scraping** -- optional scrape of the business's own website for branding colors and logo
- **AI content generation** -- category-aware prompts (restaurants vs services vs retail)
- **AI image generation** -- Gemini generates images for Services, Why Choose Us, and Contact sections
- **Google Maps photos** -- real photos used for Hero, About, and Gallery sections
- **Review filtering** -- only 4-5 star reviews are included
- **Device preview** -- desktop, tablet, and mobile preview modes
- **SEO score panel** -- on-page SEO metrics
- **Download or deploy** -- download the HTML bundle or visit the live deployed site
- **Site history** -- browse previously generated sites

## Pipeline Steps

1. **Parse** -- Extract place ID from Google Maps URL or Places selection
2. **Scrape business** -- Playwright scrapes the full business profile from Google Maps
3. **Scrape website** -- (optional) Scrape the business's own website for branding colors/logo
4. **Generate content** -- Claude AI generates all website copy, tailored to the business category
5. **Generate images** -- Gemini AI creates images for services, why-choose-us, and contact sections
6. **Build site** -- Assemble a React + Tailwind site from templates with the generated data
7. **Deploy** -- Push to Cloudflare Pages or Vercel and return the live URL

## Environment Variables

### Backend (Railway)

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API for content generation |
| `GEMINI_API_KEY` | Google Gemini for AI image generation |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Pages deployment |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier |
| `VERCEL_TOKEN` | Vercel deployment (optional) |
| `VERCEL_TEAM_ID` | Vercel team identifier (optional) |
| `SITE_BUILDER_PORT` | Server port (default: 9405) |
| `SITE_BUILDER_HOST` | Server host (default: 0.0.0.0) |

### Frontend (Vercel)

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Backend URL (Railway) |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Places Autocomplete |

## Project Structure

```
apps/site_builder/
├── backend/
│   ├── main.py                    # FastAPI server + WebSocket + pipeline
│   ├── Dockerfile                 # Railway deployment
│   ├── modules/
│   │   ├── maps_url_parser.py     # Parse Google Maps URLs
│   │   ├── maps_scraper.py        # Playwright scraper for business data
│   │   ├── website_scraper.py     # Scrape business website for branding
│   │   ├── site_generator.py     # Claude AI content generation
│   │   ├── image_generator.py    # Gemini AI image generation
│   │   ├── react_builder.py      # Build React site from templates
│   │   ├── cloudflare_deployer.py # Deploy to Cloudflare Pages
│   │   ├── vercel_deployer.py    # Deploy to Vercel
│   │   └── websocket_manager.py  # WebSocket progress broadcasting
│   └── templates/react/           # React + Tailwind site template
├── frontend/
│   └── src/
│       ├── App.vue                # Main UI (input -> progress -> result)
│       ├── components/
│       │   ├── PlacesAutocomplete.vue  # Google Places search
│       │   ├── ProgressPanel.vue       # Step-by-step progress
│       │   ├── DevicePreview.vue       # Desktop/tablet/mobile preview
│       │   ├── SiteHistory.vue         # Generated sites history
│       │   └── SeoScorePanel.vue       # SEO metrics
│       ├── stores/
│       │   └── siteBuilderStore.ts     # Pinia state management
│       └── services/
│           ├── api.ts                  # REST API client
│           ├── websocket.ts            # WebSocket client
│           └── mapsLoader.ts           # Google Maps JS API loader
├── start_be.sh                    # Start backend locally
└── start_fe.sh                    # Start frontend locally
```

## Deployment

- **Backend**: Railway (auto-deploys from `spotcircuit/site-builder` repo)
- **Frontend**: Vercel (auto-deploys from `spotcircuit/site-builder` repo, root: `frontend`)
- **Sync**: GitHub Action on the monorepo auto-syncs to the standalone deployment repo

## Local Development

```bash
# Backend
cd apps/site_builder
./start_be.sh

# Frontend
cd apps/site_builder
./start_fe.sh
```
