import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Shield, ArrowRight, Lock, Mail, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authService } from '../services/auth.service';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [email, setEmail] = useState('finance@moneyanalysis.ai');
  const [password, setPassword] = useState('Password123!');
  const [isLoading, setIsLoading] = useState(false);

  const demoAccounts = [
    { label: 'Admin', email: 'admin@moneyanalysis.ai', role: 'Admin' },
    { label: 'Finance Mgr', email: 'finance@moneyanalysis.ai', role: 'Finance Manager' },
    { label: 'Dept Lead', email: 'engineering.lead@moneyanalysis.ai', role: 'Dept Lead' },
    { label: 'Employee', email: 'employee@moneyanalysis.ai', role: 'Employee' },
    { label: 'Auditor', email: 'auditor@moneyanalysis.ai', role: 'Auditor' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await authService.login({ email, password });
      login(res.access_token, res.user);
      showToast('success', 'Welcome back!', `Logged in as ${res.user.name}`);
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid email or password';
      showToast('error', 'Authentication Failed', msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('Password123!');
  };

  return (
    <div className="min-h-screen w-full relative flex items-center justify-center p-4 sm:p-6 md:p-8 bg-[#f8faff] overflow-hidden select-none">
      {/* Background Graphic - High Res Cover */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
        style={{ backgroundImage: `url('/login-bg.png')` }}
      />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-[380px] my-auto">
        {/* Glassmorphism Authentication Card */}
        <div
          className="rounded-3xl border border-white/90 bg-white/75 dark:bg-slate-900/80 shadow-[0_20px_60px_-15px_rgba(2,132,199,0.22)] p-6 sm:p-7 transition-all duration-300"
          style={{
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          {/* Header */}
          <div className="text-center mb-5">
            <div className="inline-flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 text-white shadow-lg shadow-blue-500/25 mb-2.5">
              <Sparkles className="w-5 h-5" />
            </div>
            <h2 className="!font-sans text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Sign In
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              Autonomous Financial Intelligence Platform
            </p>
          </div>

          {/* Quick Demo Role Selector */}
          <div className="mb-5 p-2.5 rounded-2xl bg-slate-50/85 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80">
            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-600 dark:text-indigo-300 uppercase tracking-wider mb-2 px-1">
              <span className="flex items-center gap-1.5 font-sans">
                <Shield className="w-3.5 h-3.5 text-blue-600 dark:text-indigo-400" />
                Quick Demo Roles
              </span>
              <span className="text-[10px] lowercase text-slate-400">1-click autofill</span>
            </div>
            <div className="grid grid-cols-3 gap-1">
              {demoAccounts.map((d) => {
                const isSelected = email === d.email;
                return (
                  <button
                    key={d.email}
                    type="button"
                    onClick={() => handleQuickLogin(d.email)}
                    className={`px-1.5 py-1.5 rounded-xl text-[11px] font-medium border transition-all text-center flex items-center justify-center gap-1 font-sans cursor-pointer ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-500/20 font-semibold'
                        : 'bg-white/90 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                    }`}
                  >
                    {isSelected && <CheckCircle2 className="w-3 h-3 shrink-0" />}
                    <span className="truncate">{d.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div className="space-y-1">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 font-sans">
                Work Email
              </label>
              <div className="relative flex items-center">
                <div className="absolute left-3 text-slate-400 pointer-events-none">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  className="w-full h-10 pl-9 pr-3 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white/90 dark:bg-slate-950/70 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all shadow-sm font-sans"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 font-sans">
                Password
              </label>
              <div className="relative flex items-center">
                <div className="absolute left-3 text-slate-400 pointer-events-none">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full h-10 pl-9 pr-3 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white/90 dark:bg-slate-950/70 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all shadow-sm font-sans"
                />
              </div>
            </div>

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full h-10 mt-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-semibold text-sm rounded-xl shadow-md shadow-blue-500/25 border-0 font-sans cursor-pointer"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to Controller
            </Button>
          </form>

          {/* Footer */}
          <div className="mt-5 pt-3.5 border-t border-slate-200/80 dark:border-slate-800/80 text-center text-xs text-slate-500 dark:text-slate-400 font-sans">
            Need an enterprise account?{' '}
            <Link
              to="/register"
              className="text-blue-600 dark:text-indigo-400 hover:text-blue-700 dark:hover:text-indigo-300 font-semibold transition-colors ml-1"
            >
              Register organization
            </Link>
          </div>
        </div>

        {/* Bottom assurance */}
        <div className="mt-3 text-center">
          <p className="text-[11px] text-slate-500 font-medium font-sans">
            SOC2 Type II Certified • 256-bit AES Encryption
          </p>
        </div>
      </div>
    </div>
  );
};


