# Site Builder — API Reference

Base URL: `http://localhost:9405` (development) or Railway URL (production)

All endpoints return JSON. Errors use standard HTTP status codes with `{"detail": "message"}` bodies.

---

## WebSocket

### `WS /ws`

Connects to receive real-time pipeline progress events.

**Message types received from server:**

```json
// Step update (during pipeline execution)
{
  "type": "step",
  "step": "scraping_profile",
  "status": "started" | "progress" | "completed" | "error",
  "message": "Scraping business profile from Google Maps...",
  "data": { "job_id": "uuid" }
}

// Pipeline complete
{
  "type": "site_ready",
  "site": {
    "job_id": "uuid",
    "title": "Best Plumber Austin | Fast Reliable Service",
    "business_name": "Austin Plumbing Co",
    "template_name": "modern",
    "deploy_url": "https://site-austin-plumbing-abc123.pages.dev",
    "deploy_provider": "cloudflare",
    "seo": { "rating": 4.8, "review_count": 127, ... }
  }
}

// Error
{
  "type": "error",
  "message": "Site generation failed: ...",
  "details": { "job_id": "uuid", "traceback": "..." }
}

// Connection handshake
{
  "type": "connection_established",
  "message": "Connected to Site Builder WebSocket"
}
```

**Pipeline step keys (in order):**

| Step Key | Description |
|----------|-------------|
| `parsing_url` | Parsing the Google Maps URL |
| `scraping_profile` | Playwright scraping business from Google Maps |
| `scraping_website` | Scraping the business's own website (optional) |
| `generating_content` | Claude AI generating website copy |
| `generating_images` | Gemini AI generating images |
| `building_site` | npm build of the React site |
| `deploying` | Deploying to Cloudflare Pages or Vercel |

---

## Health

### `GET /health`

Returns service health and configuration status.

**Response 200:**
```json
{
  "status": "healthy",
  "service": "site-builder",
  "version": "1.1.0",
  "websocket_connections": 2,
  "active_jobs": 3,
  "timestamp": "2026-03-11T21:15:00.000000",
  "services": {
    "anthropic": true,
    "cloudflare": true,
    "vercel": false,
    "gemini": true
  }
}
```

---

## Site Generation

### `POST /api/generate-site`

Starts an asynchronous site generation job. Returns immediately with a `job_id`. Progress is streamed over WebSocket.

**Request body:**
```json
{
  "maps_url": "https://www.google.com/maps/place/Joe%27s+Plumbing/@30.2672,-97.7431,17z",
  "template_name": "modern",
  "deploy_target": "auto",
  "business_context": "Family-owned plumbing company since 1985, specializing in residential repairs and new construction.",
  "website_url": "https://joesplumbing.com"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `maps_url` | string | Yes | Google Maps URL or place URL |
| `template_name` | string | No | Template to use (default: `"modern"`) |
| `deploy_target` | string | No | `"auto"`, `"cloudflare"`, `"vercel"`, `"none"`, or `null` |
| `business_context` | string | No | Owner-provided description, used as primary truth for AI |
| `website_url` | string | No | Override website URL for scraping branding/images |

**Deploy target behavior:**
- `"auto"` or `null` — prefers Cloudflare if configured, falls back to Vercel
- `"cloudflare"` — uses Cloudflare, falls back to Vercel on failure
- `"vercel"` — uses Vercel, falls back to Cloudflare on failure
- `"none"` — builds without deploying

**Response 202:**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "started"
}
```

**Errors:**
- `422` — missing required `maps_url`

---

## Job Status

### `GET /api/job/{job_id}`

Polls the status of a generation job.

