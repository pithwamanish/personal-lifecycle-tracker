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

export interface ILifecycleService {
  // Auth & User Management
  getCurrentUser(): Promise<User | null>;
  login(email: string, password?: string): Promise<User>;
  signup(email: string, password?: string, name?: string): Promise<User>;
  logout(): Promise<void>;
  switchUser(userId: string): Promise<User>;
  listUsers(): Promise<User[]>;
  deleteAccount(userId: string): Promise<void>;

  // Lifecycle Items Management
  getItems(options?: {
    groupId?: string | null;
    type?: LifecycleType;
    searchQuery?: string;
  }): Promise<LifecycleItem[]>;
  getItem(id: string): Promise<LifecycleItem>;
  createItem(data: CreateItemDTO): Promise<LifecycleItem>;
  updateItem(id: string, data: UpdateItemDTO): Promise<LifecycleItem>;
  toggleItemCompletion(id: string): Promise<LifecycleItem>;
  deleteItem(id: string): Promise<void>;

  // Groups & Sharing
  getGroups(): Promise<Group[]>;
  getGroup(id: string): Promise<Group>;
  createGroup(name: string): Promise<Group>;
  inviteMember(groupId: string, memberEmail: string): Promise<Group>;
  removeMember(groupId: string, memberEmail: string): Promise<Group>;
  leaveGroup(groupId: string): Promise<void>;
  deleteGroup(groupId: string): Promise<void>;

  // Reminders & Email Digest
  getRemindersSummary(): Promise<RemindersSummary>;
  getDigestConfig(): Promise<DailyDigestConfig>;
  updateDigestConfig(config: Partial<DailyDigestConfig>): Promise<DailyDigestConfig>;
  generateAndSendDailyDigest(recipientEmail?: string): Promise<DailyDigestEmail>;
  getDigestHistory(): Promise<DailyDigestEmail[]>;

  // Development & Seeding
  resetToDefaultSeed(): Promise<void>;
}
