# Site Builder — Testing

## Overview

The site builder has three test suites:

| Suite | Framework | Tests | Location |
|-------|-----------|-------|----------|
| Backend unit tests | pytest + httpx | 33 tests | `backend/tests/` |
| Frontend store tests | vitest | 33 tests | `frontend/src/stores/__tests__/` |
| E2E smoke tests | Playwright | 21 tests | `frontend/e2e/site-builder.spec.ts` |
| E2E full generation | Playwright | 11 tests | `frontend/e2e/full-generation.spec.ts` |

---

## Backend Tests (pytest)

Located in `backend/tests/`. Run with:

```bash
cd apps/site_builder/backend
uv run pytest tests/ -v --tb=short
```

### Configuration (`pytest.ini`)

```ini
asyncio_mode = auto
```

All async tests use `@pytest.mark.asyncio`.

### Fixtures (`conftest.py`)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `client` | function | `httpx.AsyncClient` wired to the FastAPI app via `ASGITransport` |
| `clean_jobs` | function (autouse) | Clears the `jobs` dict before and after each test — ensures isolation |
| `sample_job_id` | function | Creates a completed job in memory, returns its UUID |
| `sample_editable_data` | function | Returns a full `data.json` payload for editor endpoint tests |

The `clean_jobs` autouse fixture is the key to test isolation. Since jobs are stored in an in-memory dict, clearing it before and after each test prevents state leakage between tests.

### `test_api.py` (26 tests)

Tests all REST endpoints:

**Health:**
- `test_health` — verifies status, service name, active_jobs, services config

**Generate Site:**
- `test_generate_site_creates_job` — POST returns 202 with job_id, job appears in dict
- `test_generate_site_missing_url` — missing `maps_url` returns 422

**Job Status:**
- `test_get_job_status` — returns job data, strips dist_path/build_dir/content
- `test_get_job_not_found` — 404 for unknown job_id

**Download:**
- `test_download_completed` — returns text/html with Content-Disposition
- `test_download_not_completed` — 400 when job is not complete
- `test_download_not_found` — 404 for unknown job_id

**Editable Data:**
- `test_get_editable_data` — returns `{data: dict}` for completed job
- `test_get_editable_data_not_found` — 404
- `test_get_editable_data_no_result` — 400 for in-progress job

**Rebuild Site:**
- `test_rebuild_no_job` — 404
- `test_rebuild_no_build_dir` — 400 when job has no build_dir

**Generate Section:**
- `test_generate_section_invalid_type` — 400 with "Unknown section type" message
- `test_generate_section_validation` — 422 for empty body

**Redeploy:**
- `test_redeploy_no_job` — 404
- `test_redeploy_no_dist` — 400

**Image Upload:**
- `test_upload_image_success` — uploads 1x1 PNG, returns `/uploads/` URL
- `test_upload_image_wrong_type` — 400 for `text/plain`
- `test_upload_image_too_large` — 400 (skipped in CI — allocating 10MB+ is slow)
- `test_max_image_size_constant` — verifies `MAX_IMAGE_SIZE == 10 * 1024 * 1024`

**Delete Site:**
- `test_delete_site_invalid_name` — 400 for names with spaces/special chars

**Job TTL:**
- `test_job_created_at_stored` — verifies `created_at` field is present and ISO-parseable

### `test_models.py` (7 test classes)

Tests Pydantic models and the deploy target resolver:

**`TestGenerateSiteRequest`:**
- Minimal construction (only `maps_url`)
- Full construction with all optional fields
- Missing `maps_url` raises ValidationError

**`TestGenerateSiteResponse`:**
- Basic construction and field access

**`TestRebuildSiteRequest`:**
- Construction with `job_id` + `data`
- Missing `data` raises ValidationError

**`TestGenerateSectionRequest`:**
- Construction and field access
- All 5 valid section types are accepted by the model

**`TestRedeploySiteRequest`:**
- Basic construction

**`TestResolveDeployTarget`:**
- `"none"` returns `None`
- `"auto"` with no env vars returns `None` (temporarily clears env vars, restores after)

---

## Frontend Store Tests (vitest)

Located in `frontend/src/stores/__tests__/siteBuilderStore.test.ts`. Run with:

```bash
cd apps/site_builder/frontend
npx vitest run
```

### Test Structure

