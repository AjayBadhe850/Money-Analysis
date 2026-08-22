import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  LogOut,
  ChevronDown,
  UserCheck,
  Building,
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
    <header className="h-16 border-b border-slate-200/80 bg-white/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30 select-none">
      {/* Left: Organization Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100/90 border border-slate-200 text-slate-800 text-xs font-semibold font-sans shadow-sm">
          <Building className="w-3.5 h-3.5 text-blue-600" />
          <span>Acme Global Technologies Inc.</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse ml-1" />
        </div>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200/70 font-semibold font-sans">
          Fiscal 2026
        </span>
      </div>

      {/* Right: Role Switcher, Alerts & Profile */}
      <div className="flex items-center gap-3 font-sans">
        {/* Quick Demo Role Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 shadow-sm transition-all cursor-pointer"
          >
            <Shield className="w-3.5 h-3.5 text-blue-600" />
            <span>Role: <strong className="text-blue-600">{user?.role}</strong></span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-slate-200 bg-white shadow-xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 mb-1">
                Quick Role Switcher
              </div>
              {demoAccounts.map((acc) => (
                <button
                  key={acc.email}
                  onClick={() => handleSwitchRole(acc.email)}
                  className={`w-full text-left flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-colors cursor-pointer ${
                    user?.email === acc.email
                      ? 'bg-blue-50 text-blue-700 font-semibold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div>
                    <div className="text-slate-900 font-medium">{acc.name}</div>
                    <div className="text-[10px] text-slate-500">{acc.role}</div>
                  </div>
                  {user?.email === acc.email && <UserCheck className="w-3.5 h-3.5 text-blue-600" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notification Bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
          title="Cost Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
        </button>

        {/* User Info & Logout */}
        <div className="h-5 w-px bg-slate-200 mx-1" />

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200/80 hover:border-rose-200 transition-all cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
};

