import { ILifecycleService } from './api';
import { getItemUrgency, getTodayDateString } from './dateUtils';
import { buildDailyDigestEmail } from './digestService';
import {
  CreateItemDTO,
  DailyDigestConfig,
  DailyDigestEmail,
  Group,
  LifecycleItem,
  LifecycleType,
  RemindersSummary,
  UpdateItemDTO,
  User,
} from './types';

const STORAGE_KEYS = {
  USERS: 'plt_users_v1',
  CURRENT_USER_ID: 'plt_current_user_id_v1',
  GROUPS: 'plt_groups_v1',
  ITEMS: 'plt_items_v1',
  DIGEST_CONFIG: 'plt_digest_config_v1',
  DIGEST_HISTORY: 'plt_digest_history_v1',
};

function getRelativeDateStr(daysOffset: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const DEFAULT_USERS: User[] = [
  {
    id: 'user_alex',
    email: 'alex@example.com',
    name: 'Alex Taylor',
    createdAt: '2026-01-10T08:00:00Z',
  },
  {
    id: 'user_sarah',
    email: 'sarah@example.com',
    name: 'Sarah Jenkins',
    createdAt: '2026-02-14T09:30:00Z',
  },
  {
    id: 'user_jordan',
    email: 'jordan@example.com',
    name: 'Jordan Patel',
    createdAt: '2026-03-01T11:15:00Z',
  },
];

const DEFAULT_GROUPS: Group[] = [
  {
    id: 'group_home',
    name: 'Oakridge Family & Home',
    ownerId: 'user_alex',
    ownerEmail: 'alex@example.com',
    memberEmails: ['alex@example.com', 'sarah@example.com'],
    createdAt: '2026-02-15T10:00:00Z',
  },
  {
    id: 'group_vehicles',
    name: 'Shared Vehicle Maintenance',
    ownerId: 'user_sarah',
    ownerEmail: 'sarah@example.com',
    memberEmails: ['sarah@example.com', 'alex@example.com', 'jordan@example.com'],
    createdAt: '2026-02-20T14:00:00Z',
  },
];

function generateSeedItems(): LifecycleItem[] {
  return [
    // Renewals
    {
      id: 'item_1',
      name: 'Vehicle Auto Insurance Policy',
      lifecycleType: 'renewal',
      dueDate: getRelativeDateStr(-4), // 4 days overdue
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_vehicles',
      groupName: 'Shared Vehicle Maintenance',
      createdAt: '2026-08-01T08:00:00Z',
      updatedAt: '2026-08-01T08:00:00Z',
    },
    {
      id: 'item_2',
      name: 'International Passport Renewal',
      lifecycleType: 'renewal',
      dueDate: getRelativeDateStr(12), // 12 days upcoming
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: null,
      groupName: null,
      createdAt: '2026-08-05T09:00:00Z',
      updatedAt: '2026-08-05T09:00:00Z',
    },
    {
      id: 'item_3',
      name: 'Residential Homeowners Insurance',
      lifecycleType: 'renewal',
      dueDate: getRelativeDateStr(24), // 24 days upcoming
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-08-10T11:00:00Z',
      updatedAt: '2026-08-10T11:00:00Z',
    },
    {
      id: 'item_4',
      name: 'State Driver License Renewal',
      lifecycleType: 'renewal',
      dueDate: getRelativeDateStr(-30),
      status: 'completed',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: null,
      groupName: null,
      createdAt: '2026-07-01T10:00:00Z',
      updatedAt: '2026-09-01T10:00:00Z',
    },

    // Maintenance
    {
      id: 'item_5',
      name: 'HVAC Air Filter & Coil Servicing',
      lifecycleType: 'maintenance',
      dueDate: getRelativeDateStr(-2), // 2 days overdue
      status: 'active',
      ownerId: 'user_sarah',
      ownerEmail: 'sarah@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-08-15T12:00:00Z',
      updatedAt: '2026-08-15T12:00:00Z',
    },
    {
      id: 'item_6',
      name: 'Honda CR-V Brake Inspection & Tire Rotation',
      lifecycleType: 'maintenance',
      dueDate: getRelativeDateStr(9), // 9 days upcoming
      status: 'active',
      ownerId: 'user_sarah',
      ownerEmail: 'sarah@example.com',
      groupId: 'group_vehicles',
      groupName: 'Shared Vehicle Maintenance',
      createdAt: '2026-08-20T14:30:00Z',
      updatedAt: '2026-08-20T14:30:00Z',
    },
    {
      id: 'item_7',
      name: 'Reverse Osmosis Filter Cartridge Replacement',
      lifecycleType: 'maintenance',
      dueDate: undefined, // Missing due date allowed per Decision 29
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-09-01T09:00:00Z',
      updatedAt: '2026-09-01T09:00:00Z',
    },
    {
      id: 'item_8',
      name: 'Annual Water Heater Flush',
      lifecycleType: 'maintenance',
      dueDate: getRelativeDateStr(-60),
      status: 'completed',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-06-01T08:00:00Z',
      updatedAt: '2026-07-15T08:00:00Z',
    },

    // Warranties
    {
      id: 'item_9',
      name: 'MacBook Pro AppleCare+ Protection',
      lifecycleType: 'warranty',
      dueDate: getRelativeDateStr(5), // 5 days upcoming
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: null,
      groupName: null,
      createdAt: '2026-08-25T15:00:00Z',
      updatedAt: '2026-08-25T15:00:00Z',
    },
    {
      id: 'item_10',
      name: 'Samsung 65" OLED TV 3-Year Limited Warranty',
      lifecycleType: 'warranty',
      dueDate: getRelativeDateStr(-10), // 10 days overdue
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-07-10T16:00:00Z',
      updatedAt: '2026-07-10T16:00:00Z',
    },
    {
      id: 'item_11',
      name: 'Bosch Dishwasher 5-Year Parts Warranty',
      lifecycleType: 'warranty',
      dueDate: getRelativeDateStr(120), // far future
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: 'group_home',
      groupName: 'Oakridge Family & Home',
      createdAt: '2026-08-01T11:00:00Z',
      updatedAt: '2026-08-01T11:00:00Z',
    },
    {
      id: 'item_12',
      name: 'Espresso Machine Manufacturer Warranty',
      lifecycleType: 'warranty',
      dueDate: undefined, // Missing date allowed
      status: 'active',
      ownerId: 'user_alex',
      ownerEmail: 'alex@example.com',
      groupId: null,
      groupName: null,
      createdAt: '2026-09-02T13:00:00Z',
      updatedAt: '2026-09-02T13:00:00Z',
    },
  ];
}

const DEFAULT_DIGEST_CONFIG: DailyDigestConfig = {
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York',
  deliveryTime: '08:00', // Option B from Question 34
  enabled: true, // Both reminder channels always enabled
};

export class MockLifecycleService implements ILifecycleService {
  private users: User[] = [];
  private currentUserId: string | null = null;
  private groups: Group[] = [];
  private items: LifecycleItem[] = [];
  private digestConfig: DailyDigestConfig = { ...DEFAULT_DIGEST_CONFIG };
  private digestHistory: DailyDigestEmail[] = [];

  constructor() {
    this.loadState();
  }

  private isStorageAvailable(): boolean {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
  }

  private loadState(): void {
    if (!this.isStorageAvailable()) {
      this.initDefaults();
      return;
    }

    try {
      const storedUsers = localStorage.getItem(STORAGE_KEYS.USERS);
      const storedUserId = localStorage.getItem(STORAGE_KEYS.CURRENT_USER_ID);
      const storedGroups = localStorage.getItem(STORAGE_KEYS.GROUPS);
      const storedItems = localStorage.getItem(STORAGE_KEYS.ITEMS);
      const storedConfig = localStorage.getItem(STORAGE_KEYS.DIGEST_CONFIG);
      const storedHistory = localStorage.getItem(STORAGE_KEYS.DIGEST_HISTORY);

      if (storedUsers) {
        this.users = JSON.parse(storedUsers);
        this.currentUserId = storedUserId || this.users[0]?.id || null;
        this.groups = storedGroups ? JSON.parse(storedGroups) : DEFAULT_GROUPS;
        this.items = storedItems ? JSON.parse(storedItems) : generateSeedItems();
        this.digestConfig = storedConfig ? JSON.parse(storedConfig) : DEFAULT_DIGEST_CONFIG;
        this.digestHistory = storedHistory ? JSON.parse(storedHistory) : [];
      } else {
        this.initDefaults();
      }
    } catch {
      this.initDefaults();
    }
  }

  private initDefaults(): void {
    this.users = [...DEFAULT_USERS];
    this.currentUserId = DEFAULT_USERS[0].id;
    this.groups = [...DEFAULT_GROUPS];
    this.items = generateSeedItems();
    this.digestConfig = { ...DEFAULT_DIGEST_CONFIG };
    this.digestHistory = [];
    this.saveState();
  }

  private saveState(): void {
    if (!this.isStorageAvailable()) return;
    try {
      localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(this.users));
      if (this.currentUserId) {
        localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, this.currentUserId);
      } else {
        localStorage.removeItem(STORAGE_KEYS.CURRENT_USER_ID);
      }
      localStorage.setItem(STORAGE_KEYS.GROUPS, JSON.stringify(this.groups));
      localStorage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(this.items));
      localStorage.setItem(STORAGE_KEYS.DIGEST_CONFIG, JSON.stringify(this.digestConfig));
      localStorage.setItem(STORAGE_KEYS.DIGEST_HISTORY, JSON.stringify(this.digestHistory));
    } catch {
      // Storage quota or error ignore
    }
  }

  public async resetToDefaultSeed(): Promise<void> {
    this.initDefaults();
  }

  // ------------------ AUTH & USER MANAGEMENT ------------------

  public async getCurrentUser(): Promise<User | null> {
    if (!this.currentUserId) return null;
    return this.users.find((u) => u.id === this.currentUserId) || null;
  }

  public async login(email: string, _password?: string): Promise<User> {
    const trimmed = email.trim().toLowerCase();
    let user = this.users.find((u) => u.email.toLowerCase() === trimmed);
    if (!user) {
      // Automatically provision user for testing email & password sign in
      user = {
        id: `user_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        email: trimmed,
        name: trimmed.split('@')[0],
        createdAt: new Date().toISOString(),
      };
      this.users.push(user);
    }
    this.currentUserId = user.id;
    this.saveState();
    return user;
  }

  public async signup(email: string, _password?: string, name?: string): Promise<User> {
    const trimmed = email.trim().toLowerCase();
    const existing = this.users.find((u) => u.email.toLowerCase() === trimmed);
    if (existing) {
      this.currentUserId = existing.id;
      this.saveState();
      return existing;
    }

    const newUser: User = {
      id: `user_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      email: trimmed,
      name: name?.trim() || trimmed.split('@')[0],
      createdAt: new Date().toISOString(),
    };
    this.users.push(newUser);
    this.currentUserId = newUser.id;
    this.saveState();
    return newUser;
  }

  public async logout(): Promise<void> {
    this.currentUserId = null;
    this.saveState();
  }

  public async switchUser(userId: string): Promise<User> {
    const user = this.users.find((u) => u.id === userId);
    if (!user) {
      throw new Error('User not found');
    }
    this.currentUserId = user.id;
    this.saveState();
    return user;
  }

  public async listUsers(): Promise<User[]> {
    return [...this.users];
  }

  /**
   * Decision 23: "Account deletion removes everything associated with the account, including its group items."
   * - Deletes user
   * - Deletes user's personal items
   * - Deletes groups owned by user and all items in those groups (Decision 30)
   * - Removes user from any groups they belonged to as member
   * - If user owned items in other shared groups, per Decision 23 those are removed too
   */
  public async deleteAccount(userId: string): Promise<void> {
    const userToDelete = this.users.find((u) => u.id === userId);
    if (!userToDelete) return;

    // 1. Find groups owned by user
    const ownedGroupIds = this.groups.filter((g) => g.ownerId === userId).map((g) => g.id);

    // 2. Remove items belonging to user or owned groups
    this.items = this.items.filter(
      (item) => item.ownerId !== userId && (!item.groupId || !ownedGroupIds.includes(item.groupId))
    );

    // 3. Remove groups owned by user
    this.groups = this.groups.filter((g) => g.ownerId !== userId);

    // 4. Remove user email from any remaining groups
    this.groups = this.groups.map((g) => ({
      ...g,
      memberEmails: g.memberEmails.filter((em) => em.toLowerCase() !== userToDelete.email.toLowerCase()),
    }));

    // 5. Remove user
    this.users = this.users.filter((u) => u.id !== userId);

    // 6. If currently logged in as this user, reset or switch
    if (this.currentUserId === userId) {
      this.currentUserId = this.users[0]?.id || null;
    }

    this.saveState();
  }

  // ------------------ ITEMS MANAGEMENT ------------------

  private async requireCurrentUser(): Promise<User> {
    const user = await this.getCurrentUser();
    if (!user) {
      throw new Error('Authentication required');
    }
    return user;
  }

  /**
   * Returns items accessible to current user:
   * 1. Personal items owned by user (groupId === null)
   * 2. Shared group items for groups where user is a member
   */
  public async getItems(options?: {
    groupId?: string | null;
    type?: LifecycleType;
    searchQuery?: string;
  }): Promise<LifecycleItem[]> {
    const currentUser = await this.requireCurrentUser();

    // Find groups the user belongs to
    const userGroupIds = this.groups
      .filter((g) => g.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase()))
      .map((g) => g.id);

    let accessible = this.items.filter((item) => {
      // Personal items owned by user
      if (!item.groupId) {
        return item.ownerId === currentUser.id;
      }
      // Group items accessible if member of that group
      return userGroupIds.includes(item.groupId);
    });

    if (options?.groupId !== undefined) {
      if (options.groupId === null) {
        accessible = accessible.filter((item) => !item.groupId);
      } else {
        accessible = accessible.filter((item) => item.groupId === options.groupId);
      }
    }

    if (options?.type) {
      accessible = accessible.filter((item) => item.lifecycleType === options.type);
    }

    if (options?.searchQuery && options.searchQuery.trim() !== '') {
      const q = options.searchQuery.toLowerCase().trim();
      accessible = accessible.filter(
        (item) => item.name.toLowerCase().includes(q) || (item.groupName && item.groupName.toLowerCase().includes(q))
      );
    }

    // Sort order:
    // Overdue first, then upcoming (by due date ascending), then undated, then completed
    const todayStr = getTodayDateString();
    return accessible.sort((a, b) => {
      const urgencyA = getItemUrgency(a, todayStr);
      const urgencyB = getItemUrgency(b, todayStr);

      const rank = (urgency: string) => {
        if (urgency === 'overdue') return 1;
        if (urgency === 'upcoming') return 2;
        if (urgency === 'normal') return 3;
        if (urgency === 'no_date') return 4;
        return 5; // completed
      };

      const diff = rank(urgencyA) - rank(urgencyB);
      if (diff !== 0) return diff;

      if (a.dueDate && b.dueDate) {
        return a.dueDate.localeCompare(b.dueDate);
      }
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
  }

  public async getItem(id: string): Promise<LifecycleItem> {
    const items = await this.getItems();
    const item = items.find((i) => i.id === id);
    if (!item) {
      throw new Error(`Item ${id} not found or not accessible`);
    }
    return item;
  }

  public async createItem(data: CreateItemDTO): Promise<LifecycleItem> {
    const currentUser = await this.requireCurrentUser();

    let groupName: string | null = null;
    if (data.groupId) {
      const group = this.groups.find((g) => g.id === data.groupId);
      if (!group) throw new Error('Target group not found');
      // Ensure current user is a member
      if (!group.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase())) {
        throw new Error('Not authorized to add items to this group');
      }
      groupName = group.name;
    }

    const newItem: LifecycleItem = {
      id: `item_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      name: data.name.trim(),
      lifecycleType: data.lifecycleType,
      dueDate: data.dueDate ? data.dueDate.trim().slice(0, 10) : undefined,
      status: data.status || 'active',
      ownerId: currentUser.id,
      ownerEmail: currentUser.email,
      groupId: data.groupId || null,
      groupName,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.items.unshift(newItem);
    this.saveState();
    return newItem;
  }

  public async updateItem(id: string, data: UpdateItemDTO): Promise<LifecycleItem> {
    const currentUser = await this.requireCurrentUser();
    const itemIdx = this.items.findIndex((i) => i.id === id);
    if (itemIdx === -1) throw new Error('Item not found');

    const item = this.items[itemIdx];

    // Check permissions:
    // If personal: must be owner.
    // If group item: any group member can edit (Decision 14).
    if (item.groupId) {
      const group = this.groups.find((g) => g.id === item.groupId);
      if (!group || !group.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase())) {
        throw new Error('Not authorized to edit this shared item');
      }
    } else if (item.ownerId !== currentUser.id) {
      throw new Error('Not authorized to edit this item');
    }

    let groupName = item.groupName;
    let groupId = item.groupId;

    if (data.groupId !== undefined) {
      if (data.groupId === null) {
        groupId = null;
        groupName = null;
      } else {
        const group = this.groups.find((g) => g.id === data.groupId);
        if (!group) throw new Error('Target group not found');
        groupId = group.id;
        groupName = group.name;
      }
    }

    const updated: LifecycleItem = {
      ...item,
      name: data.name !== undefined ? data.name.trim() : item.name,
      lifecycleType: data.lifecycleType !== undefined ? data.lifecycleType : item.lifecycleType,
      dueDate:
        data.dueDate !== undefined ? (data.dueDate ? data.dueDate.trim().slice(0, 10) : undefined) : item.dueDate,
      status: data.status !== undefined ? data.status : item.status,
      groupId,
      groupName,
      updatedAt: new Date().toISOString(),
    };

    this.items[itemIdx] = updated;
    this.saveState();
    return updated;
  }

  /**
   * Decision 8 & 28:
   * Mark complete and retain in main list.
   * Can toggle between 'active' and 'completed'.
   */
  public async toggleItemCompletion(id: string): Promise<LifecycleItem> {
    const item = await this.getItem(id);
    const newStatus = item.status === 'completed' ? 'active' : 'completed';
    return this.updateItem(id, { status: newStatus });
  }

  /**
   * Decision 19: Permanent deletion
   */
  public async deleteItem(id: string): Promise<void> {
    const currentUser = await this.requireCurrentUser();
    const item = this.items.find((i) => i.id === id);
    if (!item) return;

    if (item.groupId) {
      const group = this.groups.find((g) => g.id === item.groupId);
      if (!group || !group.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase())) {
        throw new Error('Not authorized to delete this shared item');
      }
    } else if (item.ownerId !== currentUser.id) {
      throw new Error('Not authorized to delete this item');
    }

    this.items = this.items.filter((i) => i.id !== id);
    this.saveState();
  }

  // ------------------ GROUPS & SHARING ------------------

  public async getGroups(): Promise<Group[]> {
    const currentUser = await this.requireCurrentUser();
    return this.groups.filter((g) =>
      g.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase())
    );
  }

  public async getGroup(id: string): Promise<Group> {
    const groups = await this.getGroups();
    const group = groups.find((g) => g.id === id);
    if (!group) throw new Error('Group not found');
    return group;
  }

  public async createGroup(name: string): Promise<Group> {
    const currentUser = await this.requireCurrentUser();
    const newGroup: Group = {
      id: `group_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      name: name.trim(),
      ownerId: currentUser.id,
      ownerEmail: currentUser.email,
      memberEmails: [currentUser.email],
      createdAt: new Date().toISOString(),
    };
    this.groups.push(newGroup);
    this.saveState();
    return newGroup;
  }

  public async inviteMember(groupId: string, memberEmail: string): Promise<Group> {
    const currentUser = await this.requireCurrentUser();
    const group = this.groups.find((g) => g.id === groupId);
    if (!group) throw new Error('Group not found');

    // Any member or owner can invite
    if (!group.memberEmails.map((e) => e.toLowerCase()).includes(currentUser.email.toLowerCase())) {
      throw new Error('Not authorized to invite to this group');
    }

    const cleanEmail = memberEmail.trim().toLowerCase();
    if (!group.memberEmails.map((e) => e.toLowerCase()).includes(cleanEmail)) {
      group.memberEmails.push(cleanEmail);
      this.saveState();
    }
    return group;
  }

  public async removeMember(groupId: string, memberEmail: string): Promise<Group> {
    const currentUser = await this.requireCurrentUser();
    const group = this.groups.find((g) => g.id === groupId);
    if (!group) throw new Error('Group not found');

    if (group.ownerId !== currentUser.id) {
      throw new Error('Only the group owner can remove members');
    }

    const cleanEmail = memberEmail.trim().toLowerCase();
    // Cannot remove owner
    if (cleanEmail === group.ownerEmail.toLowerCase()) {
      throw new Error('Cannot remove the group owner');
    }

    group.memberEmails = group.memberEmails.filter((e) => e.toLowerCase() !== cleanEmail);
    // Decision 18: Shared group items remain with the group when a member departs!
    this.saveState();
    return group;
  }

  public async leaveGroup(groupId: string): Promise<void> {
    const currentUser = await this.requireCurrentUser();
    const group = this.groups.find((g) => g.id === groupId);
    if (!group) return;

    if (group.ownerId === currentUser.id) {
      throw new Error('Group owner cannot leave the group. Delete the group or transfer ownership.');
    }

    group.memberEmails = group.memberEmails.filter((e) => e.toLowerCase() !== currentUser.email.toLowerCase());
    // Decision 18: Shared group items remain with the group
    this.saveState();
  }

  /**
   * Decision 30: "Deleting a group deletes the group and all its shared items."
   */
  public async deleteGroup(groupId: string): Promise<void> {
    const currentUser = await this.requireCurrentUser();
    const group = this.groups.find((g) => g.id === groupId);
    if (!group) return;

    if (group.ownerId !== currentUser.id) {
      throw new Error('Only group owner can delete the group');
    }

    // 1. Delete all items in this group
    this.items = this.items.filter((item) => item.groupId !== groupId);

    // 2. Delete the group
    this.groups = this.groups.filter((g) => g.id !== groupId);

    this.saveState();
  }

  // ------------------ REMINDERS & DAILY DIGEST ------------------

  public async getRemindersSummary(): Promise<RemindersSummary> {
    const items = await this.getItems();
    const todayStr = getTodayDateString();

    const overdue: LifecycleItem[] = [];
    const upcoming: LifecycleItem[] = [];

    for (const item of items) {
      const urgency = getItemUrgency(item, todayStr);
      if (urgency === 'overdue') {
        overdue.push(item);
      } else if (urgency === 'upcoming') {
        upcoming.push(item);
      }
    }

    return {
      overdue,
      upcoming,
      totalActiveReminders: overdue.length + upcoming.length,
    };
  }

  public async getDigestConfig(): Promise<DailyDigestConfig> {
    return { ...this.digestConfig };
  }

  public async updateDigestConfig(config: Partial<DailyDigestConfig>): Promise<DailyDigestConfig> {
    this.digestConfig = {
      ...this.digestConfig,
      ...config,
      enabled: true, // both reminder channels are always enabled per Decision 22
    };
    this.saveState();
    return { ...this.digestConfig };
  }

  public async generateAndSendDailyDigest(recipientEmail?: string): Promise<DailyDigestEmail> {
    const currentUser = await this.requireCurrentUser();
    const targetEmail = recipientEmail || currentUser.email;
    const reminders = await this.getRemindersSummary();

    const email = buildDailyDigestEmail({
      recipientEmail: targetEmail,
      recipientName: currentUser.name,
      config: this.digestConfig,
      overdueItems: reminders.overdue,
      upcomingItems: reminders.upcoming,
    });

    this.digestHistory.unshift(email);
    // keep up to 20 past digests
    if (this.digestHistory.length > 20) {
      this.digestHistory = this.digestHistory.slice(0, 20);
    }
    this.saveState();

    return email;
  }

  public async getDigestHistory(): Promise<DailyDigestEmail[]> {
    return [...this.digestHistory];
  }
}
