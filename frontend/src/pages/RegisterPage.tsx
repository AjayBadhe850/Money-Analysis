import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authService } from '../services/auth.service';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';

export const RegisterPage: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [companyName, setCompanyName] = useState('Acme Global Technologies Inc.');
  const [role, setRole] = useState('Finance Manager');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await authService.register({
        name,
        email,
        password,
        role,
        company_name: companyName,
      });
      login(res.access_token, res.user);
      showToast('success', 'Registration Successful!', `Welcome to Money Analysis, ${res.user.name}`);
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Check inputs.';
      showToast('error', 'Registration Error', msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

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
        <CardHeader className="space-y-1 text-center pb-4">
          <CardTitle className="text-xl font-bold text-slate-100">Create your workspace</CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Set up your organization for autonomous financial governance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Eleanor Vance"
              required
            />
            <Input
              label="Work Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="eleanor@company.com"
              required
            />
            <Input
              label="Company Name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Acme Technologies Inc."
              required
            />
            <Select
              label="User Role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              options={[
                { label: 'Admin (Full Privileges)', value: 'Admin' },
                { label: 'Finance Manager (Budgets & Approval)', value: 'Finance Manager' },
                { label: 'Department Manager (Spend Overseer)', value: 'Department Manager' },
                { label: 'Employee (Requester)', value: 'Employee' },
                { label: 'Auditor (Read-Only Governance)', value: 'Auditor' },
              ]}
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              required
            />
            <Button
              type="submit"
              className="w-full mt-2"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Get Started
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center border-t border-slate-800/80 pt-4 text-xs text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium ml-1">
            Sign In
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
};
