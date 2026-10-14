import { ILifecycleService } from './api';
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
  TOKEN: 'plt_auth_token_v1',
  CURRENT_USER_ID: 'plt_current_user_id_v1',
  USER_TOKENS: 'plt_user_tokens_v1',
  EXPLICIT_LOGOUT: 'plt_logged_out_v1',
};

const DEFAULT_SEED_PASSWORD = 'password123';

export class BackendLifecycleService implements ILifecycleService {
  private baseUrl: string;
  private token: string | null = null;
  private currentUserId: string | null = null;
  private userTokens: Record<string, string> = {};
  private explicitlyLoggedOut: boolean = false;

  constructor(baseUrl?: string) {
    if (baseUrl !== undefined) {
      this.baseUrl = baseUrl.replace(/\/$/, '');
    } else {
      const envUrl =
        typeof import.meta !== 'undefined' && import.meta.env
          ? import.meta.env.VITE_API_URL
          : '';
      let resolvedBase = envUrl || '';
      if (!resolvedBase && typeof window !== 'undefined' && window.location) {
        const host = window.location.hostname;
        if (host.includes('cloudfront.net')) {
          resolvedBase = 'https://7ksomsylvke2uawuhhccbfr6hy0agzyb.lambda-url.ap-south-1.on.aws';
        }
      }
      this.baseUrl = resolvedBase.replace(/\/$/, '');
    }
    this.loadState();
  }

  private isStorageAvailable(): boolean {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
  }

  private loadState(): void {
    if (!this.isStorageAvailable()) return;

    try {
      this.token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      this.currentUserId = localStorage.getItem(STORAGE_KEYS.CURRENT_USER_ID);
      this.explicitlyLoggedOut = localStorage.getItem(STORAGE_KEYS.EXPLICIT_LOGOUT) === 'true';

      const storedUserTokens = localStorage.getItem(STORAGE_KEYS.USER_TOKENS);
      if (storedUserTokens) {
        this.userTokens = JSON.parse(storedUserTokens);
      }
    } catch {
      // Storage access or parse error fallback
    }
  }

  private saveState(): void {
    if (!this.isStorageAvailable()) return;

    try {
      if (this.token) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, this.token);
      } else {
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
      }

