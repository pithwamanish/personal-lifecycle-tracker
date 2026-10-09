import React, { useState } from 'react';
import { Mail, Plus, Shield, Trash2, UserMinus, Users } from 'lucide-react';
import { Group, User } from '../services/types';

interface GroupsViewProps {
  groups: Group[];
  currentUser: User | null;
  onCreateGroup: (name: string) => Promise<void>;
  onInviteMember: (groupId: string, email: string) => Promise<void>;
  onRemoveMember: (groupId: string, email: string) => Promise<void>;
  onLeaveGroup: (groupId: string) => Promise<void>;
  onDeleteGroup: (groupId: string) => Promise<void>;
}

export const GroupsView: React.FC<GroupsViewProps> = ({
  groups,
  currentUser,
  onCreateGroup,
  onInviteMember,
  onRemoveMember,
  onLeaveGroup,
  onDeleteGroup,
}) => {
  const [newGroupName, setNewGroupName] = useState('');
  const [inviteEmails, setInviteEmails] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;

    try {
      setSubmitting(true);
      setError(null);
      await onCreateGroup(newGroupName.trim());
      setNewGroupName('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create group');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInvite = async (groupId: string) => {
    const email = inviteEmails[groupId]?.trim();
    if (!email) return;

    try {
      setError(null);
      await onInviteMember(groupId, email);
      setInviteEmails((prev) => ({ ...prev, [groupId]: '' }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to invite member');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Groups & Shared Access</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Collaborate on shared vehicle maintenance, household warranties, and joint renewals.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Create New Group Card */}
      <div className="p-5 bg-white rounded-xl border border-slate-200">
        <h2 className="text-sm font-semibold text-slate-900 mb-1 flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-700" />
          <span>Create New Shared Group</span>
        </h2>
        <p className="text-xs text-slate-500 mb-3">
          All invited group members can create, view, edit, and complete shared lifecycle items.
        </p>

        <form onSubmit={handleCreateGroup} className="flex gap-2 max-w-md">
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="e.g. Oakridge Family & Home"
            className="flex-1 px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
            required
          />
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 shrink-0 disabled:opacity-50"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Group</span>
          </button>
        </form>
      </div>

      {/* List of Groups */}
      <div className="space-y-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Your Groups ({groups.length})
        </h2>

        {groups.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            You don't belong to any groups yet. Create one above to share lifecycle tracking with family or teammates.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groups.map((group) => {
              const isOwner = group.ownerId === currentUser?.id;

              return (
                <div
                  key={group.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 flex flex-col justify-between"
                >
                  <div>
                    {/* Title & Owner badge */}
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base font-bold text-slate-900">{group.name}</h3>
                        <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-slate-400" />
                          <span>Owner: {group.ownerEmail}</span>
                          {isOwner && (
                            <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-1.5 py-0.2 rounded">
                              You
                            </span>
                          )}
                        </p>
                      </div>

                      {/* Group actions */}
                      {isOwner ? (
                        <button
                          onClick={() => {
                            if (
                              window.confirm(
                                `Delete "${group.name}"? Deleting a group permanently deletes the group AND all its shared items (MVP Decision 30).`
                              )
                            ) {
                              onDeleteGroup(group.id);
                            }
                          }}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete group and all its shared items"
                          aria-label="Delete group"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            if (
                              window.confirm(
                                `Leave "${group.name}"? Shared items will remain with the group (MVP Decision 18).`
                              )
                            ) {
                              onLeaveGroup(group.id);
                            }
                          }}
                          className="text-xs text-slate-500 hover:text-red-600 flex items-center gap-1"
                        >
                          <UserMinus className="w-3.5 h-3.5" />
                          <span>Leave</span>
                        </button>
                      )}
                    </div>

                    {/* Member list */}
                    <div className="mt-4 pt-3 border-t border-slate-100">
                      <div className="text-xs font-semibold text-slate-700 mb-2">
                        Members ({group.memberEmails.length}):
                      </div>
                      <div className="space-y-1.5">
                        {group.memberEmails.map((email) => (
                          <div
                            key={email}
                            className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-50 text-slate-700"
                          >
                            <span className="truncate">{email}</span>
                            {isOwner && email.toLowerCase() !== group.ownerEmail.toLowerCase() && (
                              <button
                                onClick={() => onRemoveMember(group.id, email)}
                                className="text-slate-400 hover:text-red-600 transition-colors p-0.5"
                                title="Remove member"
                                aria-label={`Remove ${email}`}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Invite by email form (Decision 13) */}
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                      Invite Member by Email
                    </label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Mail className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                        <input
                          type="email"
                          value={inviteEmails[group.id] || ''}
                          onChange={(e) =>
                            setInviteEmails((prev) => ({
                              ...prev,
                              [group.id]: e.target.value,
                            }))
                          }
                          placeholder="colleague@example.com"
                          className="w-full pl-8 pr-2.5 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => handleInvite(group.id)}
                        className="px-3 py-1.5 text-xs font-medium text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors shrink-0"
                      >
                        Invite
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