**Response 200:**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "step": "deploying",
  "maps_url": "https://www.google.com/maps/...",
  "template_name": "modern",
  "created_at": "2026-03-11T21:10:00.000000",
  "completed_at": "2026-03-11T21:11:02.345678",
  "error": null,
  "result": {
    "html": "<!DOCTYPE html>...",
    "title": "Joe's Plumbing Austin | Expert Plumbers",
    "business_name": "Joe's Plumbing",
    "template_name": "modern",
    "generated_at": "2026-03-11T21:11:02.000000",
    "deploy_url": "https://site-joes-plumbing-f47ac1.pages.dev",
    "deploy_provider": "cloudflare",
    "seo": {
      "seo_title": "Joe's Plumbing Austin | Expert Plumbers",
      "seo_description": "Trusted Austin plumbers since 1985. ...",
      "og_title": "Joe's Plumbing | Austin's Trusted Plumber",
      "og_description": "Family-owned plumbing service ...",
      "rating": 4.8,
      "review_count": 127,
      "has_phone": true,
      "has_address": true,
      "has_website": true,
      "has_hours": true,
      "has_photos": true,
      "has_reviews": true,
      "category": "Plumber",
      "real_review_count": 12
    }
  }
}
```

Note: `dist_path`, `build_dir`, and `content` are stripped from the polling response to reduce payload size.

**Job status values:**
- `started` — job created, pipeline about to begin
- `parsing_url` | `scraping_profile` | `scraping_website` | `generating_content` | `generating_images` | `building_site` | `deploying` — active pipeline step
- `completed` — pipeline finished successfully
- `failed` — pipeline errored (see `error` field)

**Errors:**
- `404` — job not found

---

### `GET /api/job/{job_id}/data`

Returns the editable `data.json` payload for a completed job. Used by the frontend editor to populate section fields.

**Response 200:**
```json
{
  "data": {
    "business_name": "Joe's Plumbing",
    "hero_headline": "Austin's Most Trusted Plumbers",
    "hero_subheadline": "Fast, reliable service when you need it most",
    "about_title": "About Joe's Plumbing",
    "about_text": "Family-owned since 1985...",
    "services": [
      { "name": "Emergency Repairs", "description": "...", "icon_suggestion": "wrench" }
    ],
    "why_choose_us": [
      { "title": "Licensed & Insured", "description": "...", "icon_key": "shield-check" }
    ],
    "process_steps": [
      { "step_number": 1, "title": "Call Us", "description": "...", "icon_key": "phone" }
    ],
    "testimonials": [
      { "author": "John D.", "rating": 5, "text": "Great service!", "verified": true }
    ],
    "faq_items": [
      { "question": "Do you offer emergency service?", "answer": "Yes, 24/7." }
    ],
    "cta_headline": "Ready to Fix Your Plumbing Problem?",
    "cta_button_text": "Get a Free Quote",
    "color_primary": "#1E40AF",
    "color_secondary": "#3B82F6",
    "font_heading": "Montserrat",
    "font_body": "Open Sans",
    "seo_title": "Joe's Plumbing Austin | Expert Plumbers",
    "seo_description": "...",
    "og_title": "...",
    "og_description": "...",
    "og_image": "",
    "canonical_url": "",
    "phone": "(512) 555-1234",
    "email": "joe@joesplumbing.com",
    "address": "123 Main St, Austin, TX 78701",
    "website": "https://joesplumbing.com",
    "hours": { "Monday": "8am-5pm", "Tuesday": "8am-5pm", ... },
    "photos": ["https://...", ...],
    "latitude": 30.2672,
    "longitude": -97.7431,
    "rating": 4.8,
    "review_count": 127,
    "category": "Plumber",
    "ai_hero_image": "/images/hero-bg.png",
    "ai_about_image": "/images/about.png",
    "ai_services_image": "/images/services.png",
    "ai_why_choose_us_image": "/images/why-choose-us.png",
    "ai_contact_image": "/images/contact.png",
    "social_links": { "facebook": "https://...", "instagram": "https://..." }
  }
}
```

**Errors:**
- `404` — job not found
- `400` — job has no result yet

---

### `GET /api/job/{job_id}/download`

Downloads the generated HTML as a file. Sets `Content-Disposition: attachment`.

**Response 200:** HTML file with filename `{business-name}.html`

**Response headers:**
```
Content-Type: text/html; charset=utf-8
Content-Disposition: attachment; filename="joes-plumbing.html"
```

**Errors:**
- `404` — job not found
- `400` — job not completed yet
- `500` — job completed but no HTML (internal error)

---

## Editor Endpoints

### `POST /api/rebuild-site`

Rebuilds an existing site with updated editor data. Reuses the existing `build_dir` — skips template copy and npm install. Only updates `data.json` and re-runs `npm run build`. Much faster than full generation.

**Request body:**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "data": {
    "business_name": "Joe's Plumbing",
    "hero_headline": "Updated Headline",
    "color_primary": "#DC2626",
    "services": [...],
    ...
  }
}
```

