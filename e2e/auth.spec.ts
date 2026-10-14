import { test, expect } from '@playwright/test';
import { resetDatabase } from './helpers';

test.describe('Accounts & Authentication Flow (@spec.md Decision 3, 23)', () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test('should load application and display default authenticated user', async ({ page }) => {
    await page.goto('/');

    // Verify wordmark
    await expect(page.locator('text=Lifecycle Tracker').first()).toBeVisible();

    // Verify default user Alex Taylor is loaded
    await expect(page.locator('header').getByText('Alex Taylor')).toBeVisible();

    // Verify Dashboard navigation tab is active by default
    await expect(page.getByRole('button', { name: 'Dashboard' })).toHaveClass(/border-b-2/);
  });

  test('should switch user between independent accounts', async ({ page }) => {
    await page.goto('/');

    // Open profile menu
    const profileBtn = page.locator('header').locator('button').filter({ hasText: 'Alex Taylor' });
    await profileBtn.click();

    // Click Switch or Sign In User
    await page.getByRole('button', { name: /Switch or Sign In User/i }).click();

    // Verify Auth Modal appears with Switch User tab
    const modal = page.locator('.fixed.inset-0').filter({ hasText: /Sign In|Switch/i });
    await expect(modal).toBeVisible();

    // Click Switch User tab
    await modal.getByRole('button', { name: /Switch User/i }).click();

    // Select Sarah Jenkins
    await modal.getByRole('button', { name: /Sarah Jenkins/i }).click();

    // Modal closes and header now shows Sarah Jenkins
    await expect(modal).toBeHidden();
    await expect(page.locator('header').getByText('Sarah Jenkins')).toBeVisible();
  });

  test('should log out and log back in with email and password', async ({ page }) => {
    await page.goto('/');

    // Open profile menu and log out
    const profileBtn = page.locator('header').locator('button').filter({ hasText: 'Alex Taylor' });
    await profileBtn.click();
    await page.getByRole('button', { name: /Log Out/i }).click();

    // Header should now show generic Account
    const accountBtn = page.locator('header').locator('button').filter({ hasText: /Account/i });
    await expect(accountBtn).toBeVisible();

    // Open Auth modal to sign back in
    await accountBtn.click();
    await page.getByRole('button', { name: /Switch or Sign In User/i }).click();

    const modal = page.locator('.fixed.inset-0').filter({ hasText: /Sign In to Account/i });
    await expect(modal).toBeVisible();

    // Fill login form
    await modal.locator('#auth-email').fill('alex@example.com');
    await modal.locator('#auth-password').fill('password123');
    await modal.locator('button[type="submit"]').click();

    // Verify user is back
    await expect(modal).toBeHidden();
    await expect(page.locator('header').getByText('Alex Taylor')).toBeVisible();
  });

  test('should register a new independent user account', async ({ page }) => {
    const timestamp = Date.now();
    const testEmail = `newuser_${timestamp}@example.com`;
    const testName = `New User ${timestamp}`;

    await page.goto('/');

    // Open auth modal
    const profileBtn = page.locator('header').locator('button').filter({ hasText: /Alex Taylor|Account/i });
    await profileBtn.click();
    await page.getByRole('button', { name: /Switch or Sign In User/i }).click();

    const modal = page.locator('.fixed.inset-0').filter({ hasText: /Sign In|Create New Account/i });
    await expect(modal).toBeVisible();

    // Switch to Sign Up tab
    await modal.getByRole('button', { name: 'Sign Up', exact: true }).click();
    await expect(modal.getByRole('heading', { name: 'Create New Account' })).toBeVisible();

    // Fill signup form
    await modal.locator('#auth-name').fill(testName);
    await modal.locator('#auth-email').fill(testEmail);
    await modal.locator('#auth-password').fill('securepass123');
    await modal.getByRole('button', { name: 'Create Account' }).click();

    // User should be logged in
    await expect(modal).toBeHidden();
    await expect(page.locator('header').getByText(testName)).toBeVisible();

    // Verify fresh dashboard with no overdue items
    await expect(page.getByText('No overdue lifecycle items!')).toBeVisible();
  });
});
