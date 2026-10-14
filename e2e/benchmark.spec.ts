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

test('benchmark page load time in browser with live AWS Lambda backend', async ({ page }) => {
  const awsUrl = 'https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws';

  await page.route('**/api/v1/**', async (route) => {
    try {
      const reqStart = Date.now();
      const url = new URL(route.request().url());
      const targetUrl = `${awsUrl}${url.pathname}${url.search}`;
      const response = await page.request.fetch(targetUrl, {
        method: route.request().method(),
        headers: route.request().headers(),
        data: route.request().postDataBuffer(),
      });
      const duration = Date.now() - reqStart;
      console.log(`[AWS API] ${route.request().method()} ${url.pathname} -> ${response.status()} in ${duration}ms`);
      await route.fulfill({
        response,
      });
    } catch {
      // Ignore errors if context/page closed after assertion completed
    }
  });

  const start = Date.now();
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  const domContentLoadedTime = Date.now() - start;

  await expect(page.locator('header').getByText('Alex Taylor')).toBeVisible();
  const fullyRenderedTime = Date.now() - start;

  console.log(`\n========================================`);
  console.log(`[AWS Lambda Hosting] DOM Content Loaded Time: ${domContentLoadedTime} ms`);
  console.log(`[AWS Lambda Hosting] Fully Rendered Page Time: ${fullyRenderedTime} ms (${(fullyRenderedTime / 1000).toFixed(2)}s)`);
  console.log(`========================================\n`);

  expect(fullyRenderedTime).toBeLessThan(3000);
  await page.unrouteAll({ behavior: 'ignoreErrors' });
});

