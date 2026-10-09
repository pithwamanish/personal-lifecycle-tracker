import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, Clock, Globe, Mail, Send, ShieldCheck } from 'lucide-react';
import { DailyDigestConfig, DailyDigestEmail, DigestDeliveryTime, User } from '../services/types';

interface RemindersDigestViewProps {
  currentUser: User | null;
  config: DailyDigestConfig;
  onUpdateConfig: (config: Partial<DailyDigestConfig>) => Promise<void>;
  onGenerateDigest: (recipientEmail?: string) => Promise<DailyDigestEmail>;
  digestHistory: DailyDigestEmail[];
}

export const RemindersDigestView: React.FC<RemindersDigestViewProps> = ({
  currentUser,
  config,
  onUpdateConfig,
  onGenerateDigest,
  digestHistory,
}) => {
  const [selectedDigest, setSelectedDigest] = useState<DailyDigestEmail | null>(
    digestHistory[0] || null
  );
  const [previewTab, setPreviewTab] = useState<'html' | 'text'>('html');
  const [isGenerating, setIsGenerating] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const deliveryOptions: { id: DigestDeliveryTime; label: string; desc: string; letter: string }[] = [
    { id: '06:00', letter: 'A', label: '6:00 AM', desc: 'Early morning review before daily routine' },
    { id: '08:00', letter: 'B', label: '8:00 AM', desc: 'Morning planning as workday commences (Default)' },
    { id: '09:00', letter: 'C', label: '9:00 AM', desc: 'Start-of-workday action briefing' },
    { id: '12:00', letter: 'D', label: '12:00 PM', desc: 'Midday check-in and task review' },
  ];

  const handleDeliveryTimeChange = async (time: DigestDeliveryTime) => {
    await onUpdateConfig({ deliveryTime: time });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  const handleGenerateNow = async () => {
    try {
      setIsGenerating(true);
      const email = await onGenerateDigest(currentUser?.email);
      setSelectedDigest(email);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reminders & Daily Email Digest</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Automated notifications and scheduled daily digest of upcoming and overdue lifecycle items.
        </p>
      </div>

      {/* Reminder Channels Overview Banner */}
      <div className="p-5 bg-white rounded-xl border border-slate-200 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-slate-100 rounded-lg shrink-0">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">Dual Channel Enabled</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Both in-app badges and daily email digests are permanently enabled per Decision 22.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="p-2 bg-slate-100 rounded-lg shrink-0">
            <Clock className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">Fixed Reminder Schedule</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Overdue items remain flagged until completed; items within 30 days are tracked as upcoming.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="p-2 bg-slate-100 rounded-lg shrink-0">
            <Globe className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">Single Time Zone</h3>
            <p className="text-xs text-slate-500 mt-0.5 font-mono">
              {config.timeZone} (Application Global)
            </p>
          </div>
        </div>
      </div>

      {/* Question 34 Pending Decision: Daily Digest Delivery Time */}
      <div className="p-6 bg-white rounded-xl border border-slate-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Daily Email Digest Delivery Time
              </h2>
              {saveSuccess && (
                <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Saved
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Select the scheduled delivery time for your daily digest (Question 34):
            </p>
          </div>

          <button
            onClick={handleGenerateNow}
            disabled={isGenerating}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2 self-start sm:self-auto shrink-0 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{isGenerating ? 'Generating...' : 'Simulate / Send Digest Now'}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {deliveryOptions.map((opt) => {
            const isSelected = config.deliveryTime === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleDeliveryTimeChange(opt.id)}
                className={`p-4 rounded-xl border text-left transition-all relative ${
                  isSelected
                    ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-400 text-slate-900'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-bold ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                    Option {opt.letter}
                  </span>
                  {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                </div>
                <div className="text-lg font-bold font-mono tracking-tight">{opt.label}</div>
                <div className={`text-xs mt-1 ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                  {opt.desc}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Daily Digest Inspector & Previewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* History column */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 p-5 flex flex-col h-[500px]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center justify-between">
            <span>Digest Sent Log ({digestHistory.length})</span>
            <Mail className="w-3.5 h-3.5 text-slate-400" />
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {digestHistory.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">
                No digests dispatched yet. Click "Simulate / Send Digest Now" to generate one.
              </div>
            ) : (
              digestHistory.map((d) => {
                const isSelected = selectedDigest?.id === d.id;
                return (
                  <button
                    key={d.id}
                    onClick={() => setSelectedDigest(d)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'border-slate-900 bg-slate-50'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-900">{d.recipientEmail}</span>
                      <span className="font-mono text-[11px] text-slate-400">
                        {new Date(d.generatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-600 truncate">{d.subject}</div>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1 font-mono">
                      <span>{d.overdueCount} overdue</span>
                      <span>·</span>
                      <span>{d.upcomingCount} upcoming</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Live Email Preview column */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col h-[500px]">
          {/* Preview toolbar */}
          <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-900">Email Digest Preview</span>
              {selectedDigest && (
                <span className="text-xs text-slate-500 ml-2">
                  — {selectedDigest.subject}
                </span>
              )}
            </div>

            <div className="flex items-center gap-1 bg-slate-200 p-0.5 rounded-lg text-xs font-medium">
              <button
                onClick={() => setPreviewTab('html')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  previewTab === 'html' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                HTML Template
              </button>
              <button
                onClick={() => setPreviewTab('text')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  previewTab === 'text' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Plain Text
              </button>
            </div>
          </div>

          {/* Email content */}
          <div className="flex-1 overflow-auto p-4 bg-slate-100">
            {selectedDigest ? (
              previewTab === 'html' ? (
                <div
                  className="bg-white rounded shadow-xs mx-auto max-w-xl overflow-hidden"
                  dangerouslySetInnerHTML={{ __html: selectedDigest.htmlContent }}
                />
              ) : (
                <pre className="bg-slate-900 text-slate-100 p-5 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap">
                  {selectedDigest.textContent}
                </pre>
              )
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
                <AlertCircle className="w-8 h-8 text-slate-400 mb-2" />
                <p>Click "Simulate / Send Digest Now" to see how scheduled emails are formatted and delivered.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
