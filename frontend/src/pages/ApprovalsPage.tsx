import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  AlertTriangle,
  ArrowRight,
  Filter,
  User,
} from 'lucide-react';
import { aiService } from '../services/ai.service';
import { ApprovalResponse } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';

export const ApprovalsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [approvals, setApprovals] = useState<ApprovalResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [isLoading, setIsLoading] = useState(true);

  const [activeReq, setActiveReq] = useState<ApprovalResponse | null>(null);
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchApprovals = async () => {
    setIsLoading(true);
    try {
      const list = await aiService.getApprovals(statusFilter || undefined);
      setApprovals(list);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [statusFilter]);

  const handleActionConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeReq || !actionType) return;
    setIsSubmitting(true);
    try {
      if (actionType === 'APPROVE') {
        await aiService.approveRequest(activeReq.id, actionNotes || undefined);
        showToast('success', 'Action Approved & Executed', `Request #${activeReq.id} approved.`);
      } else {
        await aiService.rejectRequest(activeReq.id, actionNotes || undefined);
        showToast('info', 'Request Rejected', `Request #${activeReq.id} marked as rejected.`);
      }
      setActiveReq(null);
      setActionType(null);
      setActionNotes('');
      fetchApprovals();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to process approval action');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canApprove = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Human-in-the-Loop Governance & Approvals
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Safeguarded financial authorization gateway ensuring autonomous agent recommendations undergo human review before execution
          </p>
        </div>
        <div className="w-48">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={[
              { label: 'PENDING Only', value: 'PENDING' },
              { label: 'APPROVED Only', value: 'APPROVED' },
              { label: 'EXECUTED Only', value: 'EXECUTED' },
              { label: 'REJECTED Only', value: 'REJECTED' },
              { label: 'All Requests', value: '' },
            ]}
          />
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {isLoading ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-36 rounded-xl" />)
        ) : approvals.length === 0 ? (
          <Card className="p-8 text-center border-slate-800 text-slate-400 text-xs">
            No approval requests matching status filter: {statusFilter || 'All'}.
          </Card>
        ) : (
          approvals.map((req) => (
            <Card key={req.id} className="hover-glow border-slate-800 p-5 flex flex-col md:flex-row md:items-center justify-between gap-5">
              <div className="space-y-2 max-w-2xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-slate-100 text-sm">{req.title}</span>
                  <Badge variant={req.status === 'APPROVED' || req.status === 'EXECUTED' ? 'success' : req.status === 'REJECTED' ? 'destructive' : 'warning'}>
                    {req.status}
                  </Badge>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase">
                    {req.request_type}
                  </span>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    +{formatCurrency(req.impact_savings_monthly)}/mo savings
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{req.details}</p>

                <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                  <span>Risk: <strong className="text-slate-200">{req.risk_level}</strong></span>
                  <span>•</span>
                  <span>Submitted: {formatDate(req.created_at)}</span>
                  {req.response_notes && (
                    <>
                      <span>•</span>
                      <span>Notes: <em className="text-slate-300">"{req.response_notes}"</em></span>
                    </>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              {req.status === 'PENDING' && canApprove && (
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setActiveReq(req);
                      setActionType('REJECT');
                      setActionNotes('');
                    }}
                    leftIcon={<XCircle className="w-3.5 h-3.5 text-rose-400" />}
                  >
                    Reject
                  </Button>
                  <Button
                    variant="emerald"
                    size="sm"
                    onClick={() => {
                      setActiveReq(req);
                      setActionType('APPROVE');
                      setActionNotes('Approved by Finance Controller');
                    }}
                    leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                  >
                    Approve & Execute
                  </Button>
                </div>
              )}
            </Card>
          ))
        )}
      </div>

      {/* Confirmation Modal */}
      <Modal
        isOpen={Boolean(activeReq && actionType)}
        onClose={() => {
          setActiveReq(null);
          setActionType(null);
        }}
        title={actionType === 'APPROVE' ? 'Approve Optimization Action' : 'Reject Request'}
      >
        <form onSubmit={handleActionConfirm} className="space-y-4 text-xs">
          <p className="text-slate-300">
            {actionType === 'APPROVE'
              ? `You are authorizing "${activeReq?.title}". This will trigger non-destructive downstream optimization actions yielding ${formatCurrency(activeReq?.impact_savings_monthly || 0)}/mo in savings.`
              : `Are you sure you want to reject "${activeReq?.title}"?`}
          </p>

          <Input
            label="Decision Notes (Audit Trail)"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="e.g. Reviewed with IT Procurement, proceeding."
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button
              variant="secondary"
              size="sm"
              type="button"
              onClick={() => {
                setActiveReq(null);
                setActionType(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant={actionType === 'APPROVE' ? 'emerald' : 'destructive'}
              size="sm"
              type="submit"
              isLoading={isSubmitting}
            >
              {actionType === 'APPROVE' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
