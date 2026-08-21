import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Shield, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authService } from '../services/auth.service';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';

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
    { label: 'Dept Mgr', email: 'engineering.lead@moneyanalysis.ai', role: 'Department Manager' },
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
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Brand logo */}
      <div className="flex items-center gap-3 mb-6 z-10">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 flex items-center justify-center shadow-xl shadow-indigo-500/20">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Money Analysis <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">AI</span>
          </h1>
          <p className="text-xs text-slate-400">Multi-Agent Finance Controller</p>
        </div>
      </div>

      <Card className="w-full max-w-md border-slate-800 bg-slate-900/90 backdrop-blur-xl shadow-2xl z-10">
        <CardHeader className="space-y-1 text-center pb-6">
          <CardTitle className="text-xl font-bold text-slate-100">Sign in to your account</CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Enter your enterprise credentials or choose a demo role below
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Demo account quick fill buttons */}
          <div className="mb-6 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-indigo-400 uppercase tracking-wider mb-2.5">
              <Shield className="w-3 h-3" /> Quick Demo Role Selector
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {demoAccounts.map((d) => (
                <button
                  key={d.email}
                  type="button"
                  onClick={() => handleQuickLogin(d.email)}
                  className={`px-2 py-1.5 rounded-lg text-xs font-medium border transition-all text-center ${
                    email === d.email
                      ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300 font-semibold'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
            <Button
              type="submit"
              className="w-full mt-2"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center border-t border-slate-800/80 pt-4 text-xs text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-medium ml-1">
            Register company
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
};
