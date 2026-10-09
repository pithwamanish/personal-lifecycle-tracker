import React from 'react';
import { Calendar, CheckCircle2, Circle, Edit3, Trash2, Users } from 'lucide-react';
import { formatDisplayDate, getItemUrgency, getRelativeDueDateLabel, getTodayDateString } from '../services/dateUtils';
import { LifecycleItem } from '../services/types';

interface ItemRowProps {
  item: LifecycleItem;
  onToggleComplete: (id: string) => void;
  onEdit: (item: LifecycleItem) => void;
  onDelete: (id: string) => void;
}

export const ItemRow: React.FC<ItemRowProps> = ({
  item,
  onToggleComplete,
  onEdit,
  onDelete,
}) => {
  const todayStr = getTodayDateString();
  const urgency = getItemUrgency(item, todayStr);
  const isCompleted = item.status === 'completed';

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'renewal':
        return 'Renewal';
      case 'maintenance':
        return 'Maintenance';
      case 'warranty':
        return 'Warranty';
      default:
        return type;
    }
  };

  return (
    <div
      className={`group flex flex-col sm:flex-row sm:items-center justify-between p-4 border-b border-slate-200 transition-colors ${
        isCompleted
          ? 'bg-slate-50/60 text-slate-500'
          : urgency === 'overdue'
          ? 'bg-red-50/30 hover:bg-red-50/60'
          : urgency === 'upcoming'
          ? 'bg-amber-50/20 hover:bg-amber-50/50'
          : 'bg-white hover:bg-slate-50/80'
      }`}
    >
      <div className="flex items-start sm:items-center gap-3.5 flex-1 min-w-0">
        {/* Toggle complete button */}
        <button
          onClick={() => onToggleComplete(item.id)}
          className="mt-0.5 sm:mt-0 text-slate-400 hover:text-slate-900 transition-colors shrink-0 focus-visible:outline-2 focus-visible:outline-slate-900 rounded"
          title={isCompleted ? 'Mark as active' : 'Mark as complete'}
          aria-label={isCompleted ? 'Mark as active' : 'Mark as complete'}
        >
          {isCompleted ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          ) : (
            <Circle className="w-5 h-5 hover:text-emerald-600" />
          )}
        </button>

        {/* Item details */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`text-sm font-semibold truncate ${
                isCompleted ? 'line-through text-slate-400' : 'text-slate-900'
              }`}
            >
              {item.name}
            </span>
          </div>

          {/* Zero-Pill metadata with subtle typographic separators */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-slate-500 mt-1">
            <span className="font-medium text-slate-700">{getTypeLabel(item.lifecycleType)}</span>
            <span aria-hidden="true" className="text-slate-300">·</span>
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-3 h-3 text-slate-400 inline" />
              <span>{formatDisplayDate(item.dueDate)}</span>
              {!isCompleted && item.dueDate && (
                <span
                  className={`font-medium ${
                    urgency === 'overdue'
                      ? 'text-red-700'
                      : urgency === 'upcoming'
                      ? 'text-amber-700'
                      : 'text-slate-500'
                  }`}
                >
                  ({getRelativeDueDateLabel(item.dueDate, item.status, todayStr)})
                </span>
              )}
            </span>

            <span aria-hidden="true" className="text-slate-300">·</span>
            {item.groupName ? (
              <span className="inline-flex items-center gap-1 text-slate-600">
                <Users className="w-3 h-3 text-slate-400" />
                <span>{item.groupName}</span>
              </span>
            ) : (
              <span className="text-slate-500">Personal</span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-3 sm:mt-0 pl-8 sm:pl-4 shrink-0">
        <button
          onClick={() => onEdit(item)}
          className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors"
          title="Edit item"
          aria-label="Edit item"
        >
          <Edit3 className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Permanently delete item"
          aria-label="Permanently delete item"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
