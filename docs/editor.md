# Site Builder — Inline Editor

The inline editor opens automatically when site generation completes. It appears as a 480px sidebar on the left, with a device-responsive iframe preview on the right.

## Editor Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ [Site Builder Header]              [Edit Site] [Visit] [Download]│
├─────────────────────────┬───────────────────────────────────────┤
│ Edit Site          [×]  │  [🖥 Desktop] [📱 Tablet] [📲 Mobile] │
│ ─────────────────────── │  ┌─────────────────────────────────┐  │
│ [▼] Hero                │  │                                 │  │
│ [▼] About               │  │   iframe srcdoc preview         │  │
│ [▼] Services            │  │   (inlined JS + CSS)            │  │
│ [▼] Gallery             │  │                                 │  │
│ [▼] CTA                 │  └─────────────────────────────────┘  │
│ [▼] FAQ                 │                                       │
│ [▼] Testimonials        │                                       │
│ [▼] Why Choose Us       │                                       │
│ [▼] How It Works        │                                       │
│ [▼] Contact             │                                       │
│ [▼] Design              │                                       │
│ [▼] SEO                 │                                       │
│ [▼] Visibility          │                                       │
│ ─────────────────────── │                                       │
│ [Quick Preview]         │                                       │
│ [Apply Changes]         │                                       │
│ [Re-deploy Live Site]   │                                       │
└─────────────────────────┴───────────────────────────────────────┘
```

## Editor Sections

Each section is an accordion (`EditorAccordion.vue`). Click to expand.

### Hero

Fields:
- `hero_headline` — primary headline (benefit-driven)
- `hero_subheadline` — supporting tagline
- Hero background image — `ImageField` with upload + URL entry
  - Accepts AI hero image URL, Google Maps photo URL, or user upload

### About

Fields:
- `about_title` — section heading
- `about_text` — body copy (multi-paragraph)
- About image — `ImageField`

### Services

List editor with per-item fields:
- `name` — service name
- `description` — 2-sentence description
- `icon_suggestion` — icon name from the icon set

Actions per item:
- Move up / Move down
- Delete

Add item: "Add Service" button at the bottom.

AI Generate button opens `GenerateModal` for bulk generation.

### Gallery

List of image URLs. Each entry shows a thumbnail preview.

- Add image URL manually
- Upload image via file picker (max 10 MB)
- Remove image

Source priority in the rendered site: Google Maps photos, then AI gallery images, then user-added URLs.

### CTA

Fields:
- `cta_headline` — call-to-action heading
- `cta_button_text` — button label

### FAQ

List editor with per-item fields:
- `question`
- `answer`

Actions: move up/down, delete. AI Generate available.

### Testimonials

List editor with per-item fields:
- `author` — name (AI samples are prefixed with `[Sample]`)
- `rating` — 1-5 stars
- `text` — review text

Actions: move up/down, delete. AI Generate available.

Note: Real Google reviews (scraped from Maps) are marked `verified: true` and are shown with a verification badge in the rendered site.

### Why Choose Us

List editor with per-item fields:
- `title` — differentiator headline
- `description` — 1-2 sentence explanation
- `icon_key` — icon name

Actions: move up/down, delete. AI Generate available.

### How It Works

List editor for process steps:
- `step_number` — auto-numbered
- `title` — step label
- `description` — step explanation
- `icon_key` — icon name

Rendered only when the array is non-empty. For restaurants/retail/venues, Claude returns an empty array so this section is hidden by default.

AI Generate available.

### Contact

Fields:
- `phone`
- `email`
- `address`
- `website`
- Hours (structured as day/time pairs)

### Design

#### Theme Presets

12 one-click themes that set `color_primary`, `color_secondary`, `font_heading`, `font_body` simultaneously:

| Theme | Primary | Secondary | Heading Font | Body Font |
|-------|---------|-----------|--------------|-----------|
| Ocean | `#2563EB` | `#0EA5E9` | Inter | Inter |
| Forest | `#059669` | `#10B981` | Lora | Source Sans Pro |
| Sunset | `#DC2626` | `#F59E0B` | Montserrat | Open Sans |
| Royal | `#7C3AED` | `#A855F7` | Playfair Display | Lato |
| Slate | `#334155` | `#64748B` | Space Grotesk | DM Sans |
| Coral | `#F43F5E` | `#FB923C` | Poppins | Nunito |
| Teal | `#0D9488` | `#2DD4BF` | Manrope | Inter |
| Gold | `#B45309` | `#D97706` | Merriweather | Work Sans |
| Navy | `#1E3A5F` | `#2563EB` | Raleway | Roboto |
| Rose | `#BE185D` | `#EC4899` | Outfit | Sora |
| Olive | `#4D7C0F` | `#84CC16` | Crimson Text | Rubik |
| Midnight | `#1E1B4B` | `#4338CA` | Space Grotesk | Inter |

#### Custom Colors

Color picker + hex input for `color_primary` and `color_secondary`.

#### Font Selectors

Dropdown for `font_heading` and `font_body`. Available fonts:

