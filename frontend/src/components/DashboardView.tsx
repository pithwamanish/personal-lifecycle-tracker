import React from 'react';
import { AlertCircle, CheckCircle2, Clock, Filter, Layers, Plus } from 'lucide-react';
import { getItemUrgency, getTodayDateString } from '../services/dateUtils';
import { Group, LifecycleItem } from '../services/types';
import { ItemRow } from './ItemRow';

interface DashboardViewProps {
  items: LifecycleItem[];
  groups: Group[];
  selectedGroupId: string | null | 'ALL';
  onSelectGroup: (groupId: string | null | 'ALL') => void;
  onToggleComplete: (id: string) => void;
  onEdit: (item: LifecycleItem) => void;
  onDelete: (id: string) => void;
  onOpenCreate: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  items,
  groups,
  selectedGroupId,
  onSelectGroup,
  onToggleComplete,
  onEdit,
  onDelete,
  onOpenCreate,
}) => {
  const todayStr = getTodayDateString();

  // Categorize items
  const overdueItems: LifecycleItem[] = [];
  const upcomingItems: LifecycleItem[] = [];
  const otherActiveItems: LifecycleItem[] = [];
  const completedItems: LifecycleItem[] = [];

  for (const item of items) {
    if (item.status === 'completed') {
      completedItems.push(item);
      continue;
    }

    const urgency = getItemUrgency(item, todayStr);
    if (urgency === 'overdue') {
      overdueItems.push(item);
    } else if (urgency === 'upcoming') {
      upcomingItems.push(item);
    } else {
      otherActiveItems.push(item);
    }
  }

  const totalActive = overdueItems.length + upcomingItems.length + otherActiveItems.length;

  return (
    <div className="space-y-8">
      {/* Scope Toolbar & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Priority Action Dashboard</h1>
          <p className="text-xs text-slate-500 mt-1">
            Focusing on upcoming renewals, scheduled maintenance, and expiring warranties.
          </p>
        </div>

        {/* Scope Selector: All | Personal | Groups */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Scope:</span>
          <select
            value={selectedGroupId === 'ALL' ? 'ALL' : selectedGroupId === null ? 'PERSONAL' : selectedGroupId}
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'ALL') onSelectGroup('ALL');
              else if (val === 'PERSONAL') onSelectGroup(null);
              else onSelectGroup(val);
            }}
            className="text-xs bg-white border border-slate-300 rounded-md px-2.5 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-900"
          >
            <option value="ALL">All Accessible Items</option>
            <option value="PERSONAL">Personal Only</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                Group: {g.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Metric Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500">
            <span>Overdue Actions</span>
            <AlertCircle className="w-4 h-4 text-red-600" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono tabular-nums text-red-600">
            {overdueItems.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Remain until completed</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500">
            <span>Upcoming (30 Days)</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono tabular-nums text-amber-700">
            {upcomingItems.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Included in daily digest</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500">
            <span>Total Active</span>
            <Layers className="w-4 h-4 text-slate-600" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono tabular-nums text-slate-900">
            {totalActive}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Across all lifecycle types</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500">
            <span>Completed Records</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono tabular-nums text-emerald-700">
            {completedItems.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Retained in list</div>
        </div>
      </div>

      {/* Priority Section 1: Overdue Items */}
      <section className="bg-white rounded-xl border border-red-200 overflow-hidden shadow-2xs">
        <div className="px-6 py-4 bg-red-50/60 border-b border-red-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-red-900">
              Overdue Items ({overdueItems.length})
            </h2>
          </div>
          <span className="text-xs text-red-700 font-medium">Immediate attention required</span>
        </div>

        {overdueItems.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
            <p className="font-semibold text-slate-800">No overdue lifecycle items!</p>
            <p className="mt-0.5">All renewals, maintenance, and warranties are on track.</p>
          </div>
        ) : (
          <div>
            {overdueItems.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                onToggleComplete={onToggleComplete}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </section>

      {/* Priority Section 2: Upcoming Actions */}
      <section className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="px-6 py-4 bg-amber-50/40 border-b border-amber-200/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Clock className="w-4 h-4 text-amber-700" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-amber-900">
              Upcoming Actions — Next 30 Days ({upcomingItems.length})
            </h2>
          </div>
          <span className="text-xs text-amber-800 font-medium">Scheduled for reminders</span>
        </div>

        {upcomingItems.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <p className="font-semibold text-slate-800">No upcoming items due in the next 30 days.</p>
            <p className="mt-0.5">Use "Track Item" to schedule your next renewal, service, or warranty.</p>
          </div>
        ) : (
          <div>
            {upcomingItems.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                onToggleComplete={onToggleComplete}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </section>

      {/* Section 3: All Active & Undated Records */}
      {otherActiveItems.length > 0 && (
        <section className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Layers className="w-4 h-4 text-slate-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Scheduled & Undated Active Items ({otherActiveItems.length})
              </h2>
            </div>
            <span className="text-xs text-slate-500">Dates beyond 30 days or undated</span>
          </div>

          <div>
            {otherActiveItems.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                onToggleComplete={onToggleComplete}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        </section>
      )}

      {/* Section 4: Completed Records (Retained in main list per Decision 8 & 28) */}
      <section className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="px-6 py-4 bg-slate-50/60 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Completed Records ({completedItems.length})
            </h2>
          </div>
          <span className="text-xs text-slate-500">Retained visible in main list</span>
        </div>

        {completedItems.length === 0 ? (
          <div className="p-6 text-center text-slate-400 text-xs">
            No completed items yet. Complete items using the checkmark.
          </div>
        ) : (
          <div>
            {completedItems.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                onToggleComplete={onToggleComplete}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </section>

      {/* Quick Action Footer if zero items */}
      {items.length === 0 && (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900">No lifecycle items tracked yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Get started by tracking your first renewal, maintenance item, or product warranty.
          </p>
          <button
            onClick={onOpenCreate}
            className="mt-4 px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg inline-flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Track First Item</span>
          </button>
        </div>
      )}
    </div>
  );
};
