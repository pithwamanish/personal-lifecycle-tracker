import React, { useState } from 'react';
import { Check, ChevronRight, Clock, HelpCircle, Shield, Wrench, X } from 'lucide-react';
import { CreateItemDTO, Group, LifecycleType } from '../services/types';

interface GuidedCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  groups: Group[];
  onSubmit: (data: CreateItemDTO) => Promise<void>;
  preselectedType?: LifecycleType;
}

export const GuidedCreateModal: React.FC<GuidedCreateModalProps> = ({
  isOpen,
  onClose,
  groups,
  onSubmit,
  preselectedType,
}) => {
  const [step, setStep] = useState<1 | 2>(preselectedType ? 2 : 1);
  const [selectedType, setSelectedType] = useState<LifecycleType>(preselectedType || 'renewal');
  const [name, setName] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [hasDueDate, setHasDueDate] = useState(true);
  const [groupId, setGroupId] = useState<string>('');
  const [status, setStatus] = useState<'active' | 'completed'>('active');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleTypeSelect = (type: LifecycleType) => {
    setSelectedType(type);
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Item name is required');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit({
        name: name.trim(),
        lifecycleType: selectedType,
        dueDate: hasDueDate && dueDate ? dueDate : undefined,
        groupId: groupId ? groupId : null,
        status,
      });
      // reset state
      setName('');
      setDueDate('');
      setGroupId('');
      setStatus('active');
      setStep(1);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create item');
    } finally {
      setSubmitting(false);
    }
  };

  const typeConfig: Record<
    LifecycleType,
    { title: string; desc: string; icon: React.ReactNode; example: string }
  > = {
    renewal: {
      title: 'Renewal',
      desc: 'Legal, financial, or membership expiration milestones',
      example: 'e.g. Passport, Auto Insurance, Driver License, Gym Membership',
      icon: <Clock className="w-5 h-5 text-indigo-600" />,
    },
    maintenance: {
      title: 'Maintenance',
      desc: 'Periodic physical equipment, home, or vehicle care',
      example: 'e.g. HVAC Filter Change, Oil & Brake Service, Water Purifier',
      icon: <Wrench className="w-5 h-5 text-amber-600" />,
    },
    warranty: {
      title: 'Warranty',
      desc: 'Coverage duration for electronics, appliances, and assets',
      example: 'e.g. Laptop AppleCare, TV Limited Warranty, Refrigerator 5-Yr',
      icon: <Shield className="w-5 h-5 text-emerald-600" />,
    },
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden transition-all">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              {step === 1 ? 'Step 1: Choose Lifecycle Type' : `Step 2: Track New ${typeConfig[selectedType].title}`}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {step === 1
                ? 'Select which category fits your lifecycle record'
                : 'Enter the common fields to begin tracking'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step 1: Type Selection */}
        {step === 1 && (
          <div className="p-6 space-y-3">
            {(['renewal', 'maintenance', 'warranty'] as LifecycleType[]).map((type) => {
              const item = typeConfig[type];
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleTypeSelect(type)}
                  className="w-full text-left p-4 rounded-lg border border-slate-200 hover:border-slate-900 hover:bg-slate-50 transition-all flex items-start gap-4 group"
                >
                  <div className="p-2.5 bg-slate-100 group-hover:bg-white rounded-lg transition-colors shrink-0">
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-900 transition-colors" />
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">{item.desc}</p>
                    <p className="text-xs text-slate-400 italic mt-1">{item.example}</p>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Step 2: Common Fields Form */}
        {step === 2 && (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
                {error}
              </div>
            )}

            {/* Selected type pill / back button */}
            <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-2 text-xs">
                {typeConfig[selectedType].icon}
                <span className="font-semibold text-slate-900">{typeConfig[selectedType].title}</span>
                <span className="text-slate-400">· Guided Mode</span>
              </div>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-slate-600 hover:text-slate-900 font-medium underline"
              >
                Change type
              </button>
            </div>

            {/* Common Field: Name */}
            <div>
              <label htmlFor="item-name" className="block text-xs font-semibold text-slate-800 mb-1">
                Name <span className="text-red-600">*</span>
              </label>
              <input
                id="item-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={typeConfig[selectedType].example.replace('e.g. ', '').split(',')[0]}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
                required
                autoFocus
              />
            </div>

            {/* Common Field: Due Date (optional manual entry) */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="item-due-date" className="block text-xs font-semibold text-slate-800">
                  Due Date
                </label>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-500 flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hasDueDate}
                      onChange={(e) => setHasDueDate(e.target.checked)}
                      className="rounded border-slate-300 text-slate-900 focus:ring-slate-900"
                    />
                    <span>Has specific due date</span>
                  </label>
                </div>
              </div>

              {hasDueDate ? (
                <input
                  id="item-due-date"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              ) : (
                <div className="text-xs text-slate-500 bg-slate-50 px-3 py-2 border border-dashed border-slate-200 rounded-lg flex items-center gap-2">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                  <span>No due date specified (allowed per MVP Decision 29).</span>
                </div>
              )}
            </div>

            {/* Destination: Personal vs Group */}
            <div>
              <label htmlFor="item-group" className="block text-xs font-semibold text-slate-800 mb-1">
                Access & Scope
              </label>
              <select
                id="item-group"
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
              <p className="text-[11px] text-slate-500 mt-1">
                Group items are shared with all members of that group.
              </p>
            </div>

            {/* Status (Active / Completed) */}
            <div>
              <label className="block text-xs font-semibold text-slate-800 mb-1">Initial Status</label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
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
                    name="status"
                    value="completed"
                    checked={status === 'completed'}
                    onChange={() => setStatus('completed')}
                    className="text-slate-900 focus:ring-slate-900"
                  />
                  <span>Completed</span>
                </label>
              </div>
            </div>

            {/* Form Footer */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 text-xs font-medium text-slate-700 hover:text-slate-900 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Track Item'}
                <Check className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
