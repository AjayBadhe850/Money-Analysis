import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Download,
  Printer,
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Zap,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { reportService, AutomationStatusResponse } from '../services/report.service';
import { formatCurrency, formatPercent, formatDate } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';

export const ReportsPage: React.FC = () => {
  const { showToast } = useToast();

  const [reportData, setReportData] = useState<any>(null);
  const [automationStatus, setAutomationStatus] = useState<AutomationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const fetchReportData = async () => {
    setIsLoading(true);
    try {
      const [rep, auto] = await Promise.all([
        reportService.getMonthlyReport(),
        reportService.getAutomationStatus().catch(() => null),
      ]);
      setReportData(rep);
      setAutomationStatus(auto);
    } catch (err) {
      console.error('Failed to load report data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, []);

  const handleDownloadPdf = async () => {
    setIsDownloadingPdf(true);
    try {
      await reportService.downloadMonthlyPdf();
      showToast('success', 'PDF Generated', 'Monthly Financial Controller Report downloaded.');
    } catch (err) {
      showToast('error', 'Export Error', 'Failed to generate PDF report.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (isLoading || !reportData) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-44 w-full rounded-xl" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    );
  }

  const { kpis, charts, savings_opportunities, anomalies, forecast, approved_actions } = reportData;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Monthly Financial Controller Report
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Verified financial statement, departmental budget burn, and autonomous multi-agent recommendations for {reportData.report_period}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            leftIcon={<Printer className="w-3.5 h-3.5" />}
          >
            Print
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleDownloadPdf}
            isLoading={isDownloadingPdf}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            Download Verified PDF
          </Button>
        </div>
      </div>

      {/* Scheduled Automation Telemetry */}
      {automationStatus && (
        <Card className="border-indigo-500/20 bg-indigo-950/20 p-4 text-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <span className="font-bold text-slate-200 block">Scheduled Finance Automation (Celery Beat & Redis)</span>
                <span className="text-[11px] text-slate-400">
                  Daily Anomaly Scans: {automationStatus.tasks.daily_anomaly_scan?.last_run ? formatDate(automationStatus.tasks.daily_anomaly_scan.last_run) : 'Active Daily'} • Weekly Optimization: {automationStatus.tasks.weekly_savings_optimization?.last_run ? formatDate(automationStatus.tasks.weekly_savings_optimization.last_run) : 'Active Weekly'}
                </span>
              </div>
            </div>
            <Badge variant="success">SCHEDULER RUNNING</Badge>
          </div>
        </Card>
      )}

      {/* Executive Summary Card */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="purple">Section 1</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">Executive P&L Performance & Strategic Commentary</h2>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">
          {reportData.executive_summary}
        </p>
      </Card>

      {/* Financial Matrix Summary Table */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="cyan">Section 2</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">Executive Financial Metrics Matrix</h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Revenue</span>
            <span className="text-xl font-bold text-cyan-400 mt-1 block">{formatCurrency(kpis.total_revenue)}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Enterprise Inflow</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Total OPEX</span>
            <span className="text-xl font-bold text-rose-400 mt-1 block">{formatCurrency(kpis.total_expenses)}</span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Operating Expenses</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Net Profit</span>
            <span className="text-xl font-bold text-emerald-400 mt-1 block">{formatCurrency(kpis.net_profit)}</span>
            <span className="text-[10px] text-emerald-400 mt-0.5 block">{kpis.profit_margin_pct}% Margin</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Identified Savings</span>
            <span className="text-xl font-bold text-indigo-400 mt-1 block">+{formatCurrency(reportData.total_monthly_savings_potential)}/mo</span>
            <span className="text-[10px] text-indigo-400 mt-0.5 block">Recurring Opportunities</span>
          </div>
        </div>
      </Card>

      {/* Department Budget Breakdown */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="cyan">Section 3</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">Department Budget Allocation & Variance</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[10px] font-semibold uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-2.5">Department</th>
                <th className="px-4 py-2.5 text-right">Spent Amount</th>
                <th className="px-4 py-2.5 text-right">Allocated Budget</th>
                <th className="px-4 py-2.5 text-right">Remaining Variance</th>
                <th className="px-4 py-2.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {charts.budget_vs_actual.map((dept: any, idx: number) => {
                const varAmt = dept.allocated - dept.spent;
                const isOver = varAmt < 0;
                return (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-semibold text-slate-100">{dept.name}</td>
                    <td className="px-4 py-3 text-right text-slate-200">{formatCurrency(dept.spent)}</td>
                    <td className="px-4 py-3 text-right text-slate-400">{formatCurrency(dept.allocated)}</td>
                    <td className={`px-4 py-3 text-right font-bold ${isOver ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {formatCurrency(varAmt)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant={isOver ? 'destructive' : 'success'}>
                        {isOver ? 'OVERSPENT' : 'SAFE'}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Top Cost-Reduction Opportunities */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="success">Section 4</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            Top Multi-Agent Cost-Reduction Opportunities ({savings_opportunities.length})
          </h2>
        </div>

        <div className="space-y-3">
          {savings_opportunities.map((opp: any, idx: number) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
            >
              <div className="space-y-1 max-w-lg">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-100">{opp.title}</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                    {opp.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">{opp.description}</p>
              </div>

              <div className="text-right shrink-0">
                <div className="font-bold text-emerald-400 text-sm">+{formatCurrency(opp.estimated_monthly_saving)}/mo</div>
                <div className="text-[10px] text-slate-400">{formatCurrency(opp.estimated_annual_saving)}/yr</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Flagged Statistical Anomalies */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="destructive">Section 5</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            Flagged Statistical Anomalies & Outliers ({reportData.anomalies?.length || 0})
          </h2>
        </div>

        <div className="space-y-2.5">
          {(reportData.anomalies || []).map((anom: any, idx: number) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">{anom.transaction_description || 'Outlier Expense'}</span>
                  <Badge variant={anom.severity === 'CRITICAL' ? 'destructive' : 'warning'}>
                    {anom.severity} ({anom.anomaly_score}%)
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400">{anom.explanation}</p>
              </div>
              <div className="text-right shrink-0 font-bold text-rose-400">
                {formatCurrency(anom.transaction_amount || 0)}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 90-Day Expenditure Forecast */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="cyan">Section 6</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            90-Day Expenditure Forecast & Burn Rate Trajectory
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Projected 90-Day OPEX</span>
            <span className="text-lg font-bold text-slate-100 mt-1 block">
              {formatCurrency(reportData.forecast?.total_projected_spend || 0)}
            </span>
            <span className="text-[10px] text-cyan-400 mt-0.5 block">Trend: {reportData.forecast?.trend || 'STABLE'}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Confidence Band</span>
            <span className="text-sm font-semibold text-slate-300 mt-1 block">
              {formatCurrency(reportData.forecast?.lower_bound || 0)} - {formatCurrency(reportData.forecast?.upper_bound || 0)}
            </span>
            <span className="text-[10px] text-slate-400 mt-0.5 block">95% Prediction Interval</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Underlying ML Model</span>
            <span className="text-sm font-semibold text-slate-200 mt-1 block">Ridge Time-Series Regressor</span>
            <span className="text-[10px] text-emerald-400 mt-0.5 block">Chronological Split Validated</span>
          </div>
        </div>
      </Card>

      {/* Approved Governance Actions & Sign-Off */}
      <Card className="border-slate-800 p-6 space-y-4 bg-slate-900/60">
        <div className="border-b border-slate-800 pb-3">
          <Badge variant="purple">Section 7</Badge>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            Human-in-the-Loop Governance & Executive Sign-off
          </h2>
        </div>

        <div className="space-y-2 text-xs">
          {(reportData.approved_actions || []).length > 0 ? (
            reportData.approved_actions.map((act: any, idx: number) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-200 block">{act.title}</span>
                  <span className="text-[10px] text-slate-400">{act.type} • Status: {act.status}</span>
                </div>
                <span className="font-bold text-emerald-400">+{formatCurrency(act.impact_savings_monthly)}/mo</span>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">All recent financial optimization actions have been logged and verified in the immutable audit trail.</p>
          )}
        </div>
      </Card>
    </div>
  );
};
