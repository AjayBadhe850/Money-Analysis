import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  LogOut,
  ChevronDown,
  UserCheck,
  Building,
  Sparkles,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { authService } from '../../services/auth.service';
import { UserRole } from '../../types';

export const Navbar: React.FC = () => {
  const { user, login, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const demoAccounts = [
    { role: 'Admin' as UserRole, email: 'admin@moneyanalysis.ai', name: 'Eleanor Vance (Admin)' },
    { role: 'Finance Manager' as UserRole, email: 'finance@moneyanalysis.ai', name: 'Marcus Sterling (Finance)' },
    { role: 'Department Manager' as UserRole, email: 'engineering.lead@moneyanalysis.ai', name: 'Dr. Sarah Chen (Eng Lead)' },
    { role: 'Employee' as UserRole, email: 'employee@moneyanalysis.ai', name: 'Jordan Rivera (Employee)' },
    { role: 'Auditor' as UserRole, email: 'auditor@moneyanalysis.ai', name: 'Arthur Pendelton (Auditor)' },
  ];

  const handleSwitchRole = async (email: string) => {
    setShowRoleMenu(false);
    try {
      const res = await authService.login({ email, password: 'Password123!' });
      login(res.access_token, res.user);
      showToast('success', 'Role Switched', `Now logged in as ${res.user.name} (${res.user.role})`);
    } catch {
      showToast('error', 'Switch Failed', 'Could not authenticate demo user');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    showToast('info', 'Logged out', 'You have been signed out');
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Organization Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium">
          <Building className="w-3.5 h-3.5 text-indigo-400" />
          <span>Acme Global Technologies Inc.</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse ml-1" />
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
          Fiscal 2026
        </span>
      </div>

      {/* Right: Role Switcher, Alerts & Profile */}
      <div className="flex items-center gap-3">
        {/* Quick Demo Role Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
            <span>Role: <strong className="text-indigo-400">{user?.role}</strong></span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-800 bg-slate-900 shadow-2xl p-1.5 z-50">
              <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 mb-1">
                Quick Test Switcher
              </div>
              {demoAccounts.map((acc) => (
                <button
                  key={acc.email}
                  onClick={() => handleSwitchRole(acc.email)}
                  className={`w-full text-left flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors ${
                    user?.email === acc.email
                      ? 'bg-indigo-600/20 text-indigo-300 font-semibold'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div>
                    <div className="text-slate-100">{acc.name}</div>
                    <div className="text-[10px] text-slate-400">{acc.role}</div>
                  </div>
                  {user?.email === acc.email && <UserCheck className="w-3.5 h-3.5 text-indigo-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notification Bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-colors"
          title="Cost Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
        </button>

        {/* User Info & Logout */}
        <div className="h-6 w-px bg-slate-800 mx-1" />

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
};
