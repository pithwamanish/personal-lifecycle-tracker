import React, { useCallback, useEffect, useState } from 'react';
import { AuthModal } from './components/AuthModal';
import { DashboardView } from './components/DashboardView';
import { EditItemModal } from './components/EditItemModal';
import { GroupsView } from './components/GroupsView';
import { GuidedCreateModal } from './components/GuidedCreateModal';
import { InAppRemindersDrawer } from './components/InAppRemindersDrawer';
import { LifecycleListView } from './components/LifecycleListView';
import { Navbar, NavTab } from './components/Navbar';
import { RemindersDigestView } from './components/RemindersDigestView';
import {
  CreateItemDTO,
  DailyDigestConfig,
  DailyDigestEmail,
  Group,
  LifecycleItem,
  LifecycleType,
  RemindersSummary,
  UpdateItemDTO,
  User,
  lifecycleService,
} from './services';

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [items, setItems] = useState<LifecycleItem[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null | 'ALL'>('ALL');
  const [reminders, setReminders] = useState<RemindersSummary>({
    overdue: [],
    upcoming: [],
    totalActiveReminders: 0,
  });
  const [digestConfig, setDigestConfig] = useState<DailyDigestConfig>({
    timeZone: 'UTC',
    deliveryTime: '08:00',
    enabled: true,
  });
  const [digestHistory, setDigestHistory] = useState<DailyDigestEmail[]>([]);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createPreselectedType, setCreatePreselectedType] = useState<LifecycleType | undefined>(undefined);
  const [editingItem, setEditingItem] = useState<LifecycleItem | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isRemindersDrawerOpen, setIsRemindersDrawerOpen] = useState(false);

  // Loading state
  const [loading, setLoading] = useState(true);

  // Refresh all state from centralized services layer
  const refreshData = useCallback(async () => {
    try {
      const [user, users] = await Promise.all([
        lifecycleService.getCurrentUser(),
        lifecycleService.listUsers(),
      ]);
      setCurrentUser(user);
      setAllUsers(users);

      if (user) {
        const [loadedGroups, loadedItems, loadedReminders] =
          await Promise.all([
            lifecycleService.getGroups(),
            lifecycleService.getItems(
              selectedGroupId === 'ALL'
                ? undefined
                : { groupId: selectedGroupId }
            ),
            lifecycleService.getRemindersSummary(),
          ]);

        setGroups(loadedGroups);
        setItems(loadedItems);
        setReminders(loadedReminders);

        // Fetch digest settings in background without blocking initial paint
        Promise.all([
          lifecycleService.getDigestConfig(),
          lifecycleService.getDigestHistory(),
        ])
          .then(([loadedConfig, loadedHistory]) => {
            setDigestConfig(loadedConfig);
            setDigestHistory(loadedHistory);
          })
          .catch((err) => console.debug('Digest data deferred fetch error:', err));
      } else {
        setGroups([]);
        setItems([]);
        setReminders({ overdue: [], upcoming: [], totalActiveReminders: 0 });
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedGroupId]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Auth handlers
  const handleLogin = async (email: string, password?: string) => {
    await lifecycleService.login(email, password);
    await refreshData();
  };

  const handleSignup = async (email: string, password?: string, name?: string) => {
    await lifecycleService.signup(email, password, name);
    await refreshData();
  };

  const handleSwitchUser = async (userId: string) => {
    await lifecycleService.switchUser(userId);
    setSelectedGroupId('ALL');
    await refreshData();
  };

  const handleLogout = async () => {
    await lifecycleService.logout();
    await refreshData();
  };

  const handleDeleteAccount = async () => {
    if (!currentUser) return;
    const confirmed = window.confirm(
      `Permanently delete account for ${currentUser.email}?\n\nPer MVP Decision 23, account deletion permanently removes everything associated with the account, including all personal items and owned group items.`
    );
    if (!confirmed) return;

    await lifecycleService.deleteAccount(currentUser.id);
    await refreshData();
  };

  // Item handlers
  const handleCreateItem = async (data: CreateItemDTO) => {
    await lifecycleService.createItem(data);
    await refreshData();
  };

  const handleUpdateItem = async (id: string, data: UpdateItemDTO) => {
    await lifecycleService.updateItem(id, data);
    await refreshData();
  };

  const handleToggleComplete = async (id: string) => {
    await lifecycleService.toggleItemCompletion(id);
    await refreshData();
  };

  const handleDeleteItem = async (id: string) => {
    const confirmed = window.confirm('Permanently delete this lifecycle record?');
    if (!confirmed) return;

    await lifecycleService.deleteItem(id);
    await refreshData();
  };

  // Group handlers
  const handleCreateGroup = async (name: string) => {
    await lifecycleService.createGroup(name);
    await refreshData();
  };

  const handleInviteMember = async (groupId: string, email: string) => {
    await lifecycleService.inviteMember(groupId, email);
    await refreshData();
  };

  const handleRemoveMember = async (groupId: string, email: string) => {
    await lifecycleService.removeMember(groupId, email);
    await refreshData();
  };

  const handleLeaveGroup = async (groupId: string) => {
    await lifecycleService.leaveGroup(groupId);
    setSelectedGroupId('ALL');
    await refreshData();
  };

  const handleDeleteGroup = async (groupId: string) => {
    await lifecycleService.deleteGroup(groupId);
    setSelectedGroupId('ALL');
    await refreshData();
  };

  // Digest handlers
  const handleUpdateDigestConfig = async (configUpdate: Partial<DailyDigestConfig>) => {
    const updated = await lifecycleService.updateDigestConfig(configUpdate);
    setDigestConfig(updated);
  };

  const handleGenerateDigest = async (recipientEmail?: string) => {
    const email = await lifecycleService.generateAndSendDailyDigest(recipientEmail);
    await refreshData();
    return email;
  };

  const openCreateWithOptionalType = (type?: LifecycleType) => {
    setCreatePreselectedType(type);
    setIsCreateOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-slate-700">Loading Personal Lifecycle Tracker...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900 selection:bg-slate-900 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        currentUser={currentUser}
        unreadCount={reminders.totalActiveReminders}
        onOpenReminders={() => setIsRemindersDrawerOpen(true)}
        onOpenCreate={() => openCreateWithOptionalType(undefined)}
        onOpenAuth={() => setIsAuthOpen(true)}
        onDeleteAccount={handleDeleteAccount}
        onLogout={handleLogout}
      />

      {/* Main View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardView
            items={items}
            groups={groups}
            selectedGroupId={selectedGroupId}
            onSelectGroup={setSelectedGroupId}
            onToggleComplete={handleToggleComplete}
            onEdit={(item) => setEditingItem(item)}
            onDelete={handleDeleteItem}
            onOpenCreate={() => openCreateWithOptionalType(undefined)}
          />
        )}

        {activeTab === 'renewals' && (
          <LifecycleListView
            type="renewal"
            items={items}
            groups={groups}
            selectedGroupId={selectedGroupId}
            onSelectGroup={setSelectedGroupId}
            onToggleComplete={handleToggleComplete}
            onEdit={(item) => setEditingItem(item)}
            onDelete={handleDeleteItem}
            onOpenCreate={() => openCreateWithOptionalType('renewal')}
          />
        )}

        {activeTab === 'maintenance' && (
          <LifecycleListView
            type="maintenance"
            items={items}
            groups={groups}
            selectedGroupId={selectedGroupId}
            onSelectGroup={setSelectedGroupId}
            onToggleComplete={handleToggleComplete}
            onEdit={(item) => setEditingItem(item)}
            onDelete={handleDeleteItem}
            onOpenCreate={() => openCreateWithOptionalType('maintenance')}
          />
        )}

        {activeTab === 'warranties' && (
          <LifecycleListView
            type="warranty"
            items={items}
            groups={groups}
            selectedGroupId={selectedGroupId}
            onSelectGroup={setSelectedGroupId}
            onToggleComplete={handleToggleComplete}
            onEdit={(item) => setEditingItem(item)}
            onDelete={handleDeleteItem}
            onOpenCreate={() => openCreateWithOptionalType('warranty')}
          />
        )}

        {activeTab === 'groups' && (
          <GroupsView
            groups={groups}
            currentUser={currentUser}
            onCreateGroup={handleCreateGroup}
            onInviteMember={handleInviteMember}
            onRemoveMember={handleRemoveMember}
            onLeaveGroup={handleLeaveGroup}
            onDeleteGroup={handleDeleteGroup}
          />
        )}

        {activeTab === 'digest' && (
          <RemindersDigestView
            currentUser={currentUser}
            config={digestConfig}
            onUpdateConfig={handleUpdateDigestConfig}
            onGenerateDigest={handleGenerateDigest}
            digestHistory={digestHistory}
          />
        )}
      </main>

      {/* Guided Create Item Modal */}
      <GuidedCreateModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        groups={groups}
        onSubmit={handleCreateItem}
        preselectedType={createPreselectedType}
      />

      {/* Edit Item Modal */}
      <EditItemModal
        item={editingItem}
        isOpen={Boolean(editingItem)}
        onClose={() => setEditingItem(null)}
        groups={groups}
        onSubmit={handleUpdateItem}
      />

      {/* In-App Reminders Drawer */}
      <InAppRemindersDrawer
        isOpen={isRemindersDrawerOpen}
        onClose={() => setIsRemindersDrawerOpen(false)}
        reminders={reminders}
        onToggleComplete={handleToggleComplete}
      />

      {/* Auth & Switch User Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLogin={handleLogin}
        onSignup={handleSignup}
        onSwitchUser={handleSwitchUser}
        availableUsers={allUsers}
        currentUserId={currentUser?.id}
      />

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>
            Personal Lifecycle Tracker &bull; Renewals, Maintenance, and Warranties
          </p>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab('digest')}
              className="hover:text-slate-900 transition-colors"
            >
              Daily Digest Schedule
            </button>
            <span aria-hidden="true">&bull;</span>
            <button
              onClick={() => setIsAuthOpen(true)}
              className="hover:text-slate-900 transition-colors"
            >
              Switch Account
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
