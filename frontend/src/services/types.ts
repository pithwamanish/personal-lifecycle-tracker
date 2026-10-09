/**
 * Domain types for Personal Lifecycle Tracker
 * Adheres strictly to the Consolidated MVP Scope:
 * - Types: Renewals, Maintenance, Warranties
 * - Common fields only: Name, Lifecycle type, Due date (optional), Status
 * - No custom fields, no recurring schedules, no attachments, no assignment
 */

export type LifecycleType = 'renewal' | 'maintenance' | 'warranty';

export type ItemStatus = 'active' | 'completed';

export type ItemUrgency = 'overdue' | 'upcoming' | 'normal' | 'no_date' | 'completed';

export interface LifecycleItem {
  id: string;
  name: string;
  lifecycleType: LifecycleType;
  dueDate?: string; // ISO Date YYYY-MM-DD, optional manual entry
  status: ItemStatus;
  ownerId: string;
  ownerEmail: string;
  groupId?: string | null; // null if personal item
  groupName?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateItemDTO {
  name: string;
  lifecycleType: LifecycleType;
  dueDate?: string;
  status?: ItemStatus;
  groupId?: string | null;
}

export interface UpdateItemDTO {
  name?: string;
  lifecycleType?: LifecycleType;
  dueDate?: string;
  status?: ItemStatus;
  groupId?: string | null;
}

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface Group {
  id: string;
  name: string;
  ownerId: string;
  ownerEmail: string;
  memberEmails: string[];
  createdAt: string;
}

export type DigestDeliveryTime = '06:00' | '08:00' | '09:00' | '12:00';

export interface DailyDigestConfig {
  timeZone: string;
  deliveryTime: DigestDeliveryTime;
  enabled: boolean;
}

export interface DailyDigestEmail {
  id: string;
  recipientEmail: string;
  recipientName: string;
  generatedAt: string;
  deliveryTime: DigestDeliveryTime;
  timeZone: string;
  subject: string;
  overdueCount: number;
  upcomingCount: number;
  overdueItems: LifecycleItem[];
  upcomingItems: LifecycleItem[];
  htmlContent: string;
  textContent: string;
}

export interface RemindersSummary {
  overdue: LifecycleItem[];
  upcoming: LifecycleItem[];
  totalActiveReminders: number;
}