All 33 tests are in a single `describe('siteBuilderStore - Editor', ...)` block. Each test uses a fresh Pinia instance via `setActivePinia(createPinia())`.

The `beforeEach` sets up `editableData` with a realistic structure:
- 3 services, 2 FAQ items, 1 testimonial, 1 why_choose_us item, 2 process steps

### Test Coverage

**`updateEditableField` (4 tests):**
- Updates a top-level string field
- Updates a nested array item field via dot notation (`services.0.name`)
- Updates the last item in an array
- No-ops when `editableData` is null

**`addEditableArrayItem` (4 tests):**
- Appends item to `services` array
- Appends item to `faq_items` array
- No-ops when path is not an array (e.g. `hero_headline`)
- No-ops when `editableData` is null

**`removeEditableArrayItem` (4 tests):**
- Removes middle item (index 1 of 3)
- Removes first item
- Removes last item
- No-ops when `editableData` is null

**`moveEditableArrayItem` (6 tests):**
- Moves item up (index 1 → 0)
- Moves item down (index 0 → 1)
- Does not move first item further up (boundary)
- Does not move last item further down (boundary)
- No-ops on non-array path
- No-ops when `editableData` is null

**`editorDirty` (3 tests):**
- `false` when no `savedDataSnapshot` exists
- `false` when data matches snapshot (JSON equality)
- `true` after a field is changed from the snapshot state

**`closeEditor` (2 tests):**
- Closes when `editorDirty` is `false`
- Shows unsaved warning and keeps editor open when dirty

**`forceCloseEditor` (1 test):**
- Closes editor and clears `showUnsavedWarning` regardless of dirty state

---

## E2E Tests (Playwright)

Playwright tests require both servers running:
- Backend at `http://localhost:9405`
- Frontend at `http://localhost:5177`

### Fast Smoke Tests (`site-builder.spec.ts`, 21 tests)

Run in ~30 seconds. Do not require real business scraping.

```bash
cd apps/site_builder/frontend
npx playwright test e2e/site-builder.spec.ts
```

**Test groups:**

**Smoke Tests (3):**
- Frontend loads and shows "Site Builder" heading
- Backend `/health` returns `{"status": "healthy"}`
- Backend `/docs` (Swagger) is accessible

**Input Phase (4):**
- Google Maps URL input is visible
- Template selection is present
- Deploy target options visible
- Generate button exists (requires URL to enable)

**API Endpoints (11):**
- `POST /api/generate-site` with empty body → 422
- `GET /api/job/{id}` with unknown id → 404
- `GET /api/job/{id}/data` with unknown id → 404
- `GET /api/job/{id}/download` with unknown id → 404
- `POST /api/rebuild-site` with missing job → 404
- `POST /api/generate-section` with invalid type → 400
- `POST /api/generate-section` with valid type → not 400 (may 200 or 500 based on API key)
- `POST /api/redeploy-site` with missing job → 404
- `POST /api/upload-image` with non-image file → 400
- `POST /api/upload-image` with valid PNG → 200, returns `/uploads/` URL
- `DELETE /api/site/invalid name!!` → 400

**WebSocket (1):**
- Connects and receives `connection_established` event with correct `type` field

**Editor UI (1):**
- App mounts with `#app` element

**Site Generation Flow (1):**
- `POST /api/generate-site` with a valid Maps URL → 202, returns `job_id`
- `GET /api/job/{id}` → job exists with valid status

### Full Generation E2E (`full-generation.spec.ts`, 11 tests)

These tests take 3-5 minutes each. Run selectively:

```bash
cd apps/site_builder/frontend
npx playwright test e2e/full-generation.spec.ts
```

**Timeout:** 5 minutes per test (`test.setTimeout(300_000)`)

#### URL Rotation

The tests randomly select from 5 real businesses to ensure variety:

```typescript
const TEST_URLS = [
  'https://www.google.com/maps/place/The+Fix+Clinic/@30.347416,...',   // Austin wellness clinic
  'https://www.google.com/maps/place/Starbucks/@38.8976763,...',        // Washington DC Starbucks
  'https://www.google.com/maps/place/Joe%27s+Pizza/@40.7305067,...',    // NYC pizza
  'https://www.google.com/maps/place/The+UPS+Store/@33.4483771,...',    // Phoenix UPS Store
  'https://www.google.com/maps/place/Supercuts/@37.7749295,...',        // San Francisco Supercuts
]
```