      if (this.currentUserId) {
        localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, this.currentUserId);
      } else {
        localStorage.removeItem(STORAGE_KEYS.CURRENT_USER_ID);
      }

      if (this.explicitlyLoggedOut) {
        localStorage.setItem(STORAGE_KEYS.EXPLICIT_LOGOUT, 'true');
      } else {
        localStorage.removeItem(STORAGE_KEYS.EXPLICIT_LOGOUT);
      }

      localStorage.setItem(STORAGE_KEYS.USER_TOKENS, JSON.stringify(this.userTokens));
    } catch {
      // Ignore quota errors
    }
  }

  private setSession(user: User, token: string): void {
    this.token = token;
    this.currentUserId = user.id;
    this.userTokens[user.id] = token;
    this.explicitlyLoggedOut = false;
    this.saveState();
  }

  private clearSession(): void {
    this.token = null;
    this.currentUserId = null;
    this.explicitlyLoggedOut = true;
    this.saveState();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = new Headers(options.headers || {});

    if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
      headers.set('Content-Type', 'application/json');
    }

    if (this.token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson?.error) {
          errorMessage = errorJson.error;
        } else if (errorJson?.detail) {
          errorMessage =
            typeof errorJson.detail === 'string'
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Response might not be JSON
      }
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return undefined as unknown as T;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    }

    return undefined as unknown as T;
  }

  // ------------------ AUTH & USER MANAGEMENT ------------------

  public async getCurrentUser(): Promise<User | null> {
    if (this.token) {
      try {
        const user = await this.request<User>('/api/v1/auth/me', { method: 'GET' });
        this.currentUserId = user.id;
        this.saveState();
        return user;
      } catch {
        // Token expired or invalid
        this.token = null;
        this.currentUserId = null;
        this.saveState();
      }
    }

    // If user explicitly logged out, do not auto-login
    if (this.explicitlyLoggedOut) {
      return null;
    }

    // Default seamless initial user experience: login default seed user Alex Taylor
    try {
      const user = await this.login('alex@example.com', DEFAULT_SEED_PASSWORD);
      return user;
    } catch {
      return null;
    }
  }

  public async login(email: string, password?: string): Promise<User> {
    const trimmedEmail = email.trim().toLowerCase();
    const payload = {
      email: trimmedEmail,
      password: password || DEFAULT_SEED_PASSWORD,
    };

    const res = await this.request<{ user: User; token: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    this.setSession(res.user, res.token);
    return res.user;
  }

  public async signup(email: string, password?: string, name?: string): Promise<User> {
    const trimmedEmail = email.trim().toLowerCase();
    const payload = {
      email: trimmedEmail,
      password: password || DEFAULT_SEED_PASSWORD,
      name: name?.trim() || trimmedEmail.split('@')[0],
    };

    const res = await this.request<{ user: User; token: string }>('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    this.setSession(res.user, res.token);
    return res.user;
  }

  public async logout(): Promise<void> {
    try {
      await this.request<{ message: string }>('/api/v1/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors during logout
    }
    this.clearSession();
  }

  public async switchUser(userId: string): Promise<User> {
    // 1. Check if we already have a cached token for this user
    const cachedToken = this.userTokens[userId];
    if (cachedToken) {
      this.token = cachedToken;
      try {
        const user = await this.request<User>('/api/v1/auth/me', { method: 'GET' });
        this.setSession(user, cachedToken);
        return user;
      } catch {
        // Cached token invalid/expired, proceed to re-login
      }
    }

    // 2. Fetch available users to find target user email
    const users = await this.listUsers();
    const targetUser = users.find((u) => u.id === userId);
    if (!targetUser) {
      throw new Error('User not found');
    }

    // 3. Log in with seed password
    const user = await this.login(targetUser.email, DEFAULT_SEED_PASSWORD);
    return user;
  }

  public async listUsers(): Promise<User[]> {
    return this.request<User[]>('/api/v1/users', { method: 'GET' });
  }

  public async deleteAccount(userId: string): Promise<void> {
    await this.request<void>(`/api/v1/users/${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    });

    delete this.userTokens[userId];
    if (this.currentUserId === userId) {
      this.clearSession();
    } else {
      this.saveState();
    }
  }

  // ------------------ LIFECYCLE ITEMS MANAGEMENT ------------------

  public async getItems(options?: {
    groupId?: string | null;
    type?: LifecycleType;
    searchQuery?: string;
  }): Promise<LifecycleItem[]> {
    const params = new URLSearchParams();
    if (options?.groupId !== undefined) {
      params.set('groupId', options.groupId === null ? 'null' : options.groupId);
    }
    if (options?.type) {
      params.set('type', options.type);
    }
    if (options?.searchQuery) {
      params.set('searchQuery', options.searchQuery);
    }

    const query = params.toString();
    const endpoint = `/api/v1/items${query ? `?${query}` : ''}`;
    return this.request<LifecycleItem[]>(endpoint, { method: 'GET' });
  }

  public async getItem(id: string): Promise<LifecycleItem> {
    return this.request<LifecycleItem>(`/api/v1/items/${encodeURIComponent(id)}`, {
      method: 'GET',
    });
  }

  public async createItem(data: CreateItemDTO): Promise<LifecycleItem> {
    return this.request<LifecycleItem>('/api/v1/items', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public async updateItem(id: string, data: UpdateItemDTO): Promise<LifecycleItem> {
    return this.request<LifecycleItem>(`/api/v1/items/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  public async toggleItemCompletion(id: string): Promise<LifecycleItem> {
    return this.request<LifecycleItem>(`/api/v1/items/${encodeURIComponent(id)}/complete`, {
      method: 'POST',
    });
  }

  public async deleteItem(id: string): Promise<void> {
    await this.request<void>(`/api/v1/items/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
  }

  // ------------------ GROUPS & SHARING ------------------

  public async getGroups(): Promise<Group[]> {
    return this.request<Group[]>('/api/v1/groups', { method: 'GET' });
  }

  public async getGroup(id: string): Promise<Group> {
    return this.request<Group>(`/api/v1/groups/${encodeURIComponent(id)}`, {
      method: 'GET',
    });
  }

  public async createGroup(name: string): Promise<Group> {
    return this.request<Group>('/api/v1/groups', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  public async inviteMember(groupId: string, memberEmail: string): Promise<Group> {
    return this.request<Group>(`/api/v1/groups/${encodeURIComponent(groupId)}/members`, {
      method: 'POST',
      body: JSON.stringify({ email: memberEmail }),
    });
  }

  public async removeMember(groupId: string, memberEmail: string): Promise<Group> {
    return this.request<Group>(
      `/api/v1/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(memberEmail)}`,
      {
        method: 'DELETE',
      }
    );
  }

  public async leaveGroup(groupId: string): Promise<void> {
    await this.request<{ message: string }>(
      `/api/v1/groups/${encodeURIComponent(groupId)}/leave`,
      {
        method: 'POST',
      }
    );
  }

  public async deleteGroup(groupId: string): Promise<void> {
    await this.request<void>(`/api/v1/groups/${encodeURIComponent(groupId)}`, {
      method: 'DELETE',
    });
  }

  // ------------------ REMINDERS & EMAIL DIGEST ------------------

  public async getRemindersSummary(): Promise<RemindersSummary> {
    return this.request<RemindersSummary>('/api/v1/reminders/summary', {
      method: 'GET',
    });
  }

  public async getDigestConfig(): Promise<DailyDigestConfig> {
    return this.request<DailyDigestConfig>('/api/v1/reminders/digest/config', {
      method: 'GET',
    });
  }

  public async updateDigestConfig(
    config: Partial<DailyDigestConfig>
  ): Promise<DailyDigestConfig> {
    return this.request<DailyDigestConfig>('/api/v1/reminders/digest/config', {
      method: 'PATCH',
      body: JSON.stringify(config),
    });
  }

  public async generateAndSendDailyDigest(
    recipientEmail?: string
  ): Promise<DailyDigestEmail> {
    return this.request<DailyDigestEmail>('/api/v1/reminders/digest/generate', {
      method: 'POST',
      body: JSON.stringify(recipientEmail ? { recipientEmail } : {}),
    });
  }

  public async getDigestHistory(): Promise<DailyDigestEmail[]> {
    return this.request<DailyDigestEmail[]>('/api/v1/reminders/digest/history', {
      method: 'GET',
    });
  }

  // ------------------ DEVELOPMENT & SEEDING ------------------

  public async resetToDefaultSeed(): Promise<void> {
    await this.request<{ message: string }>('/api/v1/dev/seed', {
      method: 'POST',
    });
  }
}
