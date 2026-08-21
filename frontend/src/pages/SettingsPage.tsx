import React from 'react';
import { Settings, Shield, Building, Key, CheckCircle2, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  const rbacMatrix = [
    { role: 'Admin', dash: 'Full', writeTx: 'Yes', csv: 'Yes', budget: 'Yes', vendor: 'Yes', subs: 'Yes', audit: 'Full' },
    { role: 'Finance Manager', dash: 'Full', writeTx: 'Yes', csv: 'Yes', budget: 'Yes', vendor: 'Yes', subs: 'Yes', audit: 'Full' },
    { role: 'Department Manager', dash: 'Dept', writeTx: 'Yes (Dept)', csv: 'Yes (Dept)', budget: 'View', vendor: 'View', subs: 'View', audit: 'No' },
    { role: 'Employee', dash: 'Basic', writeTx: 'Request', csv: 'No', budget: 'View', vendor: 'View', subs: 'View', audit: 'No' },
    { role: 'Auditor', dash: 'Full Read', writeTx: 'Read-Only', csv: 'Read-Only', budget: 'Read-Only', vendor: 'Read-Only', subs: 'Read-Only', audit: 'Full' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          System Settings & Access Governance
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Enterprise configuration, user role permissions matrix, and database connectivity status
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Profile Card */}
        <Card className="border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold text-lg">
              {user?.name.charAt(0)}
            </div>
            <div>
              <h3 className="font-bold text-slate-100 text-base">{user?.name}</h3>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Assigned Role:</span>
              <Badge variant="default">{user?.role}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Company ID:</span>
              <span className="font-mono text-slate-200">#{user?.company_id || 1}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Session Security:</span>
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> JWT HS256 Active
              </span>
            </div>
          </div>
        </Card>

        {/* Company Settings */}
        <Card className="lg:col-span-2 border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
            <Building className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-100 text-base">Organization Profile</h3>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800">
              <span className="text-slate-400 block mb-1">Company Legal Name</span>
              <span className="font-bold text-slate-100 text-sm">Acme Global Technologies Inc.</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800">
              <span className="text-slate-400 block mb-1">Industry Sector</span>
              <span className="font-bold text-slate-100 text-sm">Enterprise Software & AI</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800">
              <span className="text-slate-400 block mb-1">Functional Base Currency</span>
              <span className="font-bold text-slate-100 text-sm">USD ($)</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800">
              <span className="text-slate-400 block mb-1">Fiscal Year Start Month</span>
              <span className="font-bold text-slate-100 text-sm">January 1</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Role-Based Access Control Matrix */}
      <Card className="border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400" />
            Role-Based Authorization & Privileges Matrix (RBAC)
          </CardTitle>
          <CardDescription>
            System-enforced access boundaries across administrative, operational, and auditing personnel
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Dashboard</th>
                  <th className="px-4 py-3">Transactions</th>
                  <th className="px-4 py-3">CSV Import</th>
                  <th className="px-4 py-3">Budgets</th>
                  <th className="px-4 py-3">Vendors</th>
                  <th className="px-4 py-3">Subscriptions</th>
                  <th className="px-4 py-3">Audit Logs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {rbacMatrix.map((r) => (
                  <tr
                    key={r.role}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      user?.role === r.role ? 'bg-indigo-600/10 font-semibold text-indigo-200' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-bold text-slate-100 flex items-center gap-1.5">
                      {r.role}
                      {user?.role === r.role && <Badge variant="default" size="sm">You</Badge>}
                    </td>
                    <td className="px-4 py-3">{r.dash}</td>
                    <td className="px-4 py-3">{r.writeTx}</td>
                    <td className="px-4 py-3">{r.csv}</td>
                    <td className="px-4 py-3">{r.budget}</td>
                    <td className="px-4 py-3">{r.vendor}</td>
                    <td className="px-4 py-3">{r.subs}</td>
                    <td className="px-4 py-3">{r.audit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
