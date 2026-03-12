// Website-Only Generation E2E — tests generation from a website URL (no Maps URL)
// Run: npx playwright test e2e/website-generation.spec.ts

import { test, expect } from '@playwright/test'

const FRONTEND = 'http://localhost:5177'
const BACKEND = 'http://localhost:9405'

// ─── Website-Only Generation (no Maps URL) ──────────────────────
test.describe('Site Builder - Website-Only Generation', () => {
  test.setTimeout(300_000)

  let jobId: string

  test('1. Generate site from website URL via API', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {
        website_url: 'https://thefixclinic.com',
        business_name: 'The Fix Clinic',
        business_category: 'Medical Spa',
      },
    })
    expect(resp.status()).toBe(202)
    const data = await resp.json()
    expect(data.job_id).toBeTruthy()
    jobId = data.job_id
    console.log(`[Website E2E] Job started: ${jobId}`)
  })

  test('2. Poll until website-only generation completes', async ({ request }) => {
    expect(jobId).toBeTruthy()

    let status = 'started'
    let pollCount = 0
    const maxPolls = 120 // 4 min max

    while (status !== 'completed' && status !== 'failed' && pollCount < maxPolls) {
      await new Promise(r => setTimeout(r, 2000))
      const resp = await request.get(`${BACKEND}/api/job/${jobId}`)
      const data = await resp.json()
      status = data.status
      if (pollCount % 5 === 0) {
        console.log(`[Website E2E] Poll #${pollCount}: status=${status}, step=${data.step}`)
      }
      pollCount++
    }

    expect(status).toBe('completed')
    console.log(`[Website E2E] Generation completed after ${pollCount * 2}s`)
  })

  test('3. Verify website-only generated HTML', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/job/${jobId}`)
    const data = await resp.json()

    expect(data.status).toBe('completed')
    expect(data.result).toBeTruthy()
    expect(data.result.html).toBeTruthy()
    expect(data.result.html.length).toBeGreaterThan(10000)
    expect(data.result.business_name).toBeTruthy()

    // Verify HTML contains key sections
    const html = data.result.html.toLowerCase()
    expect(html).toContain('hero')
    expect(html).toContain('services')
    expect(html).toContain('contact')

    console.log(`[Website E2E] HTML verified: ${data.result.html.length} chars, business: ${data.result.business_name}`)
  })

  test('4. Fetch editable data from website-only job', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/job/${jobId}/data`)
    expect(resp.status()).toBe(200)
    const data = await resp.json()

    expect(data.data).toBeTruthy()
    expect(data.data.business_name).toBeTruthy()
    expect(data.data.hero_headline).toBeTruthy()

    console.log(`[Website E2E] Editable data verified: ${Object.keys(data.data).length} fields`)
  })

  test('5. Validate API rejects website-only without business name', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {
        website_url: 'https://example.com',
        // No business_name — should fail
      },
    })
    expect(resp.status()).toBe(400)
    const data = await resp.json()
    expect(data.detail).toContain('business_name')
  })

  test('6. Validate API rejects empty request', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {},
    })
    expect(resp.status()).toBe(400)
    const data = await resp.json()
    expect(data.detail).toContain('maps_url or website_url')
  })
})
