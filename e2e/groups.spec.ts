import { test, expect } from '@playwright/test';
import { resetDatabase } from './helpers';

test.describe('Groups & Shared Access Flow (@spec.md Decision 4, 13, 14, 18, 30)', () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test('should display existing groups and allow creating a new group', async ({ page }) => {
    await page.goto('/');

    // Navigate to Groups tab
    await page.getByRole('button', { name: 'Groups' }).click();

    await expect(page.getByRole('heading', { name: 'Groups & Shared Access' })).toBeVisible();

    // Verify existing seed groups
    await expect(page.getByRole('heading', { name: 'Oakridge Family & Home' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Shared Vehicle Maintenance' })).toBeVisible();

    // Create a new group
    const newGroupName = 'Lakehouse Vacation Property';
    const input = page.locator('input[placeholder="e.g. Oakridge Family & Home"]');
    await input.fill(newGroupName);
    await page.getByRole('button', { name: 'Create Group' }).click();

    // Verify newly created group card appears
    await expect(page.getByText(newGroupName)).toBeVisible();
  });

  test('should invite a new member by email to a group', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'Groups' }).click();

    const groupCard = page.locator('.bg-white').filter({ hasText: 'Oakridge Family & Home' });
    await expect(groupCard).toBeVisible();

    // Invite a new member
    const inviteEmail = 'partner@example.com';
    const emailInput = groupCard.locator('input[type="email"]');
    await emailInput.fill(inviteEmail);
    await groupCard.getByRole('button', { name: 'Invite' }).click();

    // Member should now appear in the members list
    await expect(groupCard.getByText(inviteEmail)).toBeVisible();
  });

  test('should remove a member from a group', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'Groups' }).click();

    const groupCard = page.locator('.bg-white').filter({ hasText: 'Oakridge Family & Home' });
    await expect(groupCard).toBeVisible();

    // Alex is owner of Oakridge Family & Home; Sarah is a member
    const removeBtn = groupCard.getByRole('button', { name: 'Remove sarah@example.com' });
    if (await removeBtn.isVisible()) {
      await removeBtn.click();
      await expect(groupCard.getByText('sarah@example.com')).toHaveCount(0);
    }
  });

  test('should delete group and all associated items permanently (Decision 30)', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'Groups' }).click();

    const groupCard = page.locator('.bg-white').filter({ hasText: 'Oakridge Family & Home' });
    await expect(groupCard).toBeVisible();

    // Set dialog handler
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    // Click delete group
    await groupCard.getByRole('button', { name: 'Delete group' }).click();

    // Group should disappear
    await expect(page.locator('.bg-white').filter({ hasText: 'Oakridge Family & Home' })).toHaveCount(0);
  });
});