Override with env var: `TEST_MAPS_URL=https://... npx playwright test ...`

#### Test Sequence (11 tests)

Tests share `jobId` across the suite via a module-level variable:

1. **Generate site from Maps URL** — POST to `/api/generate-site`, verify 202 + job_id
2. **Poll until completion** — polls every 2 seconds, up to 4 minutes (120 attempts), expects `status === "completed"`
3. **Verify generated HTML** — checks HTML contains hero, about, services, contact sections + business name
4. **Fetch editable data** — verifies `data.json` has all required fields (headline, services, colors, fonts, contact)
5. **Edit data and rebuild** — modifies headline, adds a service, changes colors to red, calls rebuild, verifies edits appear in rebuilt HTML
6. **Upload image and rebuild** — uploads a 1x1 test PNG, sets as `ai_about_image`, rebuilds, verifies filename appears in HTML
7. **AI generate section** — generates 2 FAQ items about pricing; validates structure (question + answer fields)
8. **Redeploy edited site** — calls redeploy; verifies either deploy URL returned or skips gracefully if no provider
9. **Download HTML** — verifies `Content-Type: text/html`, `Content-Disposition: attachment`, body length > 1000 chars
10. **Verify final job status** — confirms job remains `completed`, business name and HTML are present
11. **Full UI E2E** — drives the complete flow through the Vue UI (search → generate → wait → open editor → edit headline → apply changes → verify iframe)

---

## GitHub Actions CI

### `test-site-builder.yml`

Triggers on push/PR when any file under `apps/site_builder/` changes.

**`backend-tests` job:**
1. Checkout
2. Install Astral UV
3. `uv python install 3.13`
4. `uv sync` (installs from `pyproject.toml`)
5. `uv run pytest tests/ -v --tb=short`

**`frontend-tests` job:**
1. Checkout
2. Setup Node.js 20 with npm cache
3. `npm ci`
4. `npx vitest run`
5. `npx tsc --noEmit --skipLibCheck` (type check)

Note: E2E tests are not run in CI (they require live servers and take 3-5 minutes each).

---

## ACT → LEARN → REUSE Workflow

The expert system implements a self-improving test cycle:

### `/experts/site-builder/test-learn`

Runs all three test suites, analyzes results, and updates the expertise file:

1. Run backend pytest
2. Run frontend vitest
3. Check if servers are up, run E2E if available
4. Analyze failures and coverage gaps
5. Update `.claude/commands/experts/site-builder/expertise.yaml` with new insights
6. Validate YAML syntax
7. Suggest 3-5 new tests for coverage gaps

### `/experts/site-builder/test-verify`

Full E2E test with the test verifier agent:

1. Runs full-generation E2E tests
2. Captures all console output (timings, business name, section counts)
3. Invokes `site-builder-test-verifier` agent to analyze results
4. Agent extracts performance benchmarks, data quality metrics, failure root causes
5. Agent updates expertise file with learnings

### Test Verifier Agent (`.claude/agents/site-builder-test-verifier.md`)

A specialized Claude agent that:
1. Reads E2E test output logs
2. Builds a generation timeline from `[E2E]` console.log markers
3. Extracts data quality (services count, FAQs, images, deploy URL)
4. Identifies failure root causes (test bug vs app bug vs environment)
5. Updates expertise YAML with performance benchmarks and insights
6. Generates a structured verification report

---

## Testing Tips

### Running a Single Playwright Test

```bash
npx playwright test e2e/site-builder.spec.ts --grep "WebSocket"
```

### Debugging Failures

```bash
# Run with headed browser (see what's happening)
npx playwright test --headed

# Generate trace for analysis
npx playwright test --trace on
npx playwright show-trace trace.zip
```

### Specific Business URL for E2E

```bash
TEST_MAPS_URL="https://www.google.com/maps/place/..." npx playwright test e2e/full-generation.spec.ts
```

### Running Backend Tests with Verbose Output

```bash
cd apps/site_builder/backend
uv run pytest tests/test_api.py -v -s  # -s shows print() output
```

### Type Checking

```bash
cd apps/site_builder/frontend
npx tsc --noEmit --skipLibCheck
```
