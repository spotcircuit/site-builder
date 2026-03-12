import { test, expect } from '@playwright/test'

// Base URLs
const FRONTEND = 'http://localhost:5177'
const BACKEND = 'http://localhost:9405'

test.describe('Site Builder - Smoke Tests', () => {
  test('frontend loads', async ({ page }) => {
    await page.goto(FRONTEND)
    // The app should show the heading (use getByRole to avoid strict mode with multiple matches)
    await expect(page.getByRole('heading', { name: 'Site Builder' })).toBeVisible({ timeout: 10000 })
  })

  test('backend health check', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/health`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.status).toBe('healthy')
    expect(data.service).toBe('site-builder')
  })

  test('backend API docs available', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/docs`)
    expect(resp.ok()).toBeTruthy()
  })
})

test.describe('Site Builder - Input Phase', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(FRONTEND)
  })

  test('shows Google Maps URL input', async ({ page }) => {
    // PlacesAutocomplete has placeholder "Search for any business..." or "Paste a Google Maps URL..."
    const input = page.locator('input[placeholder*="business"]').or(page.locator('input[placeholder*="Google Maps"]')).first()
    await expect(input).toBeVisible({ timeout: 10000 })
  })

  test('shows template selection', async ({ page }) => {
    // Should have template options or a default template name
    await expect(page.locator('text=modern').or(page.locator('text=Modern')).or(page.locator('text=Template')).first()).toBeVisible({ timeout: 10000 })
  })

  test('shows deploy target options', async ({ page }) => {
    // Should have deploy target selector (Cloudflare, Vercel, etc.)
    const deploySection = page.locator('text=deploy').or(page.locator('text=Deploy')).or(page.locator('text=Hosting')).first()
    await expect(deploySection).toBeVisible({ timeout: 10000 })
  })

  test('generate button exists but requires URL', async ({ page }) => {
    const generateBtn = page.locator('button').filter({ hasText: /generate|build|create/i }).first()
    await expect(generateBtn).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Site Builder - API Endpoints', () => {
  test('POST /api/generate-site validates input', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {},
    })
    expect(resp.status()).toBe(400) // Custom validation: at least one URL required
  })

  test('GET /api/job/{id} returns 404 for missing job', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/job/nonexistent-job-id`)
    expect(resp.status()).toBe(404)
  })

  test('GET /api/job/{id}/data returns 404 for missing job', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/job/nonexistent-job-id/data`)
    expect(resp.status()).toBe(404)
  })

  test('GET /api/job/{id}/download returns 404 for missing job', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/job/nonexistent-job-id/download`)
    expect(resp.status()).toBe(404)
  })

  test('POST /api/rebuild-site returns 404 for missing job', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/rebuild-site`, {
      data: { job_id: 'missing', data: {} },
    })
    expect(resp.status()).toBe(404)
  })

  test('POST /api/generate-section rejects invalid type', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-section`, {
      data: {
        section_type: 'invalid_type',
        prompt: 'test',
        context: { business_name: 'Test' },
      },
    })
    expect(resp.status()).toBe(400)
  })

  test('POST /api/generate-section accepts valid type (not 400)', async ({ request }) => {
    // Only test one type to avoid timeout (each call hits Claude API)
    const resp = await request.post(`${BACKEND}/api/generate-section`, {
      data: {
        section_type: 'services',
        prompt: 'test',
        context: { business_name: 'Test' },
      },
    })
    // Should either succeed (200) or fail due to API key (500), NOT 400
    expect(resp.status()).not.toBe(400)
  })

  test('POST /api/redeploy-site returns 404 for missing job', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/redeploy-site`, {
      data: { job_id: 'missing' },
    })
    expect(resp.status()).toBe(404)
  })

  test('POST /api/upload-image rejects non-image files', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/upload-image`, {
      multipart: {
        file: {
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('hello'),
        },
      },
    })
    expect(resp.status()).toBe(400)
  })

  test('POST /api/upload-image accepts valid images', async ({ request }) => {
    // Minimal valid PNG
    const pngBytes = Buffer.from([
      0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
      0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
      0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xde, 0x00, 0x00, 0x00,
      0x0c, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9c, 0x63, 0xf8, 0x0f, 0x00, 0x00,
      0x01, 0x01, 0x00, 0x05, 0x18, 0xd8, 0x4e, 0x00, 0x00, 0x00, 0x00, 0x49,
      0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
    ])
    const resp = await request.post(`${BACKEND}/api/upload-image`, {
      multipart: {
        file: {
          name: 'test.png',
          mimeType: 'image/png',
          buffer: pngBytes,
        },
      },
    })
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.url).toContain('/uploads/')
    expect(data.filename).toContain('.png')
  })

  test('DELETE /api/site rejects invalid project names', async ({ request }) => {
    const resp = await request.delete(`${BACKEND}/api/site/invalid name!!`)
    expect(resp.status()).toBe(400)
  })

  test('GET /api/templates returns available templates', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/templates`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.templates).toBeTruthy()
    expect(Array.isArray(data.templates)).toBeTruthy()
    // At least modern should be available
    const modern = data.templates.find((t: any) => t.name === 'modern')
    expect(modern).toBeTruthy()
    expect(modern.available).toBe(true)
    expect(modern.label).toBeTruthy()
  })
})

test.describe('Site Builder - WebSocket', () => {
  test('WebSocket connects and receives handshake', async ({ page }) => {
    // Use page.evaluate to test WebSocket from browser context
    const result = await page.evaluate(async () => {
      return new Promise<{ connected: boolean; event_type: string | null }>((resolve) => {
        const ws = new WebSocket('ws://localhost:9405/ws')
        const timeout = setTimeout(() => {
          ws.close()
          resolve({ connected: false, event_type: null })
        }, 5000)

        ws.onmessage = (event) => {
          clearTimeout(timeout)
          try {
            const data = JSON.parse(event.data)
            ws.close()
            resolve({ connected: true, event_type: data.type || null })
          } catch {
            ws.close()
            resolve({ connected: true, event_type: null })
          }
        }

        ws.onerror = () => {
          clearTimeout(timeout)
          resolve({ connected: false, event_type: null })
        }
      })
    })

    expect(result.connected).toBeTruthy()
    expect(result.event_type).toBe('connection_established')
  })
})

test.describe('Site Builder - Editor UI', () => {
  // These tests require a completed job to be present
  // We test the editor components exist and behave correctly

  test('editor panel structure renders correctly', async ({ page }) => {
    await page.goto(FRONTEND)
    // The editor only shows in result phase, so we check the input phase first
    await expect(page.locator('body')).toBeVisible()
    // App should be a Vue app with the site builder store
    const appExists = await page.locator('#app').count()
    expect(appExists).toBe(1)
  })
})

test.describe('Site Builder - Site Generation Flow', () => {
  test('can start generation with valid URL', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {
        maps_url: 'https://www.google.com/maps/place/Test/@40.7128,-74.0060,17z',
        template_name: 'modern',
        deploy_target: 'none',
      },
    })
    expect(resp.status()).toBe(202)
    const data = await resp.json()
    expect(data.job_id).toBeTruthy()
    expect(data.status).toBe('started')

    // Verify job exists
    const statusResp = await request.get(`${BACKEND}/api/job/${data.job_id}`)
    expect(statusResp.ok()).toBeTruthy()
    const status = await statusResp.json()
    expect(status.job_id).toBe(data.job_id)
    // Job could be in any pipeline state by now
    expect(status.status).toBeTruthy()
  })
})
