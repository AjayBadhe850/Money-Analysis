import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart as PieIcon,
  AlertTriangle,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
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
      <div className="rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-xl backdrop-blur-md text-xs font-sans">
        <p className="font-bold text-slate-800 mb-1.5">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={`item-${index}`} className="flex items-center gap-2 text-slate-600 py-0.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
            <span className="capitalize text-slate-500 font-medium">{entry.name}:</span>
            <span className="font-bold text-slate-900">{formatCurrency(entry.value)}</span>
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
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-2xl" />
          <Skeleton className="h-80 rounded-2xl" />
        </div>
      </div>
    );
  }

  const { kpis, charts } = data;

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Executive Finance Control
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 font-semibold">
              Live Production
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time financial performance, cash flow dynamics, and autonomous budget control
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {/* Currency Switcher */}
          <div className="flex items-center bg-white p-1 rounded-2xl border border-slate-200 text-xs shadow-sm">
            {(['USD', 'INR', 'EUR'] as const).map((curr) => (
              <button
                key={curr}
                onClick={() => setCurrency(curr)}
                className={`px-3 py-1 rounded-xl font-bold text-xs transition-all cursor-pointer ${
                  currency === curr
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
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

      {/* AI Real-time Insights Panel */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60 shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Marketing Budget Surge</span>
            <span className="text-[11px] text-slate-500">Marketing is pacing 12% above Q3 ceiling ({formatCustomCurrency(18200)} over).</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-xl bg-blue-50 text-blue-600 border border-blue-200/60 shrink-0">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900 block">SaaS License Reclamation</span>
            <span className="text-[11px] text-slate-500">18 unused Salesforce seats cost {formatCustomCurrency(2700)}/mo in Sales.</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-xl bg-cyan-50 text-cyan-600 border border-cyan-200/60 shrink-0">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Vendor Terms Arbitrage</span>
            <span className="text-[11px] text-slate-500">AWS on-demand pricing is 38% above 1-yr Compute Savings Plan.</span>
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-xl bg-purple-50 text-purple-600 border border-purple-200/60 shrink-0">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Expenditure Velocity</span>
            <span className="text-[11px] text-slate-500">90-day trajectory projects operating costs rising by 8.2%.</span>
          </div>
        </div>
      </div>

      {/* AI Cost Efficiency Score Banner */}
      {aiScore && (
        <Card className="hover-glow border-blue-200/70 bg-gradient-to-r from-blue-50/80 via-white to-cyan-50/60 p-5 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 text-white flex flex-col items-center justify-center shrink-0 shadow-md shadow-blue-500/20">
                <span className="text-2xl font-black">{aiScore.overall_score}</span>
                <span className="text-[9px] font-bold uppercase opacity-90">Score / 100</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900 text-sm">AI Cost Efficiency Rating</h3>
                  <Badge variant="purple">Grade: {aiScore.grade}</Badge>
                </div>
                <p className="text-xs text-slate-500">
                  Comprehensive 5-pillar financial health index evaluated continuously across ledgers and contracts.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
                <span className="text-[10px] text-slate-500 block">Budget Control</span>
                <span className="font-bold text-slate-900 mt-0.5 block">{aiScore.components.budget_control.score}/25</span>
                <span className="text-[10px] text-emerald-600 font-semibold">{aiScore.components.budget_control.metric}</span>
              </div>
              <div className="p-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
                <span className="text-[10px] text-slate-500 block">Vendor Terms</span>
                <span className="font-bold text-slate-900 mt-0.5 block">{aiScore.components.vendor_efficiency.score}/25</span>
                <span className="text-[10px] text-blue-600 font-semibold">{aiScore.components.vendor_efficiency.metric}</span>
              </div>
              <div className="p-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
                <span className="text-[10px] text-slate-500 block">SaaS Utilization</span>
                <span className="font-bold text-slate-900 mt-0.5 block">{aiScore.components.subscription_utilization.score}/25</span>
                <span className="text-[10px] text-cyan-600 font-semibold">{aiScore.components.subscription_utilization.metric}</span>
              </div>
              <div className="p-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
                <span className="text-[10px] text-slate-500 block">Stability</span>
                <span className="font-bold text-slate-900 mt-0.5 block">{aiScore.components.expense_stability.score}/15</span>
                <span className="text-[10px] text-purple-600 font-semibold">{aiScore.components.expense_stability.metric}</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 8 Metric KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Total Revenue (Styled matching Poster widget) */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Revenue</span>
              <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20">
                <DollarSign className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {formatCurrency(kpis.total_revenue)}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-emerald-600 mt-2 font-semibold">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>↑ 12.4% vs last period</span>
            </div>
          </CardContent>
        </Card>

        {/* 2. Total Expenses */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Expenses</span>
              <div className="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-200/60">
                <ArrowDownRight className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {formatCurrency(kpis.total_expenses)}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-rose-600 mt-2 font-medium">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>Operational & Cloud Outflows</span>
            </div>
          </CardContent>
        </Card>

        {/* 3. Net Profit (Styled matching Poster widget) */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Net Profit</span>
              <div className="w-8 h-8 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-md shadow-purple-500/20">
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {formatCurrency(kpis.net_profit)}
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 mt-2 font-semibold">
              <span>Operating Margin</span>
              <span className="text-purple-600">↑ {formatPercent(kpis.profit_margin_pct)}</span>
            </div>
          </CardContent>
        </Card>

        {/* 4. Cash Flow & Budget */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Cash Flow</span>
              <div className="p-2 rounded-xl bg-blue-50 text-blue-600 border border-blue-200/60">
                <PieIcon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {formatCurrency(kpis.monthly_budget)}
            </div>
            <div className="space-y-1.5 mt-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Used ({formatPercent(kpis.budget_used_pct)})</span>
                <span className="font-semibold text-slate-800">{formatCurrency(kpis.budget_used)}</span>
              </div>
              <Progress value={kpis.budget_used_pct} variant={kpis.budget_used_pct > 85 ? 'rose' : 'default'} size="sm" />
            </div>
          </CardContent>
        </Card>

        {/* 5. Budget Remaining */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Budget Remaining</span>
              <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200/60">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {formatCurrency(kpis.budget_remaining)}
            </div>
            <p className="text-xs text-slate-500 mt-2 font-medium">Unspent FY 2026 funds</p>
          </CardContent>
        </Card>

        {/* 6. Potential Savings (SaaS Waste) */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Potential Savings</span>
              <div className="p-2 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-amber-600 tracking-tight">
              {formatCurrency(kpis.potential_savings)}<span className="text-xs font-normal text-slate-400">/mo</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">Identified unused SaaS seats</p>
          </CardContent>
        </Card>

        {/* 7. Open Financial Alerts */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Open Alerts</span>
              <div className="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-200/60">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-rose-600 tracking-tight">
              {kpis.open_alerts_count}
            </div>
            <p className="text-xs text-slate-500 mt-2">Cost variance & renewal flags</p>
          </CardContent>
        </Card>

        {/* 8. Active Vendors & Subs */}
        <Card className="hover-glow border-slate-200/90 bg-white shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Vendor Governance</span>
              <div className="p-2 rounded-xl bg-cyan-50 text-cyan-600 border border-cyan-200/60">
                <Repeat className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight">
              {kpis.active_subscriptions_count} <span className="text-sm font-normal text-slate-500">Subs</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">{kpis.total_vendors_count} Contracted Vendors</p>
          </CardContent>
        </Card>
      </div>

      {/* Chart Row 1: Revenue vs Expenses & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue vs Expenses (Bar/Line) */}
        <Card className="lg:col-span-2 border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center justify-between">
              <span>Revenue vs. Expenses (Monthly Inflow/Outflow)</span>
              <span className="text-xs font-normal text-slate-500">USD Aggregated</span>
            </CardTitle>
            <CardDescription>Monthly comparison of gross revenues against operating expenses</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.revenue_vs_expenses} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="revenue" name="Revenue" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="expenses" name="Expenses" fill="#f43f5e" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Expense Categories (Pie/Donut matching Poster design) */}
        <Card className="border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Expenses by Category</CardTitle>
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
                      <Cell key={`cell-${index}`} fill={entry.color || '#3b82f6'} />
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
                    <span className="text-slate-700 truncate max-w-[130px] font-medium">{cat.category_name}</span>
                  </div>
                  <span className="font-bold text-slate-900">{formatCurrency(cat.amount)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart Row 2: Department Spending & Monthly Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Spending vs Allocated Budget */}
        <Card className="border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Department Spending vs. Budget</CardTitle>
            <CardDescription>Actual expenditures compared to allocated department budgets</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.department_spending} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="department_name" stroke="#94a3b8" tick={{ fontSize: 10 }} interval={0} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Bar dataKey="budget_amount" name="Budget" fill="#cbd5e1" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="spent_amount" name="Actual Spend" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Monthly Cumulative Expense Trend */}
        <Card className="border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Monthly Expense Trend</CardTitle>
            <CardDescription>Expenditure velocity and cumulative cash burn analysis</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={charts.monthly_expense_trend} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
                  <RechartsTooltip content={<CustomDashboardTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    name="Monthly Expense"
                    stroke="#2563eb"
                    strokeWidth={2.5}
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
        <Card className="lg:col-span-2 border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
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
                  className={`p-4 rounded-2xl border ${colorInfo.border} ${colorInfo.bg} flex items-start justify-between gap-4 transition-all shadow-sm`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-xs">{alert.title}</span>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-white text-slate-700 shadow-sm border border-slate-200/60">
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{alert.message}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 font-semibold shrink-0">Open</span>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Budget Threshold Overview */}
        <Card className="border-slate-200/90 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Budget Threshold Rule Matrix</CardTitle>
            <CardDescription>Automated threshold categorization rules</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="p-3 rounded-2xl border border-emerald-200 bg-emerald-50/70 flex items-center justify-between">
              <div>
                <div className="font-bold text-emerald-800">SAFE</div>
                <div className="text-slate-600 text-[11px]">&lt; 70% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            </div>

            <div className="p-3 rounded-2xl border border-amber-200 bg-amber-50/70 flex items-center justify-between">
              <div>
                <div className="font-bold text-amber-800">WARNING</div>
                <div className="text-slate-600 text-[11px]">70% – 85% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            </div>

            <div className="p-3 rounded-2xl border border-orange-200 bg-orange-50/70 flex items-center justify-between">
              <div>
                <div className="font-bold text-orange-800">CRITICAL</div>
                <div className="text-slate-600 text-[11px]">85% – 100% Allocated Spent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            </div>

            <div className="p-3 rounded-2xl border border-rose-200 bg-rose-50/70 flex items-center justify-between">
              <div>
                <div className="font-bold text-rose-800">EXCEEDED</div>
                <div className="text-slate-600 text-[11px]">&gt; 100% Budget Overspent</div>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

