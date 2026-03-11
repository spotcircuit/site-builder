import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5177',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  // Don't auto-start servers - they should already be running
  // Run: cd apps/site_builder/backend && uv run uvicorn main:app --port 9405
  // Run: cd apps/site_builder/frontend && npm run dev
  reporter: [
    ['list'],
    ['json', { outputFile: 'e2e-results.json' }],
  ],
})
