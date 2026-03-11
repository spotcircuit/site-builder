# Site Builder — Architecture

## System Overview

Site Builder is a full-stack app that converts a Google Maps business listing into a deployable React website. The frontend is Vue 3, the backend is FastAPI, and the generated sites are static React + Tailwind bundles deployed to Cloudflare Pages or Vercel.

```
[Vue 3 Frontend]  <--REST/WebSocket-->  [FastAPI Backend]
                                                |
                              +------------------------------------------+
                              | Async Pipeline (asyncio.create_task)      |
                              | 1. maps_url_parser   → ParsedMapsUrl      |
                              | 2. maps_scraper      → BusinessData        |
                              | 3. website_scraper   → WebsiteData         |
                              | 4. site_generator    → SiteContent (AI)    |
                              | 5. image_generator   → ImageGenerationResult|
                              | 6. react_builder     → ReactBuildResult    |
                              | 7. cloudflare/vercel → deploy URL          |
                              +------------------------------------------+
                                                |
                                       [In-memory jobs dict]
                                                |
                              [Generated React site → dist/ → CDN deploy]
```

## Frontend Architecture

### Application Phases

The Vue 3 app (`App.vue`) is phase-driven. The Pinia store's `phase` ref controls which section renders:

| Phase | What Renders |
|-------|-------------|
| `input` | Business URL/search input, template selector, optional context fields, site history |
| `progress` | `ProgressPanel` with step tracker + live log from WebSocket |
| `result` | `EditorPanel` (left) + `DevicePreview` (right) |
| `error` | Error message + traceback, "Try Again" button |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `App.vue` | Root — phase routing, header, WebSocket lifecycle |
| `PlacesAutocomplete.vue` | Google Places API search with Maps URL fallback |
| `ProgressPanel.vue` | Renders pipeline steps with active/completed/pending states |
| `DevicePreview.vue` | iframe with `srcdoc`, device switcher (desktop/tablet/mobile), link intercept script |
| `SiteHistory.vue` | Lists previously generated sites from localStorage |
| `SeoScorePanel.vue` | Displays SEO metrics from the `seo` field of the job result |
| `editor/EditorPanel.vue` | 480px sidebar with all 13 section editors + action buttons |

### Pinia Store (`siteBuilderStore.ts`)

Single store managing all state:

**Core State:**
- `phase` — current app phase
- `mapsUrl`, `templateName`, `businessContext`, `websiteUrl` — input fields
- `jobId` — active job ID
- `isGenerating`, `wsConnected` — UI flags

**WebSocket State:**
- `activeStep`, `completedSteps`, `stepMessages` — pipeline progress
- `logs` — full event log

**Result State:**
- `resultHtml`, `resultTitle`, `resultBusinessName`, `resultDeployUrl`, `resultDeployProvider` — generated site data
- `seoData` — SEO fields (rating, counts, flags)

**Editor State:**
- `editorOpen`, `editableData`, `savedDataSnapshot` — editor lifecycle
- `editorDirty` (computed) — JSON comparison of current vs saved snapshot
- `showUnsavedWarning`, `isRebuilding`, `isGeneratingSection`, `isRedeploying` — UI flags

**Editor Actions:**
- `updateEditableField(path, value)` — dot-notation path support (e.g. `services.0.name`)
- `addEditableArrayItem(path, item)` — append to array field
- `removeEditableArrayItem(path, index)` — splice by index
- `moveEditableArrayItem(path, from, direction)` — reorder within array
- `applyChanges()` — POST to `/api/rebuild-site`, update `resultHtml`
- `aiGenerateSection(sectionType, prompt)` — POST to `/api/generate-section`, append to array
- `redeployEditedSite()` — POST to `/api/redeploy-site`

### WebSocket Client

`services/websocket.ts` connects to `ws://localhost:9405/ws`. The store registers handlers for:
- `connection_established` — sets `wsConnected = true`
- `step` — updates `activeStep`, `completedSteps`, `stepMessages`, `logs`
- `site_ready` — triggers `fetchResult()` which polls job status until HTML is available
- `error` — transitions to error phase

---

## Backend Architecture

### FastAPI Application (`main.py`, 1055 lines)

The FastAPI app runs on port 9405. On startup it creates an asyncio background task for expired job cleanup.

**Job Storage:** An in-memory `dict[str, dict]` keyed by UUID job IDs. Jobs survive only for the process lifetime (no database). TTL cleanup runs hourly:
- Undeployed jobs: 3 days
- Deployed jobs: 6 days

