import React from 'react';
import { Clock, Filter, Plus, Shield, Wrench } from 'lucide-react';
import { Group, LifecycleItem, LifecycleType } from '../services/types';
import { ItemRow } from './ItemRow';

interface LifecycleListViewProps {
  type: LifecycleType;
  items: LifecycleItem[];
  groups: Group[];
  selectedGroupId: string | null | 'ALL';
  onSelectGroup: (groupId: string | null | 'ALL') => void;
  onToggleComplete: (id: string) => void;
  onEdit: (item: LifecycleItem) => void;
  onDelete: (id: string) => void;
  onOpenCreate: (type: LifecycleType) => void;
}

export const LifecycleListView: React.FC<LifecycleListViewProps> = ({
  type,
  items,
  groups,
  selectedGroupId,
  onSelectGroup,
  onToggleComplete,
  onEdit,
  onDelete,
  onOpenCreate,
}) => {
  const filtered = items.filter((item) => item.lifecycleType === type);
  const activeItems = filtered.filter((item) => item.status === 'active');
  const completedItems = filtered.filter((item) => item.status === 'completed');

  const configs: Record<
    LifecycleType,
    { title: string; subtitle: string; icon: React.ReactNode; placeholder: string }
  > = {
    renewal: {
      title: 'Renewals',
      subtitle: 'Track policies, legal documents, passports, licenses, and subscriptions before expiration.',
      icon: <Clock className="w-5 h-5 text-indigo-600" />,
      placeholder: 'insurance policy or passport',
    },
    maintenance: {
      title: 'Maintenance',
      subtitle: 'Schedule and verify periodic care for vehicles, home appliances, HVAC, and facilities.',
      icon: <Wrench className="w-5 h-5 text-amber-600" />,
      placeholder: 'vehicle oil change or HVAC filter',
    },
    warranty: {
      title: 'Warranties',
      subtitle: 'Monitor manufacturer and extended coverage terms for electronics, appliances, and assets.',
      icon: <Shield className="w-5 h-5 text-emerald-600" />,
      placeholder: 'product warranty or AppleCare',
    },
  };

  const currentConfig = configs[type];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-white border border-slate-200 rounded-xl shrink-0 mt-0.5">
            {currentConfig.icon}
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">{currentConfig.title}</h1>
            <p className="text-xs text-slate-500 mt-0.5">{currentConfig.subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          {/* Scope selector */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
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
              <option value="ALL">All Items</option>
              <option value="PERSONAL">Personal Only</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  Group: {g.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => onOpenCreate(type)}
            className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 shadow-xs shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Track {currentConfig.title.slice(0, -1)}</span>
          </button>
        </div>
      </div>

      {/* Summary count text */}
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span>
          <strong className="text-slate-900 font-mono tabular-nums">{activeItems.length}</strong> active
        </span>
        <span aria-hidden="true" className="text-slate-300">·</span>
        <span>
          <strong className="text-slate-900 font-mono tabular-nums">{completedItems.length}</strong> completed (retained in list)
        </span>
      </div>

      {/* Main List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
              {currentConfig.icon}
            </div>
            <p className="font-semibold text-slate-900 text-sm">No {currentConfig.title.toLowerCase()} recorded</p>
            <p className="mt-1 text-slate-500 max-w-sm mx-auto">
              Track your first {currentConfig.placeholder} to monitor due dates and receive scheduled digest reminders.
            </p>
            <button
              onClick={() => onOpenCreate(type)}
              className="mt-4 px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg inline-flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Track New {currentConfig.title.slice(0, -1)}</span>
            </button>
          </div>
        ) : (
          <div>
            {filtered.map((item) => (
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
      </div>
    </div>
  );
};
