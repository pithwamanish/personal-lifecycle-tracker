import React, { useState } from 'react';
import { Check, X } from 'lucide-react';
import { Group, LifecycleItem, LifecycleType, UpdateItemDTO } from '../services/types';

interface EditItemModalProps {
  item: LifecycleItem | null;
  isOpen: boolean;
  onClose: () => void;
  groups: Group[];
  onSubmit: (id: string, data: UpdateItemDTO) => Promise<void>;
}

export const EditItemModal: React.FC<EditItemModalProps> = ({
  item,
  isOpen,
  onClose,
  groups,
  onSubmit,
}) => {
  if (!isOpen || !item) return null;

  const [name, setName] = useState(item.name);
  const [lifecycleType, setLifecycleType] = useState<LifecycleType>(item.lifecycleType);
  const [dueDate, setDueDate] = useState(item.dueDate || '');
  const [hasDueDate, setHasDueDate] = useState(Boolean(item.dueDate));
  const [groupId, setGroupId] = useState<string>(item.groupId || '');
  const [status, setStatus] = useState<'active' | 'completed'>(item.status);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Item name is required');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit(item.id, {
        name: name.trim(),
        lifecycleType,
        dueDate: hasDueDate && dueDate ? dueDate : undefined,
        groupId: groupId ? groupId : null,
        status,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update item');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Edit Lifecycle Item</h2>
            <p className="text-xs text-slate-500 mt-0.5">Update common fields for this record</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              {error}
            </div>
          )}

          {/* Lifecycle Type */}
          <div>
            <label htmlFor="edit-lifecycle-type" className="block text-xs font-semibold text-slate-800 mb-1">
              Lifecycle Type
            </label>
            <select
              id="edit-lifecycle-type"
              value={lifecycleType}
              onChange={(e) => setLifecycleType(e.target.value as LifecycleType)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
            >
              <option value="renewal">Renewal (Insurance, Passport, License)</option>
              <option value="maintenance">Maintenance (Car, HVAC, Appliances)</option>
              <option value="warranty">Warranty (Electronics, Home Assets)</option>
            </select>
          </div>

          {/* Name */}
          <div>
            <label htmlFor="edit-name" className="block text-xs font-semibold text-slate-800 mb-1">
              Name <span className="text-red-600">*</span>
            </label>
            <input
              id="edit-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
              required
            />
          </div>

          {/* Due date */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="edit-due-date" className="block text-xs font-semibold text-slate-800">
                Due Date
              </label>
              <label className="text-xs text-slate-500 flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasDueDate}
                  onChange={(e) => setHasDueDate(e.target.checked)}
                  className="rounded border-slate-300 text-slate-900 focus:ring-slate-900"
                />
                <span>Specify due date</span>
              </label>
            </div>

            {hasDueDate ? (
              <input
                id="edit-due-date"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            ) : (
              <div className="text-xs text-slate-500 bg-slate-50 px-3 py-2 border border-dashed border-slate-200 rounded-lg">
                No due date specified (will not trigger upcoming/overdue flags).
              </div>
            )}
          </div>

          {/* Scope / Group */}
          <div>
            <label htmlFor="edit-group" className="block text-xs font-semibold text-slate-800 mb-1">
              Access & Scope
            </label>
            <select
              id="edit-group"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
            >
              <option value="">Personal (Only you)</option>
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  Group: {group.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1">Status</label>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="edit-status"
                  value="active"
                  checked={status === 'active'}
                  onChange={() => setStatus('active')}
                  className="text-slate-900 focus:ring-slate-900"
                />
                <span>Active</span>
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="edit-status"
                  value="completed"
                  checked={status === 'completed'}
                  onChange={() => setStatus('completed')}
                  className="text-slate-900 focus:ring-slate-900"
                />
                <span>Completed</span>
              </label>
            </div>
          </div>

          {/* Footer actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-700 hover:text-slate-900 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : 'Save Changes'}
              <Check className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
