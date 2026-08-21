import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Filter,
  Eye,
  Check,
  X,
  Search,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import { AnomalyItem } from '../types';
import { formatCurrency, formatDate, getAlertSeverityColor } from '../utils/formatters';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Skeleton } from '../components/ui/Skeleton';

export const AnomaliesPage: React.FC = () => {
  const { showToast } = useToast();

  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [severityFilter, setSeverityFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchAnomalies = async () => {
    setIsLoading(true);
    try {
      const list = await aiService.getAnomalies();
      setAnomalies(list);
    } catch (err) {
      console.error('Failed to load anomalies:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const handleTriggerScan = async () => {
    setIsScanning(true);
    try {
      const res = await aiService.scanAnomalies(0.08);
      showToast('success', 'Isolation Forest Scan Complete', `Scanned ${res.scanned_count} transactions. Detected ${res.anomalies_detected} anomalies.`);
      fetchAnomalies();
    } catch (err) {
      showToast('error', 'Scan Error', 'Failed to run Isolation Forest scan.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleUpdateStatus = async (id: number, status: string) => {
    try {
      await aiService.updateAnomalyStatus(id, status);
      showToast('success', 'Status Updated', `Anomaly marked as ${status}.`);
      fetchAnomalies();
    } catch (err) {
      showToast('error', 'Error', 'Failed to update anomaly status.');
    }
  };

  const filteredAnomalies = anomalies.filter((a) => {
    const matchesSeverity = !severityFilter || a.severity === severityFilter;
    const matchesSearch =
      !search ||
      (a.transaction_description && a.transaction_description.toLowerCase().includes(search.toLowerCase())) ||
      (a.vendor_name && a.vendor_name.toLowerCase().includes(search.toLowerCase())) ||
      a.explanation.toLowerCase().includes(search.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Isolation Forest Anomaly Radar
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Machine-learning outlier detector scoring transaction variance, off-cycle payments, and vendor spending spikes
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={handleTriggerScan}
          isLoading={isScanning}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Run Isolation Forest Scan
        </Button>
      </div>

      {/* Filter Ribbon */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search anomalies by description or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            options={[
              { label: 'All Severities', value: '' },
              { label: 'CRITICAL Only', value: 'CRITICAL' },
              { label: 'HIGH Only', value: 'HIGH' },
              { label: 'MEDIUM Only', value: 'MEDIUM' },
              { label: 'LOW Only', value: 'LOW' },
            ]}
          />
        </div>
      </div>

      {/* Anomalies Table */}
      <Card className="border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Tx Date</th>
                <th className="px-4 py-3.5">Vendor / Description</th>
                <th className="px-4 py-3.5 text-right">Amount</th>
                <th className="px-4 py-3.5 text-center">Anomaly Score</th>
                <th className="px-4 py-3.5">Severity</th>
                <th className="px-4 py-3.5">Detected Reasons</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : filteredAnomalies.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-400">
                    No statistical anomalies matching current criteria.
                  </td>
                </tr>
              ) : (
                filteredAnomalies.map((anom) => {
                  const severityColor = getAlertSeverityColor(anom.severity as any);
                  return (
                    <tr key={anom.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 font-mono text-slate-400 whitespace-nowrap">
                        {anom.transaction_date ? formatDate(anom.transaction_date) : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-100">{anom.vendor_name || 'Vendor'}</div>
                        <div className="text-[10px] text-slate-400">{anom.transaction_description}</div>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-slate-100">
                        {anom.transaction_amount ? formatCurrency(anom.transaction_amount) : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                          {anom.anomaly_score}/100
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase ${severityColor.bg} ${severityColor.text} ${severityColor.border}`}
                        >
                          {anom.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-sm text-slate-300">
                        <div className="space-y-1">
                          {anom.reasons && anom.reasons.length > 0 ? (
                            anom.reasons.map((r, i) => (
                              <div key={i} className="text-[11px] text-slate-300 flex items-start gap-1">
                                <span className="text-amber-400">•</span> {r}
                              </div>
                            ))
                          ) : (
                            <span className="text-slate-400">{anom.explanation}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Badge variant={anom.status === 'CONFIRMED' ? 'destructive' : anom.status === 'RESOLVED' ? 'success' : 'warning'}>
                          {anom.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                          {anom.status !== 'CONFIRMED' && (
                            <button
                              onClick={() => handleUpdateStatus(anom.id, 'CONFIRMED')}
                              className="p-1 rounded text-slate-400 hover:text-rose-400"
                              title="Confirm Issue"
                            >
                              <AlertTriangle className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {anom.status !== 'RESOLVED' && (
                            <button
                              onClick={() => handleUpdateStatus(anom.id, 'RESOLVED')}
                              className="p-1 rounded text-slate-400 hover:text-emerald-400"
                              title="Resolve"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {anom.status !== 'FALSE_POSITIVE' && (
                            <button
                              onClick={() => handleUpdateStatus(anom.id, 'FALSE_POSITIVE')}
                              className="p-1 rounded text-slate-400 hover:text-slate-200"
                              title="Mark False Positive"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
