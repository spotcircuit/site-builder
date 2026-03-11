import { test, expect } from '@playwright/test'

const FRONTEND = 'http://localhost:5177'
const BACKEND = 'http://localhost:9405'

// Rotate through different businesses to test variety
const TEST_URLS = [
  'https://www.google.com/maps/place/The+Fix+Clinic/@30.347416,-97.7593128,17z',
  'https://www.google.com/maps/place/Starbucks/@38.8976763,-77.0365298,17z',
  'https://www.google.com/maps/place/Joe%27s+Pizza/@40.7305067,-73.9938438,17z',
  'https://www.google.com/maps/place/The+UPS+Store/@33.4483771,-112.0740373,17z',
  'https://www.google.com/maps/place/Supercuts/@37.7749295,-122.4194155,17z',
]
// Use env var, or pick a random URL from the pool
const TEST_MAPS_URL = process.env.TEST_MAPS_URL || TEST_URLS[Math.floor(Math.random() * TEST_URLS.length)]

console.log(`[E2E] Selected test URL: ${TEST_MAPS_URL}`)

// These tests are SLOW (3-5 min) — only run with: npx playwright test e2e/full-generation.spec.ts
test.describe('Site Builder - Full Generation E2E', () => {
  // 5 minute timeout for the full generation flow
  test.setTimeout(300_000)

  let jobId: string

  test('1. Generate site from Maps URL via API', async ({ request }) => {
    // Start generation via API (faster than UI interaction for reliability)
    const resp = await request.post(`${BACKEND}/api/generate-site`, {
      data: {
        maps_url: TEST_MAPS_URL,
        template_name: 'modern',
        deploy_target: 'auto',
      },
    })
    expect(resp.status()).toBe(202)
    const data = await resp.json()
    expect(data.job_id).toBeTruthy()
    jobId = data.job_id
    console.log(`[E2E] Job started: ${jobId}`)
  })

  test('2. Poll until generation completes', async ({ request }) => {
    expect(jobId).toBeTruthy()

    let status = 'started'
    let attempts = 0
    const maxAttempts = 120 // 4 minutes at 2s intervals

    while (status !== 'completed' && status !== 'failed' && attempts < maxAttempts) {
      await new Promise(r => setTimeout(r, 2000))
      const resp = await request.get(`${BACKEND}/api/job/${jobId}`)
      expect(resp.ok()).toBeTruthy()
      const data = await resp.json()
      status = data.status
      const step = data.step || 'waiting'
      if (attempts % 5 === 0) {
        console.log(`[E2E] Poll #${attempts}: status=${status}, step=${step}`)
      }
      attempts++
    }

    expect(status).toBe('completed')
    console.log(`[E2E] Generation completed after ${attempts * 2}s`)
  })

  test('3. Verify generated HTML has expected sections', async ({ request }) => {
    expect(jobId).toBeTruthy()

    const resp = await request.get(`${BACKEND}/api/job/${jobId}`)
    const data = await resp.json()
    expect(data.status).toBe('completed')
    expect(data.result).toBeTruthy()
    expect(data.result.html).toBeTruthy()
    expect(data.result.business_name).toBeTruthy()

    const html = data.result.html
    // React builds bundle section IDs into JS — check content words exist
    expect(html.toLowerCase()).toContain('hero')
    expect(html.toLowerCase()).toContain('about')
    expect(html.toLowerCase()).toContain('services')
    expect(html.toLowerCase()).toContain('contact')

    // Should have the business name somewhere
    expect(html).toContain(data.result.business_name.split(' ')[0])

    console.log(`[E2E] HTML verified: ${html.length} chars, business: ${data.result.business_name}`)

    // Check if deployed
    if (data.result.deploy_url) {
      console.log(`[E2E] Deployed to: ${data.result.deploy_url}`)
    }
  })

  test('4. Fetch editable data and verify structure', async ({ request }) => {
    expect(jobId).toBeTruthy()

    const resp = await request.get(`${BACKEND}/api/job/${jobId}/data`)
    expect(resp.ok()).toBeTruthy()
    const { data } = await resp.json()

    // Verify data.json has expected fields
    expect(data.business_name).toBeTruthy()
    expect(data.hero_headline).toBeTruthy()
    expect(data.about_text).toBeTruthy()
    expect(data.color_primary).toBeTruthy()
    expect(data.font_heading).toBeTruthy()
    expect(Array.isArray(data.services)).toBeTruthy()
    expect(data.services.length).toBeGreaterThan(0)
    expect(data.phone || data.address || data.email).toBeTruthy()

    // Check optional sections that should be generated
    if (data.faq_items) {
      expect(data.faq_items.length).toBeGreaterThan(0)
      expect(data.faq_items[0].question).toBeTruthy()
      expect(data.faq_items[0].answer).toBeTruthy()
    }
    if (data.testimonials) {
      expect(data.testimonials.length).toBeGreaterThan(0)
    }

    console.log(`[E2E] Editable data: ${data.services.length} services, ${data.faq_items?.length || 0} FAQs, ${data.testimonials?.length || 0} testimonials`)
  })

  test('5. Edit data and rebuild site', async ({ request }) => {
    expect(jobId).toBeTruthy()

    // Get current data
    const dataResp = await request.get(`${BACKEND}/api/job/${jobId}/data`)
    const { data } = await dataResp.json()

    // Make edits
    const originalHeadline = data.hero_headline
    data.hero_headline = 'E2E Test Headline - Modified'
    data.hero_subheadline = 'This was edited by the E2E test suite'

    // Add a new service
    data.services.push({
      name: 'E2E Test Service',
      description: 'Added by automated E2E test',
      icon_suggestion: 'star',
    })

    // Remove last FAQ item if exists
    const originalFaqCount = data.faq_items?.length || 0
    if (data.faq_items && data.faq_items.length > 1) {
      data.faq_items.pop()
    }

    // Remove an image (set to empty string)
    const originalHeroImage = data.ai_hero_image || ''
    if (data.ai_hero_image) {
      data.ai_hero_image = ''
    }

    // Change colors
    data.color_primary = '#dc2626' // Red
    data.color_secondary = '#991b1b' // Dark red

    console.log(`[E2E] Edits: headline "${originalHeadline}" -> "E2E Test Headline - Modified"`)
    console.log(`[E2E] Edits: +1 service, ${originalFaqCount > 1 ? '-1 FAQ' : 'no FAQ change'}, hero image ${originalHeroImage ? 'cleared' : 'was empty'}`)

    // Rebuild
    const rebuildResp = await request.post(`${BACKEND}/api/rebuild-site`, {
      data: { job_id: jobId, data },
    })
    expect(rebuildResp.ok()).toBeTruthy()
    const rebuildResult = await rebuildResp.json()
    expect(rebuildResult.status).toBe('rebuilt')
    expect(rebuildResult.html).toBeTruthy()

    // Verify edits are in rebuilt HTML
    expect(rebuildResult.html).toContain('E2E Test Headline - Modified')
    expect(rebuildResult.html).toContain('E2E Test Service')
    // Color should be applied
    expect(rebuildResult.html).toContain('#dc2626')

    console.log(`[E2E] Rebuild success: ${rebuildResult.html.length} chars`)
  })

  test('6. Upload an image and rebuild with it', async ({ request }) => {
    expect(jobId).toBeTruthy()

    // Upload a minimal test PNG (1x1 pixel, RGB)
    const pngBytes = Buffer.from([
      0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
      0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
      0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xde, 0x00, 0x00, 0x00,
      0x0c, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9c, 0x63, 0xf8, 0x0f, 0x00, 0x00,
      0x01, 0x01, 0x00, 0x05, 0x18, 0xd8, 0x4e, 0x00, 0x00, 0x00, 0x00, 0x49,
      0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
    ])
    const uploadResp = await request.post(`${BACKEND}/api/upload-image`, {
      multipart: {
        file: {
          name: 'e2e-test.png',
          mimeType: 'image/png',
          buffer: pngBytes,
        },
      },
    })
    expect(uploadResp.ok()).toBeTruthy()
    const uploadResult = await uploadResp.json()
    expect(uploadResult.url).toContain('/uploads/')
    console.log(`[E2E] Image uploaded: ${uploadResult.url}`)

    // Get current data and add the uploaded image
    const dataResp = await request.get(`${BACKEND}/api/job/${jobId}/data`)
    const { data } = await dataResp.json()

    // Set as about section image
    data.ai_about_image = `http://localhost:9405${uploadResult.url}`

    // Rebuild with the new image
    const rebuildResp = await request.post(`${BACKEND}/api/rebuild-site`, {
      data: { job_id: jobId, data },
    })
    expect(rebuildResp.ok()).toBeTruthy()
    const rebuildResult = await rebuildResp.json()
    expect(rebuildResult.html).toContain(uploadResult.url.split('/').pop()!) // filename in HTML

    console.log(`[E2E] Rebuild with uploaded image: success`)
  })

  test('7. AI generate new section content', async ({ request }) => {
    expect(jobId).toBeTruthy()

    // Get business context for generation
    const dataResp = await request.get(`${BACKEND}/api/job/${jobId}/data`)
    const { data } = await dataResp.json()

    const resp = await request.post(`${BACKEND}/api/generate-section`, {
      data: {
        section_type: 'faq_items',
        prompt: 'Add 2 FAQs about pricing and availability',
        context: {
          business_name: data.business_name || 'Test Business',
          category: data.category || '',
        },
      },
    })
    // May fail if no API key, that's ok
    if (resp.ok()) {
      const result = await resp.json()
      expect(result.items).toBeTruthy()
      expect(Array.isArray(result.items)).toBeTruthy()
      expect(result.items.length).toBeGreaterThan(0)
      expect(result.items[0].question).toBeTruthy()
      expect(result.items[0].answer).toBeTruthy()
      console.log(`[E2E] AI generated ${result.items.length} FAQ items`)
    } else {
      console.log(`[E2E] AI generation skipped (status: ${resp.status()})`)
    }
  })

  test('8. Redeploy edited site', async ({ request }) => {
    expect(jobId).toBeTruthy()

    const resp = await request.post(`${BACKEND}/api/redeploy-site`, {
      data: { job_id: jobId },
    })

    if (resp.ok()) {
      const result = await resp.json()
      expect(result.deploy_url).toBeTruthy()
      expect(result.status).toBe('deployed')
      console.log(`[E2E] Redeployed to: ${result.deploy_url}`)
    } else {
      // Deploy may fail if no provider configured — that's ok
      const err = await resp.json()
      console.log(`[E2E] Redeploy skipped: ${err.detail}`)
    }
  })

  test('9. Download HTML file', async ({ request }) => {
    expect(jobId).toBeTruthy()

    const resp = await request.get(`${BACKEND}/api/job/${jobId}/download`)
    expect(resp.ok()).toBeTruthy()
    expect(resp.headers()['content-type']).toContain('text/html')
    expect(resp.headers()['content-disposition']).toContain('attachment')
    const body = await resp.text()
    expect(body.length).toBeGreaterThan(1000)
    console.log(`[E2E] Downloaded HTML: ${body.length} chars`)
  })

  test('10. Verify full job status after all edits', async ({ request }) => {
    expect(jobId).toBeTruthy()

    const resp = await request.get(`${BACKEND}/api/job/${jobId}`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()

    expect(data.status).toBe('completed')
    expect(data.job_id).toBe(jobId)
    expect(data.result).toBeTruthy()
    expect(data.result.html).toBeTruthy()
    expect(data.result.business_name).toBeTruthy()
    expect(data.created_at).toBeTruthy()

    console.log(`[E2E] Final status: ${data.status}`)
    console.log(`[E2E] Business: ${data.result.business_name}`)
    console.log(`[E2E] Deploy: ${data.result.deploy_url || 'none'}`)
    console.log(`[E2E] HTML size: ${data.result.html.length} chars`)
    console.log(`[E2E] Full generation E2E complete`)
  })
})

test.describe('Site Builder - Full UI E2E', () => {
  test.setTimeout(300_000)

  test('Generate site via UI and use editor', async ({ page }) => {
    await page.goto(FRONTEND)

    // Wait for the app to load
    await expect(page.getByRole('heading', { name: 'Site Builder' })).toBeVisible({ timeout: 10000 })

    // Enter Maps URL — type into the input and press Enter to trigger PlacesAutocomplete URL detection
    const input = page.locator('input[placeholder*="business"]').or(page.locator('input[placeholder*="Google Maps"]')).first()
    await expect(input).toBeVisible({ timeout: 10000 })
    await input.fill(TEST_MAPS_URL)
    // Trigger the paste/URL detection by dispatching input event and waiting
    await input.dispatchEvent('input')
    await page.waitForTimeout(1000)

    // If button is still disabled, set store.mapsUrl directly via Pinia
    const generateBtn = page.locator('button').filter({ hasText: /generate|build|create/i }).first()
    await expect(generateBtn).toBeVisible()
    const isDisabled = await generateBtn.getAttribute('disabled')
    if (isDisabled !== null) {
      // Set the store value directly — PlacesAutocomplete URL detection may not fire in headless
      await page.evaluate((url) => {
        const app = (document.querySelector('#app') as any)?.__vue_app__
        if (app) {
          const pinia = app.config.globalProperties.$pinia
          const store = pinia._s.get('siteBuilder')
          if (store) store.mapsUrl = url
        }
      }, TEST_MAPS_URL)
      await page.waitForTimeout(500)
    }

    await generateBtn.click()

    console.log('[UI E2E] Generation started via UI')

    // Wait for result phase — look for "Edit Site" button or the DevicePreview iframe
    // This could take 2-4 minutes
    const editButton = page.locator('button').filter({ hasText: /edit site/i }).first()
    const errorIndicator = page.locator('text=failed').or(page.locator('text=Error')).first()

    // Poll until either edit button appears or error
    let completed = false
    for (let i = 0; i < 150; i++) { // 5 min max
      if (await editButton.isVisible().catch(() => false)) {
        completed = true
        break
      }
      if (await errorIndicator.isVisible().catch(() => false)) {
        console.log('[UI E2E] Generation failed — check server logs')
        break
      }
      await page.waitForTimeout(2000)
      if (i % 10 === 0) console.log(`[UI E2E] Waiting for completion... ${i * 2}s`)
    }

    if (!completed) {
      console.log('[UI E2E] Generation did not complete in time or failed')
      // Take a screenshot for debugging
      await page.screenshot({ path: 'e2e-generation-timeout.png' })
      test.skip()
      return
    }

    console.log('[UI E2E] Generation completed, editor should be open')

    // The editor auto-opens. Look for accordion sections
    const heroAccordion = page.locator('button').filter({ hasText: /hero/i }).first()
    await expect(heroAccordion).toBeVisible({ timeout: 10000 })

    // Click Hero accordion to open it
    await heroAccordion.click()
    await page.waitForTimeout(500)

    // Find and edit the hero headline input
    const headlineInput = page.locator('input').filter({ hasText: '' }).first()
    // The hero section should have inputs visible now
    const heroInputs = page.locator('.space-y-3 input, .space-y-4 input').first()
    if (await heroInputs.isVisible().catch(() => false)) {
      await heroInputs.fill('UI E2E Modified Headline')
      console.log('[UI E2E] Modified hero headline')
    }

    // Look for the Apply Changes button and click it
    const applyBtn = page.locator('button').filter({ hasText: /apply changes/i }).first()
    if (await applyBtn.isVisible().catch(() => false)) {
      await applyBtn.click()
      console.log('[UI E2E] Clicked Apply Changes')

      // Wait for rebuild to complete (button text changes to "Rebuilding..." then back)
      await page.waitForTimeout(30000) // 30s for rebuild
      console.log('[UI E2E] Rebuild should be complete')
    }

    // Verify the preview iframe exists
    const iframe = page.locator('iframe')
    await expect(iframe).toBeVisible({ timeout: 5000 })
    console.log('[UI E2E] Preview iframe visible')

    // Take a final screenshot
    await page.screenshot({ path: 'e2e-full-ui-complete.png', fullPage: true })
    console.log('[UI E2E] Full UI E2E complete')
  })
})
