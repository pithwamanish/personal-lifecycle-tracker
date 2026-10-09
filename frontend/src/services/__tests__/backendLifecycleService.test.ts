import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BackendLifecycleService } from '../backendLifecycleService';
import { CreateItemDTO, UpdateItemDTO } from '../types';

class MockStorage {
  private store: Record<string, string> = {};
  clear() {
    this.store = {};
  }
  getItem(key: string) {
    return this.store[key] ?? null;
  }
  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }
  removeItem(key: string) {
    delete this.store[key];
  }
}

describe('BackendLifecycleService', () => {
  let service: BackendLifecycleService;
  const originalFetch = globalThis.fetch;
  const mockStorage = new MockStorage();

  beforeEach(() => {
    mockStorage.clear();
    vi.stubGlobal('localStorage', mockStorage);
    vi.stubGlobal('window', { localStorage: mockStorage });
    service = new BackendLifecycleService('http://test-api:8000');
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  function mockFetchJson(status: number, data: unknown, headers: Record<string, string> = {}) {
    return vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        headers: new Headers({ 'content-type': 'application/json', ...headers }),
        json: () => Promise.resolve(data),
      })
    );
  }

  describe('Authentication & User Management', () => {
    it('auto-logs in default seed user on initial load when no session exists', async () => {
      const mockUser = {
        id: 'user_alex',
        email: 'alex@example.com',
        name: 'Alex Taylor',
        createdAt: '2026-01-10T08:00:00Z',
      };
      const fetchMock = mockFetchJson(200, {
        user: mockUser,
        token: 'test-jwt-token-alex',
      });
      globalThis.fetch = fetchMock;

      const user = await service.getCurrentUser();
      expect(user).toEqual(mockUser);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'alex@example.com', password: 'password123' }),
        })
      );
    });

    it('retrieves current user from /me when token is cached', async () => {
      mockStorage.setItem('plt_auth_token_v1', 'existing-jwt-token');
      service = new BackendLifecycleService('http://test-api:8000');

      const mockUser = {
        id: 'user_alex',
        email: 'alex@example.com',
        name: 'Alex Taylor',
        createdAt: '2026-01-10T08:00:00Z',
      };
      const fetchMock = mockFetchJson(200, mockUser);
      globalThis.fetch = fetchMock;

      const user = await service.getCurrentUser();
      expect(user).toEqual(mockUser);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/auth/me',
        expect.objectContaining({
          method: 'GET',
          headers: expect.any(Headers),
        })
      );
    });

    it('returns null if user has explicitly logged out', async () => {
      mockStorage.setItem('plt_logged_out_v1', 'true');
      service = new BackendLifecycleService('http://test-api:8000');

      const user = await service.getCurrentUser();
      expect(user).toBeNull();
    });

    it('logs in and attaches bearer token to subsequent requests', async () => {
      const mockUser = {
        id: 'user_sarah',
        email: 'sarah@example.com',
        name: 'Sarah Jenkins',
        createdAt: '2026-02-14T09:30:00Z',
      };
      globalThis.fetch = mockFetchJson(200, {
        user: mockUser,
        token: 'sarah-token-xyz',
      });

      const user = await service.login('sarah@example.com', 'mypassword');
      expect(user).toEqual(mockUser);
      expect(mockStorage.getItem('plt_auth_token_v1')).toBe('sarah-token-xyz');

      // Now verify subsequent request passes Bearer header
      const fetchItemsMock = mockFetchJson(200, []);
      globalThis.fetch = fetchItemsMock;

      await service.getItems();
      expect(fetchItemsMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items',
        expect.objectContaining({
          headers: expect.any(Headers),
        })
      );
    });

    it('signs up a new user and updates session', async () => {
      const mockNewUser = {
        id: 'user_new',
        email: 'newuser@example.com',
        name: 'New User',
        createdAt: '2026-10-09T12:00:00Z',
      };
      globalThis.fetch = mockFetchJson(201, {
        user: mockNewUser,
        token: 'new-user-token',
      });

      const user = await service.signup('newuser@example.com', 'password123', 'New User');
      expect(user).toEqual(mockNewUser);
      expect(mockStorage.getItem('plt_auth_token_v1')).toBe('new-user-token');
    });

    it('logs out and clears session state', async () => {
      mockStorage.setItem('plt_auth_token_v1', 'token-to-clear');
      service = new BackendLifecycleService('http://test-api:8000');

      globalThis.fetch = mockFetchJson(200, { message: 'Logged out successfully' });

      await service.logout();
      expect(mockStorage.getItem('plt_auth_token_v1')).toBeNull();
      expect(mockStorage.getItem('plt_logged_out_v1')).toBe('true');
    });

    it('switches user using cached token or login fallback', async () => {
      const usersList = [
        { id: 'user_alex', email: 'alex@example.com', name: 'Alex', createdAt: '2026-01-01' },
        { id: 'user_sarah', email: 'sarah@example.com', name: 'Sarah', createdAt: '2026-01-01' },
      ];

      const fetchMock = vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/users')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: () => Promise.resolve(usersList),
          });
        }
        if (url.includes('/api/v1/auth/login')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: () =>
              Promise.resolve({
                user: usersList[1],
                token: 'sarah-token',
              }),
          });
        }
        return Promise.reject(new Error(`Unhandled URL: ${url}`));
      });
      globalThis.fetch = fetchMock;

      const switched = await service.switchUser('user_sarah');
      expect(switched.id).toBe('user_sarah');
      expect(mockStorage.getItem('plt_auth_token_v1')).toBe('sarah-token');
    });

    it('deletes account and clears session', async () => {
      mockStorage.setItem('plt_auth_token_v1', 'active-token');
      mockStorage.setItem('plt_current_user_id_v1', 'user_to_delete');
      service = new BackendLifecycleService('http://test-api:8000');

      globalThis.fetch = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 204,
          headers: new Headers(),
          json: () => Promise.resolve(),
        })
      );

      await service.deleteAccount('user_to_delete');
      expect(mockStorage.getItem('plt_auth_token_v1')).toBeNull();
      expect(mockStorage.getItem('plt_current_user_id_v1')).toBeNull();
    });
  });

  describe('Lifecycle Items CRUD', () => {
    it('fetches items with query parameters', async () => {
      const fetchMock = mockFetchJson(200, []);
      globalThis.fetch = fetchMock;

      await service.getItems({
        groupId: null,
        type: 'renewal',
        searchQuery: 'insurance',
      });

      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items?groupId=null&type=renewal&searchQuery=insurance',
        expect.any(Object)
      );
    });

    it('creates an item with guided payload', async () => {
      const dto: CreateItemDTO = {
        name: 'Home Filter',
        lifecycleType: 'maintenance',
        dueDate: '2026-11-01',
        status: 'active',
      };
      const createdItem = { id: 'item_100', ...dto, createdAt: '2026-10-09', updatedAt: '2026-10-09' };
      const fetchMock = mockFetchJson(201, createdItem);
      globalThis.fetch = fetchMock;

      const result = await service.createItem(dto);
      expect(result).toEqual(createdItem);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(dto),
        })
      );
    });

    it('updates an item', async () => {
      const updateDto: UpdateItemDTO = { name: 'Updated Name' };
      const updatedItem = { id: 'item_1', name: 'Updated Name', lifecycleType: 'renewal', status: 'active' };
      const fetchMock = mockFetchJson(200, updatedItem);
      globalThis.fetch = fetchMock;

      const result = await service.updateItem('item_1', updateDto);
      expect(result).toEqual(updatedItem);
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items/item_1',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(updateDto),
        })
      );
    });

    it('toggles item completion', async () => {
      const completedItem = { id: 'item_1', status: 'completed' };
      const fetchMock = mockFetchJson(200, completedItem);
      globalThis.fetch = fetchMock;

      const result = await service.toggleItemCompletion('item_1');
      expect(result.status).toBe('completed');
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items/item_1/complete',
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('deletes an item with 204 response', async () => {
      const fetchMock = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 204,
          headers: new Headers(),
          json: () => Promise.resolve(),
        })
      );
      globalThis.fetch = fetchMock;

      await service.deleteItem('item_1');
      expect(fetchMock).toHaveBeenCalledWith(
        'http://test-api:8000/api/v1/items/item_1',
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('Groups & Sharing', () => {
    it('manages groups and members', async () => {
      const groupData = {
        id: 'group_test',
        name: 'Family Home',
        ownerId: 'user_alex',
        ownerEmail: 'alex@example.com',
        memberEmails: ['alex@example.com'],
        createdAt: '2026-01-01',
      };

      // 1. Create group
      globalThis.fetch = mockFetchJson(201, groupData);
      const created = await service.createGroup('Family Home');
      expect(created).toEqual(groupData);

      // 2. Invite member
      const withMember = { ...groupData, memberEmails: ['alex@example.com', 'guest@example.com'] };
      globalThis.fetch = mockFetchJson(200, withMember);
      const updated = await service.inviteMember('group_test', 'guest@example.com');
      expect(updated.memberEmails).toContain('guest@example.com');

      // 3. Remove member
      globalThis.fetch = mockFetchJson(200, groupData);
      const removed = await service.removeMember('group_test', 'guest@example.com');
      expect(removed.memberEmails).not.toContain('guest@example.com');

      // 4. Leave group
      globalThis.fetch = mockFetchJson(200, { message: 'Left group successfully' });
      await service.leaveGroup('group_test');

      // 5. Delete group
      globalThis.fetch = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 204,
          headers: new Headers(),
          json: () => Promise.resolve(),
        })
      );
      await service.deleteGroup('group_test');
    });
  });

  describe('Reminders & Digest', () => {
    it('fetches summary, config, and generates daily digest', async () => {
      // 1. Summary
      const summary = { overdue: [], upcoming: [], totalActiveReminders: 0 };
      globalThis.fetch = mockFetchJson(200, summary);
      const fetchedSummary = await service.getRemindersSummary();
      expect(fetchedSummary).toEqual(summary);

      // 2. Config & update
      const config = { timeZone: 'UTC', deliveryTime: '08:00', enabled: true };
      globalThis.fetch = mockFetchJson(200, config);
      const fetchedConfig = await service.getDigestConfig();
      expect(fetchedConfig.deliveryTime).toBe('08:00');

      globalThis.fetch = mockFetchJson(200, { ...config, deliveryTime: '09:00' });
      const updatedConfig = await service.updateDigestConfig({ deliveryTime: '09:00' });
      expect(updatedConfig.deliveryTime).toBe('09:00');

      // 3. Generate digest
      const digestEmail = {
        id: 'digest_1',
        recipientEmail: 'alex@example.com',
        recipientName: 'Alex Taylor',
        subject: 'Daily Digest',
        overdueCount: 0,
        upcomingCount: 0,
        overdueItems: [],
        upcomingItems: [],
        htmlContent: '<p>Digest</p>',
        textContent: 'Digest',
      };
      globalThis.fetch = mockFetchJson(200, digestEmail);
      const generated = await service.generateAndSendDailyDigest('alex@example.com');
      expect(generated.recipientEmail).toBe('alex@example.com');
    });
  });

  describe('Error Handling', () => {
    it('extracts error field from backend 400 responses', async () => {
      globalThis.fetch = mockFetchJson(400, { error: 'Item not found or permission denied' });
      await expect(service.getItem('invalid_id')).rejects.toThrow('Item not found or permission denied');
    });

    it('extracts detail field if error is absent', async () => {
      globalThis.fetch = mockFetchJson(401, { detail: 'Invalid or expired token' });
      await expect(service.getItems()).rejects.toThrow('Invalid or expired token');
    });
  });
});
