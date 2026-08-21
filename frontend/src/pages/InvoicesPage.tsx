import React, { useState, useEffect } from 'react';
import {
  FileText,
  Plus,
  Edit2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Ban,
  Search,
} from 'lucide-react';
import { invoiceService } from '../services/invoice.service';
import { vendorService } from '../services/vendor.service';
import { Invoice, Vendor, InvoiceStatus, InvoiceSummaryResponse } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Skeleton } from '../components/ui/Skeleton';

export const InvoicesPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [data, setData] = useState<InvoiceSummaryResponse | null>(null);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [activeInvoice, setActiveInvoice] = useState<Invoice | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    invoice_number: '',
    vendor_id: '',
    issue_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
    amount: '',
    status: 'PENDING' as InvoiceStatus,
  });

  const fetchInvoices = async () => {
    setIsLoading(true);
    try {
      const res = await invoiceService.getInvoices(undefined, selectedStatus as InvoiceStatus || undefined);
      setData(res);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const loadVendors = async () => {
      try {
        const vList = await vendorService.getVendors();
        setVendors(vList);
      } catch (err) {
        console.error('Failed to load vendors:', err);
      }
    };
    loadVendors();
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [selectedStatus]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await invoiceService.createInvoice({
        invoice_number: formData.invoice_number,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
        issue_date: formData.issue_date,
        due_date: formData.due_date,
        amount: Number(formData.amount),
        status: formData.status,
      });
      showToast('success', 'Invoice Logged', `Invoice #${formData.invoice_number} saved.`);
      setIsCreateOpen(false);
      fetchInvoices();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to create invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeInvoice) return;
    setIsSubmitting(true);
    try {
      await invoiceService.updateInvoice(activeInvoice.id, {
        invoice_number: formData.invoice_number,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
        issue_date: formData.issue_date,
        due_date: formData.due_date,
        amount: Number(formData.amount),
        status: formData.status,
      });
      showToast('success', 'Invoice Updated', 'Invoice status and terms updated.');
      setIsEditOpen(false);
      fetchInvoices();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to update invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeInvoice) return;
    setIsSubmitting(true);
    try {
      await invoiceService.deleteInvoice(activeInvoice.id);
      showToast('success', 'Invoice Deleted', 'Invoice removed.');
      setIsDeleteOpen(false);
      fetchInvoices();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Could not delete invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: InvoiceStatus, isOverdue: boolean) => {
    if (isOverdue && status === 'PENDING') {
      return <Badge variant="destructive">OVERDUE</Badge>;
    }
    switch (status) {
      case 'PAID':
        return <Badge variant="success">PAID</Badge>;
      case 'OVERDUE':
        return <Badge variant="destructive">OVERDUE</Badge>;
      case 'CANCELLED':
        return <Badge variant="secondary">CANCELLED</Badge>;
      case 'PENDING':
      default:
        return <Badge variant="warning">PENDING</Badge>;
    }
  };

  const canManage = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Accounts Payable & Invoices
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Supplier invoice reconciliation, maturity tracking, and cash-outflow scheduling
          </p>
        </div>
        {canManage && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setFormData({
                invoice_number: `INV-2026-${Math.floor(1000 + Math.random() * 9000)}`,
                vendor_id: '',
                issue_date: new Date().toISOString().split('T')[0],
                due_date: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
                amount: '',
                status: 'PENDING',
              });
              setIsCreateOpen(true);
            }}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Record Invoice
          </Button>
        )}
      </div>

      {/* KPI Cards */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Total Invoiced (All)</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">{formatCurrency(data.total_invoiced)}</div>
          </Card>
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-emerald-400 uppercase">Settled & Paid</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{formatCurrency(data.total_paid)}</div>
          </Card>
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-amber-400 uppercase">Pending Due</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">{formatCurrency(data.total_pending)}</div>
          </Card>
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-rose-400 uppercase">Overdue Critical</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">{formatCurrency(data.total_overdue)}</div>
          </Card>
        </div>
      )}

      {/* Filter Selector */}
      <div className="max-w-xs">
        <Select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          options={[
            { label: 'All Invoices', value: '' },
            { label: 'PENDING Only', value: 'PENDING' },
            { label: 'PAID Only', value: 'PAID' },
            { label: 'OVERDUE Only', value: 'OVERDUE' },
            { label: 'CANCELLED Only', value: 'CANCELLED' },
          ]}
        />
      </div>

      {/* Invoices Table */}
      <Card className="border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Invoice #</th>
                <th className="px-4 py-3.5">Vendor</th>
                <th className="px-4 py-3.5">Issue Date</th>
                <th className="px-4 py-3.5">Due Date</th>
                <th className="px-4 py-3.5 text-right">Amount</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={7} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : !data || data.invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    No invoices matching filter.
                  </td>
                </tr>
              ) : (
                data.invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-slate-100">
                      {inv.invoice_number}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-200">
                      {inv.vendor_name || 'Vendor'}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {formatDate(inv.issue_date)}
                    </td>
                    <td className={`px-4 py-3 font-medium ${inv.is_overdue ? 'text-rose-400' : 'text-slate-300'}`}>
                      {formatDate(inv.due_date)}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-100">
                      {formatCurrency(inv.amount)}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(inv.status, inv.is_overdue)}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {canManage && (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => {
                              setActiveInvoice(inv);
                              setFormData({
                                invoice_number: inv.invoice_number,
                                vendor_id: inv.vendor_id ? String(inv.vendor_id) : '',
                                issue_date: inv.issue_date,
                                due_date: inv.due_date,
                                amount: String(inv.amount),
                                status: inv.status,
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
                              setActiveInvoice(inv);
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

      {/* Create Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Record Vendor Invoice">
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <Input
            label="Invoice Number"
            value={formData.invoice_number}
            onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
            placeholder="INV-2026-001"
            required
          />

          <Select
            label="Vendor"
            value={formData.vendor_id}
            onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
            options={[
              { label: 'Select Vendor', value: '' },
              ...vendors.map((v) => ({ label: v.name, value: v.id })),
            ]}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Issue Date"
              type="date"
              value={formData.issue_date}
              onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
              required
            />
            <Input
              label="Due Date"
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Amount ($)"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
            />
            <Select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as InvoiceStatus })}
              options={[
                { label: 'PENDING', value: 'PENDING' },
                { label: 'PAID', value: 'PAID' },
                { label: 'OVERDUE', value: 'OVERDUE' },
                { label: 'CANCELLED', value: 'CANCELLED' },
              ]}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Save Invoice
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Edit Invoice">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Invoice Number"
            value={formData.invoice_number}
            onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Amount ($)"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
            />
            <Select
              label="Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as InvoiceStatus })}
              options={[
                { label: 'PENDING', value: 'PENDING' },
                { label: 'PAID', value: 'PAID' },
                { label: 'OVERDUE', value: 'OVERDUE' },
                { label: 'CANCELLED', value: 'CANCELLED' },
              ]}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Update Invoice
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Dialog */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Invoice"
        message={`Are you sure you want to remove Invoice #${activeInvoice?.invoice_number}?`}
        confirmText="Delete"
        isDestructive
        isLoading={isSubmitting}
      />
    </div>
  );
};
