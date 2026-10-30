import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Configuration for Personal Lifecycle Tracker
 * Runs against services orchestrated in docker-compose.yaml.
 */
export default defineConfig({
  testDir: './',
  testMatch: '**/*.spec.ts',
  timeout: 45 * 1000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || process.env.E2E_BASE_URL || 'http://127.0.0.1:3003',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    actionTimeout: 15000,
    navigationTimeout: 20000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },
  ],
});