The `data` field is the full `data.json` payload (same structure as returned by `GET /api/job/{id}/data`).

**Response 200:**
```json
{
  "html": "<!DOCTYPE html>...",
  "status": "rebuilt"
}
```

**Errors:**
- `404` — job not found
- `400` — job has no build directory (cleaned up or never built)
- `500` — npm build failed

---

### `POST /api/generate-section`

Uses Claude AI to generate new content items for a specific section. Appends to the section — does not replace existing items.

**Valid section types:**

| `section_type` | Generated Item Schema |
|----------------|----------------------|
| `services` | `{ name, description, icon_suggestion }` |
| `faq_items` | `{ question, answer }` |
| `testimonials` | `{ author, rating, text }` (author prefixed with `[Sample]`) |
| `why_choose_us` | `{ title, description, icon_key }` |
| `process_steps` | `{ step_number, title, description, icon_key }` |

**Request body:**
```json
{
  "section_type": "faq_items",
  "prompt": "Add 3 FAQs about pricing and emergency service",
  "context": {
    "business_name": "Joe's Plumbing",
    "category": "Plumber"
  }
}
```

**Response 200:**
```json
{
  "items": [
    { "question": "How much does an emergency call cost?", "answer": "Emergency rates start at $150..." },
    { "question": "Do you offer same-day service?", "answer": "Yes, we offer same-day service..." }
  ],
  "section_type": "faq_items"
}
```

**Errors:**
- `422` — missing required fields
- `400` — unknown `section_type`
- `500` — Claude API call failed or response could not be parsed as JSON

---

### `POST /api/redeploy-site`

Re-deploys the edited site from the existing `dist/` directory. Uses auto-detect for provider (prefers Cloudflare).

**Request body:**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Response 200:**
```json
{
  "deploy_url": "https://site-joes-plumbing-f47ac1.pages.dev",
  "deploy_provider": "cloudflare",
  "status": "deployed"
}
```

**Errors:**
- `404` — job not found
- `400` — no `dist_path` (build was cleaned up) or dist directory no longer exists
- `500` — no deploy provider configured, or all providers failed

---

## Image Upload

### `POST /api/upload-image`

Uploads an image file and returns its URL. The URL can then be set on any `data.json` image field before calling `/api/rebuild-site`.

**Request:** `multipart/form-data` with a `file` field.

**Allowed types:** `image/jpeg`, `image/png`, `image/webp`, `image/gif`, `image/svg+xml`

**Max size:** 10 MB

**Response 200:**
```json
{
  "url": "/uploads/a3f9b2c1d4e5.png",
  "filename": "a3f9b2c1d4e5.png"
}
```

Note: The frontend converts the relative URL to an absolute URL (`http://localhost:9405/uploads/...`) so it works inside the iframe preview.

**Errors:**
- `400` — unsupported MIME type
- `400` — file exceeds 10 MB limit

Uploaded files are served from `GET /uploads/{filename}` (StaticFiles mount).

---

## Site Management

### `DELETE /api/site/{project_name}`

Deletes a deployed Cloudflare Pages project. Only works for Cloudflare; Vercel projects must be deleted via the Vercel dashboard.

**Path parameter:** `project_name` — must match `^[a-z0-9-]+$` (no spaces, no special characters)

**Response 200:**
```json
{ "status": "deleted", "project_name": "site-joes-plumbing-f47ac1" }
```

or if already deleted:
```json
{ "status": "already_deleted", "project_name": "site-joes-plumbing-f47ac1" }
```

**Errors:**
- `400` — invalid project name format
- `500` — Cloudflare not configured or API error

---

## API Docs

Interactive Swagger UI is available at `GET /docs`.
ReDoc is available at `GET /redoc`.

---

## Error Response Format

All errors return:
```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422):
```json
{
  "detail": [
    {
      "loc": ["body", "maps_url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
