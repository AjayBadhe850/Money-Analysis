import React, { useState, useEffect } from 'react';
import {
  Repeat,
  Plus,
  Edit2,
  Trash2,
  AlertTriangle,
  Sparkles,
  Calendar,
  Layers,
  ArrowDownRight,
  Zap,
} from 'lucide-react';
import { subscriptionService } from '../services/subscription.service';
import { departmentService } from '../services/department.service';
import { vendorService } from '../services/vendor.service';
import { Subscription, Department, Vendor, SubscriptionSummaryResponse } from '../types';
import { formatCurrency, formatPercent, formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { Progress } from '../components/ui/Progress';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Skeleton } from '../components/ui/Skeleton';

export const SubscriptionsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [data, setData] = useState<SubscriptionSummaryResponse | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [activeSub, setActiveSub] = useState<Subscription | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    service_name: '',
    vendor: '',
    vendor_id: '',
    department_id: '',
    monthly_cost: '',
    total_licenses: '10',
    active_licenses: '10',
    renewal_date: new Date().toISOString().split('T')[0],
  });

  const fetchSubscriptions = async () => {
    setIsLoading(true);
    try {
      const res = await subscriptionService.getSubscriptions();
      setData(res);
    } catch (err) {
      console.error('Failed to load subscriptions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [depts, vends] = await Promise.all([
          departmentService.getDepartments(),
          vendorService.getVendors(),
        ]);
        setDepartments(depts);
        setVendors(vends);
      } catch (err) {
        console.error('Failed to load metadata:', err);
      }
    };
    loadData();
    fetchSubscriptions();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await subscriptionService.createSubscription({
        service_name: formData.service_name,
        vendor: formData.vendor || undefined,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        monthly_cost: Number(formData.monthly_cost),
        total_licenses: Number(formData.total_licenses),
        active_licenses: Number(formData.active_licenses),
        renewal_date: formData.renewal_date,
      });
      showToast('success', 'Subscription Tracked', `Tracking "${formData.service_name}".`);
      setIsCreateOpen(false);
      fetchSubscriptions();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to create subscription');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSub) return;
    setIsSubmitting(true);
    try {
      await subscriptionService.updateSubscription(activeSub.id, {
        service_name: formData.service_name,
        vendor: formData.vendor || undefined,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        monthly_cost: Number(formData.monthly_cost),
        total_licenses: Number(formData.total_licenses),
        active_licenses: Number(formData.active_licenses),
        renewal_date: formData.renewal_date,
      });
      showToast('success', 'Subscription Updated', 'Seat counts and rates updated.');
      setIsEditOpen(false);
      fetchSubscriptions();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to update subscription');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeSub) return;
    setIsSubmitting(true);
    try {
      await subscriptionService.deleteSubscription(activeSub.id);
      showToast('success', 'Subscription Deleted', 'Subscription removed from tracking.');
      setIsDeleteOpen(false);
      fetchSubscriptions();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Could not delete subscription');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canManage = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            SaaS Subscriptions & License Optimization
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated seat utilization audit, renewal forecasting, and license waste identification
          </p>
        </div>
        {canManage && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setFormData({
                service_name: '',
                vendor: '',
                vendor_id: '',
                department_id: '',
                monthly_cost: '',
                total_licenses: '10',
                active_licenses: '8',
                renewal_date: new Date().toISOString().split('T')[0],
              });
              setIsCreateOpen(true);
            }}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Track Subscription
          </Button>
        )}
      </div>

      {/* Top Banner: License Waste Optimizer Summary */}
      {data && (
        <div className="p-5 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-950/40 backdrop-blur-md">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 shrink-0">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-100 text-base">Deterministic License Waste Detection</h3>
                  <Badge variant="warning">Rule-Based Active</Badge>
                </div>
                <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                  Calculated from unused enterprise software licenses (<code className="text-amber-300">Unused Seats × Per-Seat Cost</code>). Reclaiming these seats can yield immediate recurring savings.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 shrink-0 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase">Potential Monthly Waste</div>
                <div className="text-xl font-bold text-amber-400">{formatCurrency(data.potential_monthly_savings)}/mo</div>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase">Annual Recoverable</div>
                <div className="text-xl font-bold text-emerald-400">{formatCurrency(data.potential_annual_savings)}/yr</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subscriptions Table / Cards */}
      <Card className="border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Service / Software</th>
                <th className="px-4 py-3.5">Department</th>
                <th className="px-4 py-3.5 text-right">Monthly Spend</th>
                <th className="px-4 py-3.5 text-right">Annual Cost</th>
                <th className="px-4 py-3.5">License Utilization</th>
                <th className="px-4 py-3.5 text-right">Wasted Capital</th>
                <th className="px-4 py-3.5">Renewal Date</th>
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
              ) : !data || data.subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-400">
                    No subscriptions registered.
                  </td>
                </tr>
              ) : (
                data.subscriptions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-100">
                      <div>{sub.service_name}</div>
                      <div className="text-[10px] text-slate-400 font-normal">{sub.vendor || 'Direct Vendor'}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {sub.department_name || 'Global'}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-100">
                      {formatCurrency(sub.monthly_cost)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400">
                      {formatCurrency(sub.annual_cost)}
                    </td>
                    <td className="px-4 py-3 min-w-[160px]">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span>
                            <strong>{sub.active_licenses}</strong> / {sub.total_licenses} seats
                          </span>
                          <span className="font-semibold text-slate-200">
                            {formatPercent(sub.utilization_percentage)}
                          </span>
                        </div>
                        <Progress
                          value={sub.utilization_percentage}
                          variant={sub.has_waste_flag ? 'amber' : 'emerald'}
                          size="sm"
                        />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {sub.has_waste_flag ? (
                        <span className="inline-flex items-center gap-1 font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                          {formatCurrency(sub.estimated_monthly_waste)}/mo
                        </span>
                      ) : (
                        <span className="text-emerald-400 text-[11px] font-medium">100% Utilized</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-300 whitespace-nowrap">
                      {formatDate(sub.renewal_date)}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {canManage && (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => {
                              setActiveSub(sub);
                              setFormData({
                                service_name: sub.service_name,
                                vendor: sub.vendor || '',
                                vendor_id: sub.vendor_id ? String(sub.vendor_id) : '',
                                department_id: sub.department_id ? String(sub.department_id) : '',
                                monthly_cost: String(sub.monthly_cost),
                                total_licenses: String(sub.total_licenses),
                                active_licenses: String(sub.active_licenses),
                                renewal_date: sub.renewal_date,
                              });
                              setIsEditOpen(true);
                            }}
                            className="p-1 rounded text-slate-400 hover:text-indigo-400"
                            title="Edit"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => {
                              setActiveSub(sub);
                              setIsDeleteOpen(true);
                            }}
                            className="p-1 rounded text-slate-400 hover:text-rose-400"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create Subscription Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Track SaaS Subscription" maxWidth="lg">
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <Input
            label="Service / Software Name"
            value={formData.service_name}
            onChange={(e) => setFormData({ ...formData, service_name: e.target.value })}
            placeholder="e.g. Salesforce Sales Cloud Enterprise"
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Vendor"
              value={formData.vendor_id}
              onChange={(e) => {
                const v = vendors.find((vend) => String(vend.id) === e.target.value);
                setFormData({ ...formData, vendor_id: e.target.value, vendor: v ? v.name : '' });
              }}
              options={[
                { label: 'Select Vendor', value: '' },
                ...vendors.map((v) => ({ label: v.name, value: v.id })),
              ]}
            />
            <Select
              label="Department"
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
              options={[
                { label: 'Global (All Departments)', value: '' },
                ...departments.map((d) => ({ label: d.name, value: d.id })),
              ]}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Monthly Spend ($)"
              type="number"
              step="0.01"
              value={formData.monthly_cost}
              onChange={(e) => setFormData({ ...formData, monthly_cost: e.target.value })}
              placeholder="e.g. 5000"
              required
            />
            <Input
              label="Total Seats Purchased"
              type="number"
              value={formData.total_licenses}
              onChange={(e) => setFormData({ ...formData, total_licenses: e.target.value })}
              required
            />
            <Input
              label="Active In-Use Seats"
              type="number"
              value={formData.active_licenses}
              onChange={(e) => setFormData({ ...formData, active_licenses: e.target.value })}
              required
            />
          </div>

          <Input
            label="Next Contract Renewal Date"
            type="date"
            value={formData.renewal_date}
            onChange={(e) => setFormData({ ...formData, renewal_date: e.target.value })}
            required
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Save Subscription
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Edit Subscription" maxWidth="lg">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Service Name"
            value={formData.service_name}
            onChange={(e) => setFormData({ ...formData, service_name: e.target.value })}
            required
          />
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Monthly Cost ($)"
              type="number"
              step="0.01"
              value={formData.monthly_cost}
              onChange={(e) => setFormData({ ...formData, monthly_cost: e.target.value })}
              required
            />
            <Input
              label="Total Seats"
              type="number"
              value={formData.total_licenses}
              onChange={(e) => setFormData({ ...formData, total_licenses: e.target.value })}
              required
            />
            <Input
              label="Active Seats"
              type="number"
              value={formData.active_licenses}
              onChange={(e) => setFormData({ ...formData, active_licenses: e.target.value })}
              required
            />
          </div>
          <Input
            label="Renewal Date"
            type="date"
            value={formData.renewal_date}
            onChange={(e) => setFormData({ ...formData, renewal_date: e.target.value })}
            required
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Update
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Dialog */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Subscription"
        message={`Are you sure you want to stop tracking "${activeSub?.service_name}"?`}
        confirmText="Delete"
        isDestructive
        isLoading={isSubmitting}
      />
    </div>
  );
};
