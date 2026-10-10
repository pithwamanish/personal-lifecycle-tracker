import { test, expect } from '@playwright/test';
import { resetDatabase } from './helpers';

test.describe('Reminders & Daily Email Digest Flow (@spec.md Decision 6, 15, 22, 31, 32, 33, Question 34)', () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test('should open In-App Reminders drawer from Navbar bell and show active items', async ({ page }) => {
    await page.goto('/');

    // Bell button should exist
    const bellBtn = page.getByRole('button', { name: /Open Reminders/i });
    await expect(bellBtn).toBeVisible();

    // Open Reminders drawer
    await bellBtn.click();

    // Drawer should appear
    const drawer = page.locator('.fixed.inset-0').filter({ hasText: /In-App Reminders/i });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText(/Overdue \(/i)).toBeVisible();
    await expect(drawer.getByText(/Upcoming Within 30 Days/i)).toBeVisible();

    // Close drawer
    await drawer.getByRole('button', { name: /Close drawer/i }).click();
    await expect(drawer).toBeHidden();
  });

  test('should configure daily digest delivery time and simulate email generation', async ({ page }) => {
    await page.goto('/');

    // Navigate to Daily Digest tab
    await page.getByRole('button', { name: 'Daily Digest', exact: true }).click();

    // Verify header and permanent dual-channel notice (Decision 22)
    await expect(page.getByRole('heading', { name: 'Reminders & Daily Email Digest' })).toBeVisible();
    await expect(page.getByText('Dual Channel Enabled')).toBeVisible();

    // Verify Question 34 delivery time options
    await expect(page.getByText('Option A')).toBeVisible();
    await expect(page.getByText('6:00 AM')).toBeVisible();
    await expect(page.getByText('Option B')).toBeVisible();
    await expect(page.getByText('8:00 AM')).toBeVisible();
    await expect(page.getByText('Option C')).toBeVisible();
    await expect(page.getByText('Option D')).toBeVisible();

    // Select Option A (6:00 AM)
    const optionA = page.locator('button').filter({ hasText: 'Option A' }).first();
    await optionA.click();

    // Verify saved indicator
    await expect(page.getByText('Saved')).toBeVisible();

    // Trigger Simulate / Send Digest Now
    const sendBtn = page.getByRole('button', { name: /Simulate \/ Send Digest Now/i });
    await sendBtn.click();

    // Wait for generation to finish
    await expect(page.getByText('Email Digest Preview')).toBeVisible();
    await expect(page.getByText(/\[Action Required\]|\[Upcoming Actions\]|\[Lifecycle Tracker\]/i).first()).toBeVisible();

    // Check preview switcher between HTML and Plain Text
    const textTab = page.getByRole('button', { name: /Plain Text/i });
    if (await textTab.isVisible()) {
      await textTab.click();
      await expect(page.locator('pre')).toBeVisible();
    }
  });
});