**Job Record Fields:**
```python
{
    "job_id": str,
    "status": "started" | "scraping_profile" | "generating_content" | ... | "completed" | "failed",
    "step": str | None,
    "maps_url": str,
    "template_name": str,
    "created_at": ISO datetime str,
    "completed_at": ISO datetime str | None,
    "failed_at": ISO datetime str | None,
    "error": str | None,
    "result": {
        "html": str,            # Inlined JS+CSS for iframe preview
        "title": str,
        "business_name": str,
        "template_name": str,
        "generated_at": str,
        "dist_path": str,       # Path to dist/ dir for deployment
        "build_dir": str,       # Temp build dir for incremental rebuilds
        "content": dict,        # Full SiteContent model dump
        "business_data": dict,  # Full scraped business data
        "deploy_url": str | None,
        "deploy_provider": str | None,
        "seo": dict             # SEO fields extracted from content + business_data
    }
}
```

### Pipeline Modules

#### `maps_url_parser.py` (293 lines)

Parses Google Maps URLs into structured `ParsedMapsUrl`. Handles:
- Standard `/maps/place/NAME/@lat,lng` URLs
- CID URLs (`?cid=12345`)
- Short `goo.gl/maps/` redirect URLs
- Extracts: `business_name`, `place_id`, `cid`, `raw_url`

#### `maps_scraper.py` (1137 lines)

Playwright-based async scraper. Extracts from Google Maps:
- Name, address, phone, website, category
- Rating, review count
- Hours (structured as `dict[day, hours_str]`)
- Services list
- Photos (up to 6 URLs)
- Reviews (author, rating, text, time)
- GPS coordinates (latitude, longitude)
- Description, open/closed status

Returns: `BusinessData` Pydantic model.

Progress is streamed via callback to WebSocket during scraping sub-steps.

#### `website_scraper.py` (475 lines)

Optional scraper that visits the business's own website. Extracts:
- Logo URL
- Hero image URL
- Gallery images (up to 12)
- Brand colors
- Social links (Facebook, Instagram, Twitter, YouTube, TikTok, LinkedIn, Yelp)

Returns: `WebsiteData` Pydantic model. Non-fatal — failures are caught and logged.

#### `site_generator.py` (1039 lines)

Calls Claude (`claude-sonnet-4-20250514`, 4096 max tokens) with a structured prompt.

**Input:** `BusinessData` dict + optional `website_data` dict + optional `user_context` string.

**Output:** `SiteContent` Pydantic model with all text content, design tokens, and SEO fields.

The system prompt instructs Claude to:
- Write all content in English (translate foreign-language input)
- Use real customer reviews verbatim as testimonials
- Omit `process_steps` for restaurants, retail, venues
- Include location keywords for local SEO
- Generate SEO title under 60 chars, meta description 150-160 chars

**`SiteContent` fields:**
- `hero_headline`, `hero_subheadline`
- `about_title`, `about_text` (2-3 paragraphs)
- `services[]` — name, description, icon_suggestion
- `why_choose_us[]` — title, description, icon_key
- `process_steps[]` — step_number, title, description, icon_key (empty for non-service businesses)
- `testimonials[]` — author, rating, text
- `faq_items[]` — question, answer (5-6 items)
- `cta_headline`, `cta_button_text`
- `seo_title`, `seo_description`, `og_title`, `og_description`, `og_image`, `canonical_url`
- `tagline`
- `color_primary`, `color_secondary` (hex)
- `font_heading`, `font_body` (Google Font names)
- `hero_image_keyword`
- `inferred_category`

#### `image_generator.py` (302 lines)

Uses Google Gemini (`gemini-2.5-flash-image`) to generate photorealistic images. Only runs when `GEMINI_API_KEY` is set.

Images generated per site:
- **Hero background** (16:9) — only when no Google Maps photos exist
- **About section** (4:3) — only when no Google Maps photos exist
- **Services section** (4:3) — always generated
- **Why Choose Us** (4:3) — always generated
- **Contact section** (16:9) — always generated
- **Gallery images** (4:3, 3 images) — only when no Google Maps photos exist

Images saved to a temp directory, then copied to `public/images/` in the React build.

Returns: `ImageGenerationResult` Pydantic model with filenames for each section.

#### `react_builder.py` (471 lines)

Assembles and builds the React site:

1. **Copy template** — `cp -a backend/templates/react/ /tmp/site_build_JOBID_/`
2. **Generate `data.json`** — `_generate_data_json()` merges content + business data + images
3. **Substitute placeholders** — replaces `{{SEO_TITLE}}`, `{{COLOR_PRIMARY}}`, `{{FONT_HEADING}}`, etc. in `index.html` and `tailwind.config.js`
4. **Copy node_modules** — fast path using `cp -a` from template dir (avoids fresh npm install)
5. **`npm run build`** — Vite builds to `dist/`
6. **Inline assets** — `_inline_assets()` replaces `<link>` and `<script src>` tags with inline `<style>` and `<script>` blocks so the HTML works standalone in an iframe

**Rebuild (editor saves):** `rebuild_react_site()` skips template copy and npm install — only updates `data.json`, re-substitutes placeholders, re-runs build. Much faster than full build.

