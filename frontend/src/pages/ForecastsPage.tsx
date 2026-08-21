import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  AlertTriangle,
  Sparkles,
  Layers,
  ArrowUpRight,
  ShieldAlert,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts';
import { aiService } from '../services/ai.service';
import { ForecastResponse } from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Select } from '../components/ui/Select';
import { Skeleton } from '../components/ui/Skeleton';

export const ForecastsPage: React.FC = () => {
  const [horizon, setHorizon] = useState<number>(90);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchForecast = async () => {
    setIsLoading(true);
    try {
      const res = await aiService.generateForecast(horizon);
      setData(res);
    } catch (err) {
      console.error('Failed to load forecast:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, [horizon]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Time-Series Expenditure Forecasting
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Machine-learning regression forecasting expenditure trajectory, confidence intervals, and budget burn stress
          </p>
        </div>
        <div className="w-48">
          <Select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            options={[
              { label: '30-Day Outlook', value: 30 },
              { label: '90-Day (Quarterly)', value: 90 },
              { label: '180-Day (Half Year)', value: 180 },
              { label: '365-Day (Annual)', value: 365 },
            ]}
          />
        </div>
      </div>

      {/* KPI Ribbon */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Projected Period Spend</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {formatCurrency(data.total_projected_spend)}
            </div>
            <div className="text-[11px] text-indigo-400 mt-1">Over {data.horizon_days} days forward</div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Historical Growth Rate</div>
            <div className={`text-2xl font-bold mt-1 ${data.historical_growth_rate > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {data.historical_growth_rate > 0 ? '+' : ''}{data.historical_growth_rate}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Month-over-month trajectory</div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Trend Trajectory</div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={data.trend === 'INCREASING' ? 'destructive' : data.trend === 'DECREASING' ? 'success' : 'secondary'}>
                {data.trend}
              </Badge>
              <span className="text-xs text-slate-400 font-semibold">{data.confidence_score * 100}% Confidence</span>
            </div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">ML Model Engine</div>
            <div className="text-sm font-bold text-cyan-400 mt-1 truncate">{data.model_type}</div>
            <div className="text-[11px] text-slate-400 mt-1">95% Uncertainty Bands</div>
          </Card>
        </div>
      )}

      {/* Forecast Chart */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100">Projected Expense Velocity & Confidence Bands</h3>
            <p className="text-xs text-slate-400">Mean forecast (indigo) bounded by lower and upper 95% statistical confidence limits (slate area)</p>
          </div>
        </div>

        <div className="h-80 w-full pt-4">
          {isLoading ? (
            <Skeleton className="h-full w-full rounded-xl" />
          ) : !data || data.series.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              No forecast points available.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.series}>
                <defs>
                  <linearGradient id="forecastArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="period" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '0.75rem',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                  formatter={(value: any) => [formatCurrency(Number(value)), '']}
                />
                <Area type="monotone" dataKey="upper_bound" stroke="none" fill="#6366F1" fillOpacity={0.1} name="Upper 95% Band" />
                <Area type="monotone" dataKey="lower_bound" stroke="none" fill="#0f172a" fillOpacity={1.0} name="Lower 95% Band" />
                <Line type="monotone" dataKey="predicted_amount" stroke="#6366F1" strokeWidth={3} dot={{ r: 4, fill: '#818cf8' }} name="Projected Spend" />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
      </Card>

      {/* Projected Budget Warnings */}
      {data && data.projected_budget_problems && data.projected_budget_problems.length > 0 && (
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Projected Fiscal Stress Warnings ({data.projected_budget_problems.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.projected_budget_problems.map((prob, idx) => (
              <Card key={idx} className="p-4 border-amber-500/30 bg-amber-500/5 flex items-start gap-3">
                <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 shrink-0">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div className="space-y-1">
                  <div className="font-bold text-slate-100 text-xs">{prob.risk}</div>
                  <p className="text-xs text-slate-300 leading-relaxed">{prob.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
