// Full generation E2E — runs all generation test suites
// Individual suites can be run separately:
//   npx playwright test e2e/maps-generation.spec.ts
//   npx playwright test e2e/website-generation.spec.ts
//   npx playwright test e2e/ui-generation.spec.ts

// This file is kept for backwards compatibility
// Run: npx playwright test e2e/full-generation.spec.ts (runs this file only — use individual files instead)

import { test } from '@playwright/test'
test('See individual test files: maps-generation, website-generation, ui-generation', () => {
  // This is a placeholder. Run the individual spec files directly.
  // npx playwright test e2e/maps-generation.spec.ts
  // npx playwright test e2e/website-generation.spec.ts
  // npx playwright test e2e/ui-generation.spec.ts
})