Returns: `ReactBuildResult` with `dist_path`, `build_dir`, `index_html`.

#### `cloudflare_deployer.py` (258 lines)

Deploys via `npx wrangler pages deploy`:
1. Checks if project exists via Cloudflare API
2. If at project limit (code 8000027), deletes oldest project to make room
3. Runs `npx wrangler pages deploy <dist_path> --project-name=<name> --branch=main`
4. Parses deployment URL from wrangler output
5. Returns stable production URL: `https://{project_name}.pages.dev`

Project names are derived from business name: `site-{slug}-{job_id[:6]}`.

Required env vars: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.

#### `vercel_deployer.py` (157 lines)

Deploys via Vercel REST API (`POST /v13/deployments`):
1. Walks `dist/` and base64-encodes all files
2. POSTs to Vercel with files + project name
3. Returns deployment URL

Required env var: `VERCEL_TOKEN`. Optional: `VERCEL_TEAM_ID`.

#### `websocket_manager.py` (197 lines)

Singleton WebSocket manager. Broadcasts messages to all connected clients. Message types:
- `step` — pipeline step updates (step name, status, message, data)
- `site_ready` — final completion event with job result summary
- `error` — pipeline failure

#### Deploy Target Resolution

```python
def _resolve_deploy_target(deploy_target):
    if deploy_target == "none": return None
    if deploy_target == "cloudflare" and is_cloudflare_configured(): return "cloudflare"
    if deploy_target == "vercel" and is_vercel_configured(): return "vercel"
    if deploy_target in (None, "auto"):
        if is_cloudflare_configured(): return "cloudflare"  # Preferred
        if is_vercel_configured(): return "vercel"
    return None
```

Both providers have automatic fallback: if Cloudflare fails, tries Vercel, and vice versa.

---

## React Template System

The template lives at `backend/templates/react/src/components/`:

| Component | Section |
|-----------|---------|
| `Navbar.tsx` | Sticky navigation with business name and CTA |
| `Hero.tsx` | Hero banner with headline, subheadline, CTA button, background image |
| `SocialProof.tsx` | Rating bar (stars, review count, tagline) |
| `About.tsx` | About section with title, text, optional image |
| `Services.tsx` | Services grid with icons |
| `WhyChooseUs.tsx` | Differentiators with icons |
| `HowItWorks.tsx` | Process steps (rendered only when `process_steps` array is non-empty) |
| `Testimonials.tsx` | Review cards with star ratings |
| `FAQ.tsx` | Accordion FAQ |
| `Gallery.tsx` | Photo grid (Google Maps photos + AI gallery images) |
| `CTA.tsx` | Call-to-action section |
| `Contact.tsx` | Phone, email, address, hours, contact form, Google Maps embed |
| `Footer.tsx` | Footer with links, social links, copyright |
| `LocalBusinessSchema.tsx` | JSON-LD structured data for SEO |

**Data flow:** `App.tsx` imports `data.json` and passes it as props to each component. All content, colors, fonts, and business info comes from `data.json` — no hardcoded values.

**`data.json` structure:** Generated by `react_builder._generate_data_json()`. Contains all `SiteContent` fields plus business data fields (name, phone, email, address, hours, photos, reviews, coordinates) plus image paths (ai_hero_image, ai_about_image, ai_gallery_images, etc.) plus website-scraped data (website_logo_url, social_links, website_images).

---

## Image Handling Priority

For each visual section, the React components use images in this priority order:

1. **Hero:** User-uploaded (`ai_hero_image` custom) > Google Maps photos[0] > AI-generated (`ai_hero_image`) > gradient fallback
2. **About:** User-uploaded > Google Maps photos[1] > AI-generated (`ai_about_image`) > none
3. **Gallery:** Google Maps photos (up to 6) + AI gallery images + website images
4. **Services/Why/Contact:** AI-generated section images

---

## SEO Implementation

SEO fields embedded at two levels:

1. **`index.html` placeholders** (substituted at build time):
   - `<title>{{SEO_TITLE}}</title>`
   - `<meta name="description" content="{{SEO_DESCRIPTION}}">`
   - `<meta property="og:title" content="{{OG_TITLE}}">`
   - `<meta property="og:description" content="{{OG_DESCRIPTION}}">`
   - `<meta property="og:image" content="{{OG_IMAGE}}">`
   - `<link rel="canonical" href="{{CANONICAL_URL}}">`

2. **JSON-LD structured data** (`LocalBusinessSchema.tsx`):
   - `LocalBusiness` schema with name, address, phone, coordinates, hours, rating

---

## Uploads

User-uploaded images are saved to `backend/uploads/`. The FastAPI app mounts this directory as static files at `/uploads/`. Allowed types: JPEG, PNG, WebP, GIF, SVG. Max size: 10 MB.

Uploaded image URLs are absolute (`http://localhost:9405/uploads/filename.ext`) so they work inside the iframe preview.
