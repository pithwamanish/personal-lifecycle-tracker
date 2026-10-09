import { ItemUrgency, LifecycleItem } from './types';

/**
 * Returns the current date in YYYY-MM-DD format based on standard ISO.
 */
export function getTodayDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Determines urgency classification for a lifecycle item.
 * - Completed items are always 'completed'.
 * - Items without due dates are 'no_date' (cannot be classified as upcoming or overdue).
 * - Items with dueDate < today are 'overdue'.
 * - Items with dueDate between today and today + upcomingWindowDays are 'upcoming'.
 * - Otherwise 'normal'.
 */
export function getItemUrgency(
  item: Pick<LifecycleItem, 'status' | 'dueDate'>,
  todayStr: string = getTodayDateString(),
  upcomingWindowDays: number = 30
): ItemUrgency {
  if (item.status === 'completed') {
    return 'completed';
  }

  if (!item.dueDate || item.dueDate.trim() === '') {
    return 'no_date';
  }

  const cleanDueDate = item.dueDate.trim().slice(0, 10);
  const cleanToday = todayStr.trim().slice(0, 10);

  if (cleanDueDate < cleanToday) {
    return 'overdue';
  }

  // Calculate day difference
  const due = new Date(`${cleanDueDate}T00:00:00Z`).getTime();
  const today = new Date(`${cleanToday}T00:00:00Z`).getTime();
  const diffDays = Math.round((due - today) / (1000 * 60 * 60 * 24));

  if (diffDays >= 0 && diffDays <= upcomingWindowDays) {
    return 'upcoming';
  }

  return 'normal';
}

/**
 * Computes difference in days from today to dueDate.
 * Negative means overdue.
 */
export function getDaysDifference(dueDate?: string, todayStr: string = getTodayDateString()): number | null {
  if (!dueDate || dueDate.trim() === '') return null;
  const cleanDueDate = dueDate.trim().slice(0, 10);
  const cleanToday = todayStr.trim().slice(0, 10);

  const due = new Date(`${cleanDueDate}T00:00:00Z`).getTime();
  const today = new Date(`${cleanToday}T00:00:00Z`).getTime();
  return Math.round((due - today) / (1000 * 60 * 60 * 24));
}

/**
 * Human readable formatting for date string.
 */
export function formatDisplayDate(dateStr?: string): string {
  if (!dateStr || dateStr.trim() === '') return 'No due date';
  const clean = dateStr.trim().slice(0, 10);
  const [year, month, day] = clean.split('-').map(Number);
  if (!year || !month || !day) return dateStr;

  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Human-readable relative description for due dates.
 */
export function getRelativeDueDateLabel(
  dueDate?: string,
  status?: string,
  todayStr: string = getTodayDateString()
): string {
  if (status === 'completed') return 'Completed';
  if (!dueDate || dueDate.trim() === '') return 'No due date';

  const diff = getDaysDifference(dueDate, todayStr);
  if (diff === null) return 'No due date';

  if (diff < 0) {
    const abs = Math.abs(diff);
    return abs === 1 ? '1 day overdue' : `${abs} days overdue`;
  }
  if (diff === 0) {
    return 'Due today';
  }
  if (diff === 1) {
    return 'Due tomorrow';
  }
  return `Due in ${diff} days`;
}
