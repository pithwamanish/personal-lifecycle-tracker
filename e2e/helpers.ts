import { Page } from '@playwright/test';

export const BACKEND_URL =
  process.env.BACKEND_URL ||
  (process.env.BASE_URL && process.env.BASE_URL.includes('frontend:3000')
    ? 'http://backend:8000'
    : 'http://localhost:8003');

/**
 * Reset the database to the default seed state via the dev endpoint.
 */
export async function resetDatabase(): Promise<void> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/dev/seed`, {
      method: 'POST',
    });
    if (!res.ok) {
      console.warn(`Seed reset returned HTTP ${res.status}`);
    }
  } catch (err) {
    console.warn('Could not contact dev seed endpoint:', err);
  }
}

/**
 * Log in via UI AuthModal.
 */
export async function loginViaUI(page: Page, email: string, password = 'password123') {
  // Check if already logged in as this user
  const accountBtn = page.getByRole('button', { name: /Account/i }).or(page.locator('button:has-text("Alex"), button:has-text("Sarah"), button:has-text("Jordan")'));
  
  // Open user menu
  const userBtn = page.locator('header').locator('button').filter({ hasText: /Alex|Sarah|Jordan|Account/i }).first();
  if (await userBtn.isVisible()) {
    await userBtn.click();
    const switchOrSignIn = page.getByRole('button', { name: /Switch or Sign In User/i });
    if (await switchOrSignIn.isVisible()) {
      await switchOrSignIn.click();
    }
  } else {
    // Look for track or sign in button
    const signInBtn = page.getByRole('button', { name: /Sign In/i });
    if (await signInBtn.isVisible()) {
      await signInBtn.click();
    }
  }

  // Auth modal should be open
  const modal = page.locator('.fixed.inset-0').filter({ hasText: /Sign In|Create New Account|Switch/i });
  await modal.waitFor({ state: 'visible' });

  // Click Sign In tab
  await modal.getByRole('button', { name: 'Sign In', exact: true }).click();
  await modal.locator('#auth-email').fill(email);
  await modal.locator('#auth-password').fill(password);
  await modal.getByRole('button', { name: /Sign In/i }).click();

  // Modal should close
  await modal.waitFor({ state: 'hidden' });
}
