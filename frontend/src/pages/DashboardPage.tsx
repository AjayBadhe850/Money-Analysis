import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart as PieIcon,
  AlertTriangle,
  Sparkles,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  Users,
  Repeat,
  RefreshCw,
  Zap,
  ShieldCheck,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Line,
} from 'recharts';
import { dashboardService } from '../services/dashboard.service';
import { aiService } from '../services/ai.service';
import { DashboardResponse, CostAlert, CostEfficiencyScoreResponse } from '../types';
import { formatCurrency, formatPercent, getAlertSeverityColor } from '../utils/formatters';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { Skeleton } from '../components/ui/Skeleton';

const CustomDashboardTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900/95 p-3 shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-200 mb-1.5">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={`item-${index}`} className="flex items-center gap-2 text-slate-300 py-0.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
            <span className="capitalize text-slate-400">{entry.name}:</span>
            <span className="font-bold text-slate-100">{formatCurrency(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [aiScore, setAiScore] = useState<CostEfficiencyScoreResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currency, setCurrency] = useState<'USD' | 'INR' | 'EUR'>('USD');

  const currencyRate = currency === 'INR' ? 83.5 : currency === 'EUR' ? 0.92 : 1.0;
  const currencyPrefix = currency === 'INR' ? '₹' : currency === 'EUR' ? '€' : '$';

  const formatCustomCurrency = (amt: number) => {
    const converted = amt * currencyRate;
    return `${currencyPrefix}${converted.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [summary, alertsData, score] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getAlerts(),
        aiService.getCostEfficiencyScore().catch(() => null),
      ]);
      setData(summary);
      setAlerts(alertsData);
      setAiScore(score);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-28" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-xl" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  const { kpis, charts } = data;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Executive Finance Control
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Live Production
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time financial performance, cash flow dynamics, and autonomous budget control
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {/* Currency Switcher */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            {(['USD', 'INR', 'EUR'] as const).map((curr) => (
              <button
                key={curr}
                onClick={() => setCurrency(curr)}
                className={`px-2.5 py-1 rounded-lg font-bold text-xs transition-all ${
                  currency === curr
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {curr === 'USD' ? '$ USD' : curr === 'INR' ? '₹ INR' : '€ EUR'}
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={fetchDashboardData} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
            Refresh
          </Button>
        </div>
      </div>

      {/* AI Real-time Insights Panel (Section 13) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-amber-500/20 flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-200 block">Marketing Budget Surge</span>
            <span className="text-[11px] text-slate-400">Marketing is pacing 12% above Q3 ceiling ({formatCustomCurrency(18200)} over).</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-indigo-500/20 flex items-start gap-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-200 block">SaaS License Reclamation</span>
            <span className="text-[11px] text-slate-400">18 unused Salesforce seats cost {formatCustomCurrency(2700)}/mo in Sales.</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-cyan-500/20 flex items-start gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 shrink-0">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-200 block">Vendor Terms Arbitrage</span>
            <span className="text-[11px] text-slate-400">AWS on-demand pricing is 38% above 1-yr Compute Savings Plan.</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-purple-500/20 flex items-start gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 shrink-0">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-200 block">Expenditure Velocity</span>
            <span className="text-[11px] text-slate-400">90-day trajectory projects operating costs rising by 8.2%.</span>
          </div>
        </div>
      </div>

      {/* AI Cost Efficiency Score Banner */}
      {aiScore && (
        <Card className="hover-glow border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900/90 to-purple-950/30 p-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex flex-col items-center justify-center shrink-0">
                <span className="text-2xl font-black text-indigo-300">{aiScore.overall_score}</span>
                <span className="text-[10px] font-bold text-indigo-400 uppercase">Score / 100</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-100 text-sm">AI Cost Efficiency Rating</h3>
                  <Badge variant="purple">Grade: {aiScore.grade}</Badge>
                </div>
                <p className="text-xs text-slate-400">
                  Comprehensive 5-pillar financial health index evaluated continuously across ledgers and contracts.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Budget Control</span>
                <span className="font-bold text-slate-200 mt-0.5 block">{aiScore.components.budget_control.score}/25</span>
                <span className="text-[10px] text-emerald-400">{aiScore.components.budget_control.metric}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Vendor Terms</span>
                <span className="font-bold text-slate-200 mt-0.5 block">{aiScore.components.vendor_efficiency.score}/25</span>
                <span className="text-[10px] text-indigo-400">{aiScore.components.vendor_efficiency.metric}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">SaaS Utilization</span>
                <span className="font-bold text-slate-200 mt-0.5 block">{aiScore.components.subscription_utilization.score}/25</span>
                <span className="text-[10px] text-cyan-400">{aiScore.components.subscription_utilization.metric}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Stability</span>
                <span className="font-bold text-slate-200 mt-0.5 block">{aiScore.components.expense_stability.score}/15</span>
                <span className="text-[10px] text-purple-400">{aiScore.components.expense_stability.metric}</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 8 Metric KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Total Revenue */}
        <Card className="hover-glow border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-cyan-950/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Revenue</span>
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-100 tracking-tight">
              {formatCurrency(kpis.total_revenue)}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-cyan-400 mt-2 font-medium">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Inflow from contracts & sales</span>
            </div>
          </CardContent>
        </Card>

        {/* 2. Total Expenses */}
        <Card className="hover-glow border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-rose-950/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Expenses</span>
              <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <ArrowDownRight className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-100 tracking-tight">
              {formatCurrency(kpis.total_expenses)}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-rose-400 mt-2 font-medium">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>Operational & Cloud Outflows</span>
            </div>
          </CardContent>
        </Card>

        {/* 3. Net Profit */}
        <Card className="hover-glow border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-emerald-950/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Net Profit</span>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <DollarSign className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-emerald-400 tracking-tight">
              {formatCurrency(kpis.net_profit)}
            </div>
            <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
              <span>Operating Margin</span>
              <span className="font-semibold text-emerald-400">{formatPercent(kpis.profit_margin_pct)}</span>
            </div>
          </CardContent>
        </Card>

        {/* 4. Monthly Budget & Used */}
        <Card className="hover-glow border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Budget Allocated</span>
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <PieIcon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-100 tracking-tight">
              {formatCurrency(kpis.monthly_budget)}
            </div>
            <div className="space-y-1.5 mt-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Used ({formatPercent(kpis.budget_used_pct)})</span>
                <span className="font-medium text-slate-200">{formatCurrency(kpis.budget_used)}</span>
              </div>
              <Progress value={kpis.budget_used_pct} variant={kpis.budget_used_pct > 85 ? 'rose' : 'default'} size="sm" />
            </div>
          </CardContent>
        </Card>

        {/* 5. Budget Remaining */}
        <Card className="hover-glow border-slate-800 bg-slate-900/80">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Budget Remaining</span>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-100 tracking-tight">
              {formatCurrency(kpis.budget_remaining)}
            </div>
            <p className="text-xs text-slate-400 mt-2">Unspent FY 2026 funds</p>
          </CardContent>
        </Card>

        {/* 6. Potential Savings (SaaS Waste) */}
        <Card className="hover-glow border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900/90 to-amber-950/20">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Potential Savings</span>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-amber-400 tracking-tight">
              {formatCurrency(kpis.potential_savings)}<span className="text-xs font-normal text-slate-400">/mo</span>
            </div>
            <p className="text-xs text-amber-400/80 mt-2">Identified unused SaaS seats</p>
          </CardContent>
        </Card>

        {/* 7. Open Financial Alerts */}
        <Card className="hover-glow border-slate-800 bg-slate-900/80">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Open Alerts</span>
              <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-rose-400 tracking-tight">
              {kpis.open_alerts_count}
            </div>
            <p className="text-xs text-slate-400 mt-2">Cost variance & renewal flags</p>
          </CardContent>
        </Card>

        {/* 8. Active Vendors & Subs */}
        <Card className="hover-glow border-slate-800 bg-slate-900/80">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Vendor Governance</span>
              <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
                <Repeat className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-100 tracking-tight">
              {kpis.active_subscriptions_count} <span className="text-sm font-normal text-slate-400">Subs</span>
            </div>
            <p className="text-xs text-slate-400 mt-2">{kpis.total_vendors_count} Contracted Vendors</p>
          </CardContent>
        </Card>
      </div>

      {/* Chart Row 1: Revenue vs Expenses & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue vs Expenses (Bar/Line) */}
        <Card className="lg:col-span-2 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-slate-100 flex items-center justify-between">
              <span>Revenue vs. Expenses (Monthly Inflow/Outflow)</span>
              <span className="text-xs font-normal text-slate-400">USD Aggregated</span>
            </CardTitle>
            <CardDescription>Monthly comparison of gross revenues against operating expenses</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.revenue_vs_expenses} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="revenue" name="Revenue" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="expenses" name="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Expense Categories (Pie/Donut) */}
        <Card className="border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-slate-100">Expense by Category</CardTitle>
            <CardDescription>Share of operating expenditures across company departments</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.expense_categories}
                    dataKey="amount"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {charts.expense_categories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || '#6366f1'} />
                    ))}
                  </Pie>
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Category legends preview */}
            <div className="space-y-1.5 mt-2 max-h-28 overflow-y-auto pr-1">
              {charts.expense_categories.slice(0, 5).map((cat) => (
                <div key={cat.category_name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                    <span className="text-slate-300 truncate max-w-[130px]">{cat.category_name}</span>
                  </div>
                  <span className="font-semibold text-slate-200">{formatCurrency(cat.amount)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart Row 2: Department Spending & Monthly Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Spending vs Allocated Budget */}
        <Card className="border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-slate-100">Department Spending vs. Budget</CardTitle>
            <CardDescription>Actual expenditures compared to allocated department budgets</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.department_spending} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="department_name" stroke="#64748b" tick={{ fontSize: 10 }} interval={0} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="budget_amount" name="Budget" fill="#334155" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="spent_amount" name="Actual Spend" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Monthly Cumulative Expense Trend */}
        <Card className="border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-slate-100">Monthly Expense Trend</CardTitle>
            <CardDescription>Expenditure velocity and cumulative cash burn analysis</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={charts.monthly_expense_trend} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    name="Monthly Expense"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#expenseGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section: Active Cost Alerts & Budget Health Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Cost Alerts */}
        <Card className="lg:col-span-2 border-slate-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Active Cost Governance Alerts
                </CardTitle>
                <CardDescription>Triggered automated threshold warnings and spend anomalies</CardDescription>
              </div>
              <Badge variant="warning">{alerts.length} Active</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.slice(0, 4).map((alert) => {
              const colorInfo = getAlertSeverityColor(alert.severity);
              return (
                <div
                  key={alert.id}
                  className={`p-4 rounded-xl border ${colorInfo.border} ${colorInfo.bg} flex items-start justify-between gap-4 transition-all`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100 text-xs">{alert.title}</span>
                      <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-300">
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 shrink-0">Open</span>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Budget Threshold Overview */}
        <Card className="border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-slate-100">Budget Threshold Rule Matrix</CardTitle>
            <CardDescription>Automated threshold categorization rules</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 flex items-center justify-between">
              <div>
                <div className="font-semibold text-emerald-400">SAFE</div>
                <div className="text-slate-400 text-[11px]">&lt; 70% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            </div>

            <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/10 flex items-center justify-between">
              <div>
                <div className="font-semibold text-amber-400">WARNING</div>
                <div className="text-slate-400 text-[11px]">70% – 85% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            </div>

            <div className="p-3 rounded-lg border border-orange-500/20 bg-orange-500/10 flex items-center justify-between">
              <div>
                <div className="font-semibold text-orange-400">CRITICAL</div>
                <div className="text-slate-400 text-[11px]">85% – 100% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            </div>

            <div className="p-3 rounded-lg border border-rose-500/20 bg-rose-500/10 flex items-center justify-between">
              <div>
                <div className="font-semibold text-rose-400">EXCEEDED</div>
                <div className="text-slate-400 text-[11px]">&gt; 100% Budget Overspent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
