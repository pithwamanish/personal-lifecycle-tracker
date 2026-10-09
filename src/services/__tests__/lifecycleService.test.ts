import { beforeEach, describe, expect, it } from 'vitest';
import { MockLifecycleService } from '../mockLifecycleService';

describe('MockLifecycleService', () => {
  let service: MockLifecycleService;

  beforeEach(async () => {
    service = new MockLifecycleService();
    await service.resetToDefaultSeed();
  });

  describe('Authentication & User Management', () => {
    it('initializes with seed user Alex Taylor', async () => {
      const user = await service.getCurrentUser();
      expect(user).not.toBeNull();
      expect(user?.email).toBe('alex@example.com');
    });

    it('signs up and logs in a new user with email and password', async () => {
      const newUser = await service.signup('clara@example.com', 'secret123', 'Clara Barton');
      expect(newUser.email).toBe('clara@example.com');
      expect(newUser.name).toBe('Clara Barton');

      const current = await service.getCurrentUser();
      expect(current?.id).toBe(newUser.id);
    });

    it('switches between multiple users', async () => {
      const users = await service.listUsers();
      const sarah = users.find((u) => u.email === 'sarah@example.com');
      expect(sarah).toBeDefined();

      if (sarah) {
        await service.switchUser(sarah.id);
        const current = await service.getCurrentUser();
        expect(current?.email).toBe('sarah@example.com');
      }
    });
  });

  describe('Lifecycle Items CRUD & Common Fields', () => {
    it('creates an item with guided lifecycle type and common fields only', async () => {
      const item = await service.createItem({
        name: 'Annual Dental Checkup',
        lifecycleType: 'renewal',
        dueDate: '2026-11-01',
        status: 'active',
      });

      expect(item.id).toBeDefined();
      expect(item.name).toBe('Annual Dental Checkup');
      expect(item.lifecycleType).toBe('renewal');
      expect(item.dueDate).toBe('2026-11-01');
      expect(item.status).toBe('active');
    });

    it('supports missing due date per Decision 29', async () => {
      const item = await service.createItem({
        name: 'Smoke Detector Battery Test',
        lifecycleType: 'maintenance',
        dueDate: undefined,
        status: 'active',
      });

      expect(item.dueDate).toBeUndefined();
    });

    it('retains completed items in main list per Decision 8 & 28', async () => {
      const item = await service.createItem({
        name: 'Coffee Maker Descaling',
        lifecycleType: 'maintenance',
        dueDate: '2026-10-15',
        status: 'active',
      });

      const toggled = await service.toggleItemCompletion(item.id);
      expect(toggled.status).toBe('completed');

      const allItems = await service.getItems();
      const found = allItems.find((i) => i.id === item.id);
      expect(found).toBeDefined();
      expect(found?.status).toBe('completed');
    });

    it('permanently deletes an item per Decision 19', async () => {
      const item = await service.createItem({
        name: 'Temporary item',
        lifecycleType: 'warranty',
      });

      await service.deleteItem(item.id);
      const allItems = await service.getItems();
      expect(allItems.find((i) => i.id === item.id)).toBeUndefined();
    });
  });

  describe('Groups & Shared Access', () => {
    it('allows a user to create a group and invite members by email', async () => {
      const group = await service.createGroup('Vacation Cabin Care');
      expect(group.name).toBe('Vacation Cabin Care');
      expect(group.memberEmails).toContain('alex@example.com');

      const updatedGroup = await service.inviteMember(group.id, 'sarah@example.com');
      expect(updatedGroup.memberEmails).toContain('sarah@example.com');
    });

    it('allows all group members to manage shared items per Decision 14', async () => {
      // Alex creates group item
      const group = await service.createGroup('Co-op Garden');
      await service.inviteMember(group.id, 'sarah@example.com');

      const sharedItem = await service.createItem({
        name: 'Irrigation Winterization',
        lifecycleType: 'maintenance',
        dueDate: '2026-11-15',
        groupId: group.id,
      });

      // Switch to Sarah
      const users = await service.listUsers();
      const sarah = users.find((u) => u.email === 'sarah@example.com')!;
      await service.switchUser(sarah.id);

      // Sarah can edit or complete the shared item
      const updatedBySarah = await service.updateItem(sharedItem.id, {
        name: 'Irrigation Winterization & Valve Drain',
      });
      expect(updatedBySarah.name).toBe('Irrigation Winterization & Valve Drain');

      const completed = await service.toggleItemCompletion(sharedItem.id);
      expect(completed.status).toBe('completed');
    });

    it('deleting a group deletes the group and all its shared items per Decision 30', async () => {
      const group = await service.createGroup('Cabin Maintenance');
      const item = await service.createItem({
        name: 'Chimney Sweep',
        lifecycleType: 'maintenance',
        groupId: group.id,
      });

      await service.deleteGroup(group.id);

      const groups = await service.getGroups();
      expect(groups.find((g) => g.id === group.id)).toBeUndefined();

      const items = await service.getItems();
      expect(items.find((i) => i.id === item.id)).toBeUndefined();
    });
  });

  describe('Account Deletion cascading per Decision 23', () => {
    it('removes everything associated with the account', async () => {
      // Create user Clara
      const clara = await service.signup('clara2@example.com', 'pass', 'Clara Barton');
      const group = await service.createGroup('Clara Group');
      await service.createItem({
        name: 'Clara Personal Item',
        lifecycleType: 'renewal',
      });
      await service.createItem({
        name: 'Clara Group Item',
        lifecycleType: 'warranty',
        groupId: group.id,
      });

      // Delete Clara's account
      await service.deleteAccount(clara.id);

      const users = await service.listUsers();
      expect(users.find((u) => u.id === clara.id)).toBeUndefined();

      // Log in as Alex and verify Clara's owned group is gone
      const alex = users.find((u) => u.email === 'alex@example.com')!;
      await service.switchUser(alex.id);
      const alexGroups = await service.getGroups();
      expect(alexGroups.find((g) => g.id === group.id)).toBeUndefined();
    });
  });

  describe('Reminders and Daily Digest', () => {
    it('computes reminders summary containing overdue and upcoming items', async () => {
      const reminders = await service.getRemindersSummary();
      expect(reminders.overdue.length).toBeGreaterThan(0);
      expect(reminders.upcoming.length).toBeGreaterThan(0);
    });

    it('generates daily digest email with upcoming and overdue items per Decision 32 & 33', async () => {
      const digest = await service.generateAndSendDailyDigest('alex@example.com');
      expect(digest.recipientEmail).toBe('alex@example.com');
      expect(digest.overdueItems.length).toBeGreaterThan(0);
      expect(digest.upcomingItems.length).toBeGreaterThan(0);
      expect(digest.htmlContent).toContain('Personal Lifecycle Tracker');
      expect(digest.textContent).toContain('DAILY DIGEST');
    });

    it('allows updating daily digest delivery time per Question 34', async () => {
      const updated = await service.updateDigestConfig({ deliveryTime: '06:00' });
      expect(updated.deliveryTime).toBe('06:00');
    });
  });
});
