import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, CheckCircle2, Sparkles, ShieldAlert, ArrowUpRight } from 'lucide-react';
import { dashboardService } from '../services/dashboard.service';
import { CostAlert, CostRecommendation } from '../types';
import { formatCurrency, formatDate, getAlertSeverityColor } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';

export const AlertsPage: React.FC = () => {
  const { showToast } = useToast();
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [recommendations, setRecommendations] = useState<CostRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlertsData = async () => {
    setIsLoading(true);
    try {
      const [al, rec] = await Promise.all([
        dashboardService.getAlerts(),
        dashboardService.getRecommendations(),
      ]);
      setAlerts(al);
      setRecommendations(rec);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertsData();
  }, []);

  const handleUpdateStatus = async (alertId: number, newStatus: string) => {
    try {
      await dashboardService.updateAlertStatus(alertId, newStatus);
      showToast('success', 'Alert Updated', `Alert status marked as ${newStatus}`);
      fetchAlertsData();
    } catch (err) {
      showToast('error', 'Error', 'Failed to update alert');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Financial Alerts & Cost Optimization Triggers
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Automated threshold triggers, vendor maturity deadlines, and deterministic cost reduction opportunities
        </p>
      </div>

      {/* Alerts Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Bell className="w-4 h-4 text-amber-400" />
            Active Cost Variance Alerts ({alerts.length})
          </h2>
        </div>

        <div className="space-y-3">
          {isLoading ? (
            [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          ) : alerts.length === 0 ? (
            <Card className="p-8 text-center border-slate-800">
              <p className="text-slate-400 text-xs">No active cost alerts currently triggered.</p>
            </Card>
          ) : (
            alerts.map((alert) => {
              const colorInfo = getAlertSeverityColor(alert.severity);
              return (
                <Card
                  key={alert.id}
                  className={`border ${colorInfo.border} ${colorInfo.bg} p-5 flex flex-col md:flex-row md:items-center justify-between gap-4`}
                >
                  <div className="space-y-1.5 max-w-3xl">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-100 text-sm">{alert.title}</span>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-900/90 text-slate-200">
                        {alert.severity}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        • {formatDate(alert.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {alert.status === 'OPEN' && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleUpdateStatus(alert.id, 'ACKNOWLEDGED')}
                      >
                        Acknowledge
                      </Button>
                    )}
                    {alert.status !== 'RESOLVED' && (
                      <Button
                        variant="emerald"
                        size="sm"
                        onClick={() => handleUpdateStatus(alert.id, 'RESOLVED')}
                        leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                      >
                        Resolve
                      </Button>
                    )}
                    {alert.status === 'RESOLVED' && (
                      <Badge variant="success">RESOLVED</Badge>
                    )}
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </div>

      {/* Cost Recommendations Section */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Deterministic Cost Reduction Opportunities ({recommendations.length})
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {isLoading ? (
            [...Array(4)].map((_, i) => <Skeleton key={i} className="h-36 rounded-xl" />)
          ) : (
            recommendations.map((rec) => (
              <Card key={rec.id} className="hover-glow border-slate-800 p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                      {rec.category}
                    </span>
                    <span className="font-bold text-sm text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                      Save {formatCurrency(rec.potential_monthly_savings)}/mo
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-100 text-sm mb-1">{rec.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{rec.description}</p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500">Status: <strong>{rec.status}</strong></span>
                  <span className="text-xs text-indigo-400 font-medium">Stage 2 Auto-Apply Ready</span>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
