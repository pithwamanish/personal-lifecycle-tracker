import { test, expect } from '@playwright/test';

test('benchmark page load time in browser', async ({ page }) => {
  const start = Date.now();

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const domContentLoadedTime = Date.now() - start;

  // Wait for user name in header and items table or empty state to appear
  await expect(page.locator('header').getByText('Alex Taylor')).toBeVisible();
  const fullyRenderedTime = Date.now() - start;

  console.log(`\n========================================`);
  console.log(`DOM Content Loaded Time: ${domContentLoadedTime} ms`);
  console.log(`Fully Rendered Page Time: ${fullyRenderedTime} ms (${(fullyRenderedTime / 1000).toFixed(2)}s)`);
  console.log(`========================================\n`);

  expect(fullyRenderedTime).toBeLessThan(3000);
});

test('benchmark page load time on localhost:3003 in browser', async ({ page }) => {
  const start = Date.now();

  await page.goto('http://localhost:3003/', { waitUntil: 'domcontentloaded' });
  const domContentLoadedTime = Date.now() - start;

  await expect(page.locator('header').getByText('Alex Taylor')).toBeVisible();
  const fullyRenderedTime = Date.now() - start;

  console.log(`\n========================================`);
  console.log(`[localhost:3003] DOM Content Loaded Time: ${domContentLoadedTime} ms`);
  console.log(`[localhost:3003] Fully Rendered Page Time: ${fullyRenderedTime} ms (${(fullyRenderedTime / 1000).toFixed(2)}s)`);
  console.log(`========================================\n`);

  expect(fullyRenderedTime).toBeLessThan(3000);
});

