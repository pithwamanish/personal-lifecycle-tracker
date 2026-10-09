import React, { useState } from 'react';
import { LogIn, UserPlus, Users, X } from 'lucide-react';
import { User } from '../services/types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (email: string, password?: string) => Promise<void>;
  onSignup: (email: string, password?: string, name?: string) => Promise<void>;
  onSwitchUser: (userId: string) => Promise<void>;
  availableUsers: User[];
  currentUserId?: string;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onLogin,
  onSignup,
  onSwitchUser,
  availableUsers,
  currentUserId,
}) => {
  const [mode, setMode] = useState<'login' | 'signup' | 'switch'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email address is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      if (mode === 'login') {
        await onLogin(email.trim(), password);
      } else {
        await onSignup(email.trim(), password, name.trim());
      }
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = async (userId: string) => {
    try {
      setLoading(true);
      await onSwitchUser(userId);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to switch user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              {mode === 'login' ? 'Sign In to Account' : mode === 'signup' ? 'Create New Account' : 'Switch Active User'}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Email and password authentication</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab switchers */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 pt-2">
          <button
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors ${
              mode === 'login' ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => {
              setMode('signup');
              setError(null);
            }}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors ${
              mode === 'signup' ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Sign Up
          </button>
          <button
            onClick={() => {
              setMode('switch');
              setError(null);
            }}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors ${
              mode === 'switch' ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Switch User ({availableUsers.length})
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              {error}
            </div>
          )}

          {mode === 'switch' ? (
            <div className="space-y-3">
              <p className="text-xs text-slate-600 mb-2">
                Simulate multi-user collaboration and group permissions by switching accounts:
              </p>
              {availableUsers.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleSelectUser(user.id)}
                  className={`w-full p-3 rounded-lg border text-left flex items-center justify-between transition-colors ${
                    user.id === currentUserId
                      ? 'border-slate-900 bg-slate-50'
                      : 'border-slate-200 hover:border-slate-400 hover:bg-slate-50/50'
                  }`}
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{user.name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  {user.id === currentUserId && (
                    <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      Current
                    </span>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <div>
                  <label htmlFor="auth-name" className="block text-xs font-semibold text-slate-800 mb-1">
                    Full Name
                  </label>
                  <input
                    id="auth-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Eleanor Vance"
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              )}

              <div>
                <label htmlFor="auth-email" className="block text-xs font-semibold text-slate-800 mb-1">
                  Email Address <span className="text-red-600">*</span>
                </label>
                <input
                  id="auth-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  required
                />
              </div>

              <div>
                <label htmlFor="auth-password" className="block text-xs font-semibold text-slate-800 mb-1">
                  Password <span className="text-red-600">*</span>
                </label>
                <input
                  id="auth-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
                  required
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    'Processing...'
                  ) : mode === 'login' ? (
                    <>
                      <LogIn className="w-4 h-4" />
                      Sign In
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4" />
                      Create Account
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
