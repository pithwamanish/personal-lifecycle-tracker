import { describe, expect, it } from 'vitest';
import {
  formatDisplayDate,
  getDaysDifference,
  getItemUrgency,
  getRelativeDueDateLabel,
} from '../dateUtils';

describe('dateUtils', () => {
  const today = '2026-10-09';

  describe('getItemUrgency', () => {
    it('returns completed if item status is completed regardless of due date', () => {
      const urgency = getItemUrgency({ status: 'completed', dueDate: '2026-01-01' }, today);
      expect(urgency).toBe('completed');
    });

    it('returns no_date if dueDate is undefined or blank (Decision 29: Missing due dates allowed)', () => {
      expect(getItemUrgency({ status: 'active', dueDate: undefined }, today)).toBe('no_date');
      expect(getItemUrgency({ status: 'active', dueDate: '' }, today)).toBe('no_date');
      expect(getItemUrgency({ status: 'active', dueDate: '   ' }, today)).toBe('no_date');
    });

    it('returns overdue if dueDate is strictly prior to today', () => {
      const urgency = getItemUrgency({ status: 'active', dueDate: '2026-10-05' }, today);
      expect(urgency).toBe('overdue');
    });

    it('returns upcoming if dueDate is today or within the 30-day window', () => {
      expect(getItemUrgency({ status: 'active', dueDate: '2026-10-09' }, today)).toBe('upcoming');
      expect(getItemUrgency({ status: 'active', dueDate: '2026-10-15' }, today)).toBe('upcoming');
      expect(getItemUrgency({ status: 'active', dueDate: '2026-11-05' }, today)).toBe('upcoming');
    });

    it('returns normal if dueDate is beyond the 30-day upcoming window', () => {
      const urgency = getItemUrgency({ status: 'active', dueDate: '2026-12-01' }, today);
      expect(urgency).toBe('normal');
    });
  });

  describe('getDaysDifference', () => {
    it('computes positive days difference for upcoming dates', () => {
      expect(getDaysDifference('2026-10-14', today)).toBe(5);
    });

    it('computes negative days difference for overdue dates', () => {
      expect(getDaysDifference('2026-10-06', today)).toBe(-3);
    });

    it('returns 0 for today', () => {
      expect(getDaysDifference('2026-10-09', today)).toBe(0);
    });

    it('returns null for missing date', () => {
      expect(getDaysDifference(undefined, today)).toBeNull();
    });
  });

  describe('formatDisplayDate and relative labels', () => {
    it('formats display dates nicely', () => {
      expect(formatDisplayDate('2026-10-09')).toBe('Oct 9, 2026');
      expect(formatDisplayDate(undefined)).toBe('No due date');
    });

    it('returns human relative labels for overdue, today, and upcoming', () => {
      expect(getRelativeDueDateLabel('2026-10-05', 'active', today)).toBe('4 days overdue');
      expect(getRelativeDueDateLabel('2026-10-08', 'active', today)).toBe('1 day overdue');
      expect(getRelativeDueDateLabel('2026-10-09', 'active', today)).toBe('Due today');
      expect(getRelativeDueDateLabel('2026-10-10', 'active', today)).toBe('Due tomorrow');
      expect(getRelativeDueDateLabel('2026-10-15', 'active', today)).toBe('Due in 6 days');
      expect(getRelativeDueDateLabel('2026-10-15', 'completed', today)).toBe('Completed');
    });
  });
});
