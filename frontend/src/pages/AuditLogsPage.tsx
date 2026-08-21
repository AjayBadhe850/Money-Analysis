import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, User, Clock, ArrowRight } from 'lucide-react';
import { auditService } from '../services/audit.service';
import { AuditLog } from '../types';
import { formatDate } from '../utils/formatters';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      setIsLoading(true);
      try {
        const data = await auditService.getLogs(100, 0);
        setLogs(data);
      } catch (err) {
        console.error('Failed to load audit logs:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getActionBadge = (action: string) => {
    if (action.includes('CREATE') || action.includes('REGISTER')) {
      return <Badge variant="success">{action}</Badge>;
    }
    if (action.includes('UPDATE')) {
      return <Badge variant="default">{action}</Badge>;
    }
    if (action.includes('DELETE')) {
      return <Badge variant="destructive">{action}</Badge>;
    }
    if (action.includes('IMPORT')) {
      return <Badge variant="cyan">{action}</Badge>;
    }
    return <Badge variant="secondary">{action}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Enterprise Audit Log & Activity Trail
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Immutable event ledger tracking transactions, budget alterations, security sessions, and administrative modifications
        </p>
      </div>

      {/* Logs Table */}
      <Card className="border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Timestamp</th>
                <th className="px-4 py-3.5">Actor / User</th>
                <th className="px-4 py-3.5">Action</th>
                <th className="px-4 py-3.5">Target Entity</th>
                <th className="px-4 py-3.5">Event Details</th>
                <th className="px-4 py-3.5">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={6} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No audit logs recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-slate-200 whitespace-nowrap">
                      <div className="font-semibold">{log.user_name || 'System Auto-Daemon'}</div>
                      {log.user_email && <div className="text-[10px] text-slate-500">{log.user_email}</div>}
                    </td>
                    <td className="px-4 py-3">
                      {getActionBadge(log.action)}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-300">
                      {log.entity} {log.entity_id ? `(#${log.entity_id})` : ''}
                    </td>
                    <td className="px-4 py-3 text-slate-300 max-w-sm leading-relaxed">
                      {log.details || '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
