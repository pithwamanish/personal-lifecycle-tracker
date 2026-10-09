import React, { useState } from 'react';
import { Bell, ChevronDown, LogOut, Plus, ShieldAlert, UserCheck, Users } from 'lucide-react';
import { User } from '../services/types';

export type NavTab = 'dashboard' | 'renewals' | 'maintenance' | 'warranties' | 'groups' | 'digest';

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  currentUser: User | null;
  unreadCount: number;
  onOpenReminders: () => void;
  onOpenCreate: () => void;
  onOpenAuth: () => void;
  onDeleteAccount: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  currentUser,
  unreadCount,
  onOpenReminders,
  onOpenCreate,
  onOpenAuth,
  onDeleteAccount,
  onLogout,
}) => {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-8 h-16">
          {/* Zone 1: Single text element wordmark */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onTabChange('dashboard')}
              className="text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap hover:opacity-80 transition-opacity flex items-center gap-2"
            >
              <span className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-black">
                LT
              </span>
              <span>Lifecycle Tracker</span>
            </button>
          </div>

          {/* Zone 2: Concise single-line navigation links */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-slate-600">
            <button
              onClick={() => onTabChange('dashboard')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'dashboard' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => onTabChange('renewals')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'renewals' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Renewals
            </button>
            <button
              onClick={() => onTabChange('maintenance')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'maintenance' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Maintenance
            </button>
            <button
              onClick={() => onTabChange('warranties')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'warranties' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Warranties
            </button>
            <button
              onClick={() => onTabChange('groups')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'groups' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Groups
            </button>
            <button
              onClick={() => onTabChange('digest')}
              className={`hover:text-slate-900 transition-colors whitespace-nowrap shrink-0 py-1 ${
                activeTab === 'digest' ? 'text-slate-900 font-bold border-b-2 border-slate-900' : ''
              }`}
            >
              Daily Digest
            </button>
          </nav>

          {/* Zone 3: Primary action + In-app bell + Account dropdown */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Primary CTA */}
            <button
              onClick={onOpenCreate}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors whitespace-nowrap shrink-0 flex items-center gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Track Item</span>
            </button>

            {/* In-app reminder bell */}
            <button
              onClick={onOpenReminders}
              className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title="Open Reminders"
              aria-label="Open Reminders"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-600 text-white font-mono text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* Account Switcher / Profile */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-1.5 text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors text-xs font-medium"
              >
                <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-xs">
                  {currentUser?.name?.charAt(0) || 'U'}
                </div>
                <span className="hidden md:inline max-w-[100px] truncate">{currentUser?.name || 'Account'}</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {userMenuOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 animate-in fade-in-50"
                  onMouseLeave={() => setUserMenuOpen(false)}
                >
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="text-xs font-semibold text-slate-900 truncate">{currentUser?.name}</p>
                    <p className="text-[11px] text-slate-500 truncate">{currentUser?.email}</p>
                  </div>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onOpenAuth();
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                    <span>Switch or Sign In User</span>
                  </button>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onTabChange('groups');
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span>Manage Groups</span>
                  </button>

                  <div className="border-t border-slate-100 my-1"></div>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onLogout();
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <LogOut className="w-3.5 h-3.5 text-slate-400" />
                    <span>Log Out</span>
                  </button>

                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      onDeleteAccount();
                    }}
                    className="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-red-500" />
                    <span>Delete Account (Permanent)</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile secondary tab strip */}
        <div className="flex lg:hidden overflow-x-auto py-2 gap-4 border-t border-slate-100 text-xs font-medium text-slate-600 no-scrollbar">
          <button
            onClick={() => onTabChange('dashboard')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'dashboard' ? 'text-slate-900 font-bold' : ''}`}
          >
            Dashboard
          </button>
          <button
            onClick={() => onTabChange('renewals')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'renewals' ? 'text-slate-900 font-bold' : ''}`}
          >
            Renewals
          </button>
          <button
            onClick={() => onTabChange('maintenance')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'maintenance' ? 'text-slate-900 font-bold' : ''}`}
          >
            Maintenance
          </button>
          <button
            onClick={() => onTabChange('warranties')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'warranties' ? 'text-slate-900 font-bold' : ''}`}
          >
            Warranties
          </button>
          <button
            onClick={() => onTabChange('groups')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'groups' ? 'text-slate-900 font-bold' : ''}`}
          >
            Groups
          </button>
          <button
            onClick={() => onTabChange('digest')}
            className={`whitespace-nowrap px-2 py-1 ${activeTab === 'digest' ? 'text-slate-900 font-bold' : ''}`}
          >
            Daily Digest
          </button>
        </div>
      </div>
    </header>
  );
};