Inter, Montserrat, Poppins, Raleway, Playfair Display, Lato, Open Sans, Roboto, Source Sans Pro, Nunito, DM Sans, Outfit, Space Grotesk, Sora, Manrope, Merriweather, Lora, Crimson Text, Work Sans, Rubik

Note: Design changes (colors, fonts) require "Apply Changes" to take effect — they cannot be previewed with Quick Preview because they require a Vite rebuild to regenerate the Tailwind CSS output.

### SEO

Fields:
- `seo_title` — `<title>` tag content (under 60 chars recommended)
- `seo_description` — `<meta name="description">` (150-160 chars recommended)
- `og_title` — Open Graph title for social previews
- `og_description` — Open Graph description
- `og_image` — Open Graph image URL
- `canonical_url` — Canonical URL (prevents duplicate content)

### Section Visibility

Toggle switches for optional sections:

| Section | Data Key | Toggle Behavior |
|---------|----------|----------------|
| Services | `services` | Clears/restores array |
| Why Choose Us | `why_choose_us` | Clears/restores array |
| How It Works | `process_steps` | Clears/restores array |
| Testimonials | `testimonials` | Clears/restores array |
| FAQ | `faq_items` | Clears/restores array |
| Photo Gallery | `gallery` | Clears/restores array |

Visibility is determined by array length — empty array = hidden section. When toggled off, the data is backed up in memory so toggling back on restores the original content.

---

## Editor Actions

### Quick Preview

Sends a `postMessage` to the iframe with `{ type: 'QUICK_PREVIEW', payload: editableData }`. The React site's message listener applies text content changes instantly without a rebuild.

Limitations: Quick Preview works for text fields only. Color, font, and image changes require Apply Changes.

### Apply Changes

Calls `POST /api/rebuild-site` with the full `editableData`. The backend:
1. Writes updated `data.json` to the existing build directory
2. Re-substitutes placeholders in `index.html` (for SEO, colors, fonts)
3. Runs `npm run build`
4. Inlines JS + CSS into the HTML
5. Returns new `html` string

The frontend updates `resultHtml`, refreshing the iframe preview.

Apply Changes takes approximately 10-20 seconds (Vite rebuild time).

### Re-deploy Live Site

Available only when the site was previously deployed (`resultDeployUrl` is set). Calls `POST /api/redeploy-site` which uploads the current `dist/` to Cloudflare Pages or Vercel. Returns the (same) stable URL.

---

## Dirty Tracking

The store tracks whether the editor has unsaved changes by comparing the current `editableData` to a `savedDataSnapshot` (JSON string). The computed `editorDirty` is `true` when they differ.

When the user tries to close the editor with unsaved changes:
- Shows an "Unsaved Changes" modal
- Options: "Save & Close" (apply then close), "Discard" (close without saving), "Cancel"

---

## AI Section Generation

The "Generate with AI" button (available on Services, FAQ, Testimonials, Why Choose Us, How It Works) opens a modal (`GenerateModal.vue`) where the user types a prompt.

On submit, the store calls `POST /api/generate-section` with:
- `section_type` — which section to generate
- `prompt` — the user's instruction
- `context` — `{ business_name, category }` from `editableData`

The returned items are **appended** to the existing section array (not replaced). The user can then delete, reorder, or edit them before applying changes.

Supported section types and their item schemas:

| Section | Fields Generated |
|---------|----------------|
| `services` | `name`, `description`, `icon_suggestion` |
| `faq_items` | `question`, `answer` |
| `testimonials` | `author` (with `[Sample]` prefix), `rating`, `text` |
| `why_choose_us` | `title`, `description`, `icon_key` |
| `process_steps` | `step_number`, `title`, `description`, `icon_key` |

---

## Image Field (`ImageField.vue`)

Reusable component used across Hero, About, Gallery, and other image-bearing sections.

Features:
- URL text input — paste any image URL directly
- Upload button — opens file picker, POSTs to `/api/upload-image`, sets URL automatically
- Thumbnail preview of current image
- Clear button

Accepted upload types: JPEG, PNG, WebP, GIF, SVG (max 10 MB).

The upload URL is returned as a relative path (`/uploads/filename.ext`) but the frontend converts it to an absolute URL so it works inside the sandboxed iframe.

---

## Device Preview (`DevicePreview.vue`)

The iframe preview supports three device widths:

| Mode | Width | Height |
|------|-------|--------|
| Desktop | 100% | 700px |
| Tablet | 768px | 600px |
| Mobile | 375px | 667px |

The preview uses `srcdoc` (not `src`) so the site works offline without a separate server. The iframe HTML is the fully inlined build output (JS + CSS embedded directly).

A script injected into the iframe:
- Intercepts `<a href="#...">` clicks — smooth scrolls within the iframe instead of navigating away
- Intercepts external links — opens in a new tab with `window.open(..., '_blank')`
- Intercepts form submissions — prevents default (contact form won't actually submit)
- Listens for `SCROLL_TO_SECTION` postMessage — scrolls preview to a section when its editor accordion is opened
