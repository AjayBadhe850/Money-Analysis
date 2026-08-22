import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Shield, ArrowRight, Lock, Mail, CheckCircle2, ShieldCheck } from 'lucide-react';
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
    <div className="min-h-screen w-full relative flex items-center justify-center p-4 sm:p-6 md:p-8 bg-[#f8faff] overflow-hidden select-none font-sans">
      {/* Background Graphic - High Res Cover */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0 pointer-events-none"
        style={{ backgroundImage: `url('/login-bg.png')` }}
      />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-[390px] my-auto">
        {/* Glassmorphism Authentication Card */}
        <div
          className="rounded-3xl border border-white/90 bg-white/85 shadow-[0_20px_60px_-15px_rgba(2,132,199,0.20)] p-6 sm:p-7 transition-all duration-300"
          style={{
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
        >
          {/* Header */}
          <div className="text-center mb-5">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 text-white shadow-lg shadow-blue-500/25 mb-2.5">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              Sign In
            </h2>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Autonomous Financial Intelligence Platform
            </p>
          </div>

          {/* Quick Demo Role Selector */}
          <div className="mb-5 p-2.5 rounded-2xl bg-slate-50/90 border border-slate-200/80">
            <div className="flex items-center justify-between text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-2 px-1">
              <span className="flex items-center gap-1.5 text-blue-600">
                <Shield className="w-3.5 h-3.5" />
                Quick Role Selector
              </span>
              <span className="text-[10px] lowercase text-slate-400 font-normal">1-click autofill</span>
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {demoAccounts.map((d) => {
                const isSelected = email === d.email;
                return (
                  <button
                    key={d.email}
                    type="button"
                    onClick={() => handleQuickLogin(d.email)}
                    className={`px-1.5 py-1.5 rounded-xl text-[11px] font-semibold border transition-all text-center flex items-center justify-center gap-1 cursor-pointer ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-500/20'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
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
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600">
                Work Email
              </label>
              <div className="relative flex items-center">
                <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  className="w-full h-10 pl-10 pr-3.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all shadow-sm font-sans"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600">
                Password
              </label>
              <div className="relative flex items-center">
                <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full h-10 pl-10 pr-3.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all shadow-sm font-sans"
                />
              </div>
            </div>

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full h-10.5 mt-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-bold text-sm rounded-xl shadow-md shadow-blue-500/25 border-0 cursor-pointer"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to Controller
            </Button>
          </form>

          {/* Footer */}
          <div className="mt-5 pt-3.5 border-t border-slate-100 text-center text-xs text-slate-500">
            Need an enterprise account?{' '}
            <Link
              to="/register"
              className="text-blue-600 hover:text-blue-700 font-bold transition-colors ml-1"
            >
              Register organization
            </Link>
          </div>
        </div>

        {/* Bottom assurance */}
        <div className="mt-3.5 text-center flex items-center justify-center gap-1.5 text-[11px] text-slate-600 font-semibold">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>SOC2 Type II Certified • 256-bit AES Encryption</span>
        </div>
      </div>
    </div>
  );
};



