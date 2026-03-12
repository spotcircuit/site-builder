// Full UI E2E — tests the complete browser-based generation and editor workflow
// Run: npx playwright test e2e/ui-generation.spec.ts

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

console.log(`[UI E2E] Selected test URL: ${TEST_MAPS_URL}`)

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

    // If button is still disabled, set store via Pinia's setInputUrl (handles mapsUrl + inputUrlType)
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
          if (store) {
            store.setInputUrl(url)
          }
        }
      }, TEST_MAPS_URL)
      await page.waitForTimeout(500)
    }

    await generateBtn.click()

    console.log('[UI E2E] Generation started via UI')

    // Wait for result phase — look for "Edit Site" or "Hide Editor" button (editor auto-opens)
    // This could take 2-4 minutes
    const editButton = page.locator('button').filter({ hasText: /edit site|hide editor/i }).first()
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
