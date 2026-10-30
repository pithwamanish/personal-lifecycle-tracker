import { test, expect } from '@playwright/test';
import { resetDatabase } from './helpers';

test.describe('Full MVP Specification Compliance Journey (@spec.md Section 6)', () => {
  test.beforeEach(async () => {
    await resetDatabase();
  });

  test('end-to-end acceptance flow validating all Section 6 criteria', async ({ page }) => {
    test.setTimeout(120000);
    const timestamp = Date.now();
    const userEmail = `auditor_${timestamp}@example.com`;
    const userName = `Auditor ${timestamp}`;
    const groupName = `Audited Home Group ${timestamp}`;
    const renewalName = `Vehicle Fleet Registration ${timestamp}`;
    const maintenanceName = `Solar Inverter Servicing ${timestamp}`;
    const warrantyName = `Heat Pump Warranty ${timestamp}`;

    // ----------------------------------------------------
    // 1. Register and log in with email and password
    // ----------------------------------------------------
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Open user menu -> Switch or Sign In User
    const userBtn = page.locator('header').locator('button').filter({ hasText: /Alex Taylor|Sarah|Account/i }).first();
    await userBtn.click();
    await page.getByRole('button', { name: /Switch or Sign In User/i }).click();

    const authModal = page.locator('.fixed.inset-0').filter({ hasText: /Sign In|Create New Account/i });
    await expect(authModal).toBeVisible();

    // Sign up
    await authModal.getByRole('button', { name: 'Sign Up', exact: true }).click();
    await authModal.locator('#auth-name').fill(userName);
    await authModal.locator('#auth-email').fill(userEmail);
    await authModal.locator('#auth-password').fill('pass12345');
    await authModal.getByRole('button', { name: 'Create Account' }).click();

    await expect(authModal).toBeHidden();
    await expect(page.locator('header').getByText(userName)).toBeVisible();

    // ----------------------------------------------------
    // 2. Create a group and invite members by email
    // ----------------------------------------------------
    await page.getByRole('button', { name: 'Groups' }).click();
    await expect(page.getByRole('heading', { name: 'Groups & Shared Access' })).toBeVisible();

    const groupInput = page.locator('input[placeholder="e.g. Oakridge Family & Home"]');
    await groupInput.fill(groupName);
    await page.getByRole('button', { name: 'Create Group' }).click();

    const groupCard = page.locator('.bg-white').filter({ hasText: groupName });
    await expect(groupCard).toBeVisible();

    // Invite member
    const invitee = `technician_${timestamp}@example.com`;
    await groupCard.locator('input[type="email"]').fill(invitee);
    await groupCard.getByRole('button', { name: 'Invite' }).click();
    await expect(groupCard.getByText(invitee)).toBeVisible();

    // ----------------------------------------------------
    // 3. Create renewal, maintenance, and warranty items using a guided form
    //    with common fields (Name, Type, Due date, Status, Group)
    // ----------------------------------------------------
    // 3a. Create Renewal (due in 15 days -> upcoming)
    await page.getByRole('button', { name: /Track Item/i }).click();
    const createModal = page.locator('.fixed.inset-0').filter({ hasText: /Step [12]:/i });
    await expect(createModal).toBeVisible();
    await createModal.getByRole('button', { name: /Renewal/i }).click();

    await page.locator('#item-name').fill(renewalName);
    const date15 = new Date();
    date15.setDate(date15.getDate() + 15);
    await page.locator('#item-due-date').fill(date15.toISOString().slice(0, 10));
    await page.locator('.fixed.inset-0').getByRole('button', { name: /Track Item/i }).click();
    await expect(createModal).toBeHidden();

    // 3b. Create Maintenance (due 5 days ago -> overdue)
    await page.getByRole('button', { name: /Track Item/i }).click();
    await createModal.getByRole('button', { name: /Maintenance/i }).click();
    await page.locator('#item-name').fill(maintenanceName);
    const datePast = new Date();
    datePast.setDate(datePast.getDate() - 5);
    await page.locator('#item-due-date').fill(datePast.toISOString().slice(0, 10));
    // Assign to group
    await page.locator('#item-group').selectOption({ label: `Group: ${groupName}` });
    await page.locator('.fixed.inset-0').getByRole('button', { name: /Track Item/i }).click();
    await expect(createModal).toBeHidden();

    // 3c. Create Warranty without due date (Decision 29)
    await page.getByRole('button', { name: /Track Item/i }).click();
    await createModal.getByRole('button', { name: /Warranty/i }).click();
    await page.locator('#item-name').fill(warrantyName);
    await page.locator('.fixed.inset-0 input[type="checkbox"]').uncheck();
    await page.locator('.fixed.inset-0').getByRole('button', { name: /Track Item/i }).click();
    await expect(createModal).toBeHidden();

    // ----------------------------------------------------
    // 4. View items in lists separated by lifecycle type
    // ----------------------------------------------------
    // Renewals view
    await page.getByRole('button', { name: 'Renewals' }).click();
    await expect(page.locator(`text=${renewalName}`).first()).toBeVisible();

    // Maintenance view
    await page.getByRole('button', { name: 'Maintenance' }).click();
    await expect(page.locator(`text=${maintenanceName}`).first()).toBeVisible();

    // Warranties view
    await page.getByRole('button', { name: 'Warranties' }).click();
    await expect(page.locator(`text=${warrantyName}`).first()).toBeVisible();

    // ----------------------------------------------------
    // 5. See upcoming actions and overdue items on Dashboard
    // ----------------------------------------------------
    await page.getByRole('button', { name: 'Dashboard' }).click();

    // Overdue section must contain Maintenance
    const overdueSection = page.locator('section').filter({ hasText: /Overdue Items/i });
    await expect(overdueSection.getByText(maintenanceName)).toBeVisible();

    // Upcoming section must contain Renewal
    const upcomingSection = page.locator('section').filter({ hasText: /Upcoming Actions/i });
    await expect(upcomingSection.getByText(renewalName)).toBeVisible();

    // ----------------------------------------------------
    // 6. Mark an item complete while retaining it in the main list
    // ----------------------------------------------------
    const overdueRow = overdueSection.locator('.group').filter({ hasText: maintenanceName });
    await overdueRow.getByRole('button', { name: /Mark as complete/i }).click();

    // Retained in main list under Completed Records section with line-through
    const completedSection = page.locator('section').filter({ hasText: /Completed Records/i });
    await expect(completedSection.getByText(maintenanceName)).toBeVisible();
    await expect(completedSection.locator('.group').filter({ hasText: maintenanceName }).locator('span.line-through')).toContainText(maintenanceName);

    // ----------------------------------------------------
    // 7. Receive in-app reminders and daily email digest
    // ----------------------------------------------------
    // In-app reminders
    const bellBtn = page.getByRole('button', { name: /Open Reminders/i });
    await bellBtn.click();
    const reminderDrawer = page.locator('.fixed.inset-0').filter({ hasText: /In-App Reminders/i });
    await expect(reminderDrawer).toBeVisible();
    await expect(reminderDrawer.getByText(renewalName)).toBeVisible();
    await reminderDrawer.getByRole('button', { name: /Close drawer/i }).click();

    // Daily digest
    await page.getByRole('button', { name: 'Daily Digest', exact: true }).click();
    await expect(page.getByText('Dual Channel Enabled')).toBeVisible();
    // Configure delivery time
    await page.locator('button').filter({ hasText: 'Option C' }).first().click();
    await expect(page.getByText('Saved')).toBeVisible();

    // Simulate digest
    await page.getByRole('button', { name: /Simulate \/ Send Digest Now/i }).click();
    await expect(page.getByText('Email Digest Preview')).toBeVisible();
    await expect(page.getByText(/\[Action Required\]|\[Upcoming Actions\]|\[Lifecycle Tracker\]/i).first()).toBeVisible();

    // ----------------------------------------------------
    // 8. Permanently delete item, group, and account
    // ----------------------------------------------------
    // Delete item
    await page.getByRole('button', { name: 'Renewals' }).click();
    const renewalRow = page.locator('.group').filter({ hasText: renewalName });
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });
    await renewalRow.getByRole('button', { name: /Permanently delete item/i }).click();
    await expect(page.locator('.group').filter({ hasText: renewalName })).toHaveCount(0);

    // Delete group
    await page.getByRole('button', { name: 'Groups' }).click();
    const groupToDelete = page.locator('.bg-white').filter({ hasText: groupName });
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });
    await groupToDelete.getByRole('button', { name: 'Delete group' }).click();
    await expect(page.locator('.bg-white').filter({ hasText: groupName })).toHaveCount(0);

    // Delete account
    const finalProfileBtn = page.locator('header').locator('button').filter({ hasText: userName });
    await finalProfileBtn.click();
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });
    await page.getByRole('button', { name: /Delete Account/i }).click();

    // Verified account deletion completed and redirected/reset
    await expect(page.locator('header').getByText(userName)).toHaveCount(0);
  });
});
