import React from 'react';
import { AlertCircle, Bell, CheckCircle2, Clock, X } from 'lucide-react';
import { formatDisplayDate, getRelativeDueDateLabel, getTodayDateString } from '../services/dateUtils';
import { RemindersSummary } from '../services/types';

interface InAppRemindersDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  reminders: RemindersSummary;
  onToggleComplete: (id: string) => void;
}

export const InAppRemindersDrawer: React.FC<InAppRemindersDrawerProps> = ({
  isOpen,
  onClose,
  reminders,
  onToggleComplete,
}) => {
  if (!isOpen) return null;

  const todayStr = getTodayDateString();

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/30 backdrop-blur-xs">
      <div className="bg-white w-full max-w-md h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-slate-100 rounded-lg text-slate-800">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">In-App Reminders</h2>
              <p className="text-xs text-slate-500">
                {reminders.totalActiveReminders} active item{reminders.totalActiveReminders === 1 ? '' : 's'} need attention
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Overdue Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-red-700">
                <AlertCircle className="w-4 h-4" />
                <span>Overdue ({reminders.overdue.length})</span>
              </div>
              <span className="text-[11px] text-slate-500">Requires manual completion</span>
            </div>

            {reminders.overdue.length === 0 ? (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 text-center">
                No overdue lifecycle items.
              </div>
            ) : (
              <div className="space-y-2">
                {reminders.overdue.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-red-50/50 border border-red-200 rounded-lg flex items-start justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900 truncate">{item.name}</p>
                      <div className="flex items-center gap-1.5 text-[11px] text-red-700 mt-1">
                        <span className="capitalize">{item.lifecycleType}</span>
                        <span>·</span>
                        <span>{getRelativeDueDateLabel(item.dueDate, item.status, todayStr)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => onToggleComplete(item.id)}
                      className="px-2.5 py-1 text-xs font-medium bg-white text-slate-900 border border-slate-200 rounded hover:bg-slate-50 shrink-0 transition-colors"
                      title="Mark complete"
                    >
                      Complete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-700">
                <Clock className="w-4 h-4" />
                <span>Upcoming Within 30 Days ({reminders.upcoming.length})</span>
              </div>
            </div>

            {reminders.upcoming.length === 0 ? (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 text-center">
                No upcoming items scheduled in the next 30 days.
              </div>
            ) : (
              <div className="space-y-2">
                {reminders.upcoming.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-amber-50/30 border border-amber-200 rounded-lg flex items-start justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-900 truncate">{item.name}</p>
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-600 mt-1">
                        <span className="capitalize">{item.lifecycleType}</span>
                        <span>·</span>
                        <span className="text-amber-800 font-medium">
                          {formatDisplayDate(item.dueDate)} ({getRelativeDueDateLabel(item.dueDate, item.status, todayStr)})
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => onToggleComplete(item.id)}
                      className="p-1 text-slate-400 hover:text-emerald-700 transition-colors shrink-0"
                      title="Mark complete"
                      aria-label="Mark complete"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer info */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
          Reminders are fixed and synchronized with your scheduled daily email digest.
        </div>
      </div>
    </div>
  );
};
