import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ArrowLeftRight,
  PieChart,
  Building2,
  Users,
  Repeat,
  FileText,
  Sparkles,
  Bot,
  BarChart3,
  Bell,
  History,
  Settings,
  ShieldCheck,
  Zap,
  ShieldAlert,
  TrendingUp,
  FileCheck,
  Cpu,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const financialItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Transactions', path: '/transactions', icon: ArrowLeftRight },
    { label: 'Budgets', path: '/budgets', icon: PieChart },
    { label: 'Departments', path: '/departments', icon: Building2 },
    { label: 'Vendors', path: '/vendors', icon: Users },
    { label: 'Subscriptions', path: '/subscriptions', icon: Repeat },
    { label: 'Invoices', path: '/invoices', icon: FileText },
    { label: 'Reports', path: '/reports', icon: BarChart3 },
  ];

  const aiItems = [
    { label: 'AI Controller Copilot', path: '/ai/assistant', icon: Bot, badge: 'LangGraph' },
    { label: 'Agent Timeline', path: '/ai/timeline', icon: Cpu, badge: 'Telemetry' },
    { label: 'Optimization & What-If', path: '/ai/optimization', icon: Zap, badge: 'Planner' },
    { label: 'Anomaly Radar', path: '/ai/anomalies', icon: ShieldAlert, badge: 'ML' },
    { label: 'Expenditure Forecast', path: '/ai/forecasts', icon: TrendingUp, badge: '90d' },
    { label: 'Governance & Approvals', path: '/ai/approvals', icon: ShieldCheck, badge: 'HITL' },
    { label: 'Document Intelligence', path: '/ai/documents', icon: FileCheck, badge: 'RAG' },
  ];

  const systemItems = [
    { label: 'Alerts', path: '/alerts', icon: Bell },
    { label: 'Audit Logs', path: '/audit-logs', icon: History, roles: ['Admin', 'Finance Manager', 'Auditor'] },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const filterRole = (items: any[]) =>
    items.filter((item) => {
      if (!item.roles) return true;
      if (!user) return false;
      return user.role === 'Admin' || item.roles.includes(user.role);
    });

  return (
    <aside className="w-64 shrink-0 border-r border-slate-200/90 bg-white/90 backdrop-blur-xl flex flex-col h-screen sticky top-0 shadow-[4px_0_24px_rgba(0,0,0,0.02)] select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center shadow-md shadow-blue-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-bold text-sm tracking-tight text-slate-900 flex items-center gap-1.5 font-sans">
            Money Analysis <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200/70 font-semibold font-mono">AI</span>
          </div>
          <p className="text-[10px] text-slate-500 font-medium font-sans">Finance Controller</p>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-4">
        {/* Core Financials */}
        <div className="space-y-1">
          <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-sans">
            Core Financials
          </div>
          {filterRole(financialItems).map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group font-sans ${
                    isActive
                      ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-500/20'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                  <span>{item.label}</span>
                </div>
              </NavLink>
            );
          })}
        </div>

        {/* Multi-Agent AI Suite */}
        <div className="space-y-1 pt-2 border-t border-slate-100">
          <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1 font-sans">
            <Sparkles className="w-3 h-3 text-blue-600" /> Multi-Agent AI Suite
          </div>
          {filterRole(aiItems).map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group font-sans ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold shadow-md shadow-blue-500/20'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 transition-transform group-hover:scale-110 text-cyan-600 group-hover:text-inherit" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] uppercase px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200/80 font-semibold font-mono">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* System */}
        <div className="space-y-1 pt-2 border-t border-slate-100">
          <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-sans">
            System & Security
          </div>
          {filterRole(systemItems).map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group font-sans ${
                    isActive
                      ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-500/20'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                  <span>{item.label}</span>
                </div>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Role Footer Badge */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/60">
        <div className="flex items-center gap-2.5 p-2 rounded-xl bg-white border border-slate-200/80 shadow-sm">
          <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-200/60">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0 font-sans">
            <p className="text-xs font-semibold text-slate-800 truncate">{user?.name || 'Guest'}</p>
            <p className="text-[10px] text-blue-600 font-semibold truncate">{user?.role || 'Viewer'}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

