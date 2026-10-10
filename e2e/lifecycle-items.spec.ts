import { test, expect } from '@playwright/test';
import { resetDatabase } from './helpers';

test.describe('Lifecycle Items Management Flow (@spec.md Decision 5, 7, 8, 11, 12, 19, 25, 28, 29)', () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test('should create a renewal item using the guided two-step form', async ({ page }) => {
    await page.goto('/');

    // Click Track Item in navbar
    await page.getByRole('button', { name: /Track Item/i }).click();

    // Step 1: Choose Lifecycle Type modal
    const modal = page.locator('.fixed.inset-0').filter({ hasText: /Step [12]:/i });
    await expect(modal).toBeVisible();

    // Select Renewal
    await modal.getByRole('button', { name: /Renewal/i }).click();

    // Step 2: Enter common fields
    await expect(page.locator('.fixed.inset-0').getByText(/Step 2: Track New/i)).toBeVisible();

    const testItemName = 'E2E Motorcycle Registration';
    await page.locator('#item-name').fill(testItemName);

    // Set a future date (e.g., 20 days ahead)
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 20);
    const dateStr = futureDate.toISOString().slice(0, 10);
    await page.locator('#item-due-date').fill(dateStr);

    // Submit form
    await page.locator('.fixed.inset-0').getByRole('button', { name: /Track Item/i }).click();
    await expect(modal).toBeHidden();

    // Verify item appears on Dashboard in Upcoming section
    await expect(page.locator(`text=${testItemName}`).first()).toBeVisible();

    // Navigate to Renewals tab and verify item is listed
    await page.getByRole('button', { name: 'Renewals' }).click();
    await expect(page.locator(`text=${testItemName}`).first()).toBeVisible();
  });

  test('should create an item with missing due date (allowed per Decision 29)', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /Track Item/i }).click();
    const modal = page.locator('.fixed.inset-0').filter({ hasText: /Step [12]:/i });
    await modal.getByRole('button', { name: /Warranty/i }).click();

    const warrantyName = 'Vintage Mechanical Watch Warranty';
    await page.locator('#item-name').fill(warrantyName);

    // Uncheck "Has specific due date"
    const checkbox = page.locator('.fixed.inset-0 input[type="checkbox"]');
    await checkbox.uncheck();
    await expect(page.locator('.fixed.inset-0').getByText(/No due date specified/i)).toBeVisible();

    // Submit form
    await page.locator('.fixed.inset-0').getByRole('button', { name: /Track Item/i }).click();
    await expect(modal).toBeHidden();

    // Navigate to Warranties tab
    await page.getByRole('button', { name: 'Warranties' }).click();
    const itemRow = page.locator('.group').filter({ hasText: warrantyName });
    await expect(itemRow).toBeVisible();
    await expect(itemRow.getByText(/No due date/i)).toBeVisible();
  });

  test('should toggle item completion and retain completed item in main list (Decision 28)', async ({ page }) => {
    await page.goto('/');

    // Find the overdue item "Vehicle Auto Insurance Policy"
    const itemRow = page.locator('.group').filter({ hasText: 'Vehicle Auto Insurance Policy' }).first();
    await expect(itemRow).toBeVisible();

    // Click completion toggle button
    const toggleBtn = itemRow.getByRole('button', { name: /Mark as complete/i });
    await toggleBtn.click();

    // Item should now be marked complete (line-through style, check icon)
    await expect(itemRow.getByRole('button', { name: /Mark as active/i })).toBeVisible();
    await expect(itemRow.locator('span.line-through')).toContainText('Vehicle Auto Insurance Policy');

    // Per MVP Decision 28: Item remains visible in the list!
    await expect(itemRow).toBeVisible();

    // Toggle back to active
    await itemRow.getByRole('button', { name: /Mark as active/i }).click();
    await expect(itemRow.getByRole('button', { name: /Mark as complete/i })).toBeVisible();
  });

  test('should edit an existing item via edit modal', async ({ page }) => {
    await page.goto('/');

    const itemRow = page.locator('.group').filter({ hasText: 'International Passport Renewal' }).first();
    await expect(itemRow).toBeVisible();

    // Click edit button
    await itemRow.getByRole('button', { name: /Edit item/i }).click();

    const editModal = page.locator('.fixed.inset-0').filter({ hasText: /Edit Lifecycle Item/i });
    await expect(editModal).toBeVisible();

    // Change name
    const updatedName = 'International Passport Renewal (Expedited)';
    await editModal.locator('#edit-name').fill(updatedName);
    await editModal.getByRole('button', { name: /Save Changes/i }).click();

    await expect(editModal).toBeHidden();
    await expect(page.locator(`text=${updatedName}`).first()).toBeVisible();
  });

  test('should permanently delete an item (Decision 19)', async ({ page }) => {
    await page.goto('/');

    const itemName = 'International Passport Renewal';
    const itemRow = page.locator('.group').filter({ hasText: itemName }).first();
    await expect(itemRow).toBeVisible();

    // Accept window confirmation dialog
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    // Click delete
    await itemRow.getByRole('button', { name: /Permanently delete item/i }).click();

    // Verify item is permanently removed
    await expect(page.locator('.group').filter({ hasText: itemName })).toHaveCount(0);
  });

  test('should filter dashboard items by scope (All vs Personal vs Group)', async ({ page }) => {
    await page.goto('/');

    const scopeSelect = page.locator('select').filter({ hasText: /All Accessible Items/i }).first();
    await expect(scopeSelect).toBeVisible();

    // Select Personal Only
    await scopeSelect.selectOption('PERSONAL');
    // Group items like "Oakridge Family & Home" should not appear with group badge
    await expect(page.locator('.group').filter({ hasText: 'Shared Vehicle Maintenance' })).toHaveCount(0);

    // Select Shared Vehicle Maintenance group
    await scopeSelect.selectOption({ label: 'Group: Shared Vehicle Maintenance' });
    await expect(page.locator('.group').filter({ hasText: 'Vehicle Auto Insurance Policy' }).first()).toBeVisible();
  });
});
