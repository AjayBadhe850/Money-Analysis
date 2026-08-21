import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Plus,
  Upload,
  Download,
  Trash2,
  Edit2,
  Eye,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  FileSpreadsheet,
  AlertCircle,
} from 'lucide-react';
import { transactionService, TransactionQueryParams } from '../services/transaction.service';
import { departmentService } from '../services/department.service';
import { vendorService } from '../services/vendor.service';
import { Transaction, Department, Category, Vendor, TransactionType } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

export const TransactionsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRev, setTotalRev] = useState(0);
  const [totalExp, setTotalExp] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Filter dropdown data
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);

  // Filter params
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [selectedCat, setSelectedCat] = useState<string>('');
  const [selectedVendor, setSelectedVendor] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  const [sortBy, setSortBy] = useState('transaction_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const [activeTransaction, setActiveTransaction] = useState<Transaction | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state for create/edit
  const [formData, setFormData] = useState({
    transaction_date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    transaction_type: 'EXPENSE' as TransactionType,
    payment_method: 'Bank Transfer',
    reference_number: '',
    department_id: '',
    category_id: '',
    vendor_id: '',
  });

  // CSV Import State
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<any | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  // Load auxiliary data
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [deptList, catList, vendorList] = await Promise.all([
          departmentService.getDepartments(),
          departmentService.getCategories(),
          vendorService.getVendors(),
        ]);
        setDepartments(deptList);
        setCategories(catList);
        setVendors(vendorList);
      } catch (err) {
        console.error('Failed to load filter metadata:', err);
      }
    };
    loadMetadata();
  }, []);

  // Fetch transactions
  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: TransactionQueryParams = {
        page,
        page_size: 25,
        search: search.trim() || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        department_id: selectedDept ? Number(selectedDept) : undefined,
        category_id: selectedCat ? Number(selectedCat) : undefined,
        vendor_id: selectedVendor ? Number(selectedVendor) : undefined,
        transaction_type: selectedType || undefined,
        min_amount: minAmount ? Number(minAmount) : undefined,
        max_amount: maxAmount ? Number(maxAmount) : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      const res = await transactionService.getTransactions(params);
      setTransactions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
      setTotalRev(res.total_revenue_amount ?? (res as any).total_revenue ?? 0);
      setTotalExp(res.total_expenses_amount ?? (res as any).total_expense ?? 0);
    } catch (err) {
      console.error('Failed to fetch transactions:', err);
      showToast('error', 'Error', 'Failed to load transactions');
    } finally {
      setIsLoading(false);
    }
  }, [page, search, startDate, endDate, selectedDept, selectedCat, selectedVendor, selectedType, minAmount, maxAmount, sortBy, sortOrder, showToast]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await transactionService.createTransaction({
        transaction_date: formData.transaction_date,
        description: formData.description,
        amount: Number(formData.amount),
        transaction_type: formData.transaction_type,
        payment_method: formData.payment_method,
        reference_number: formData.reference_number || undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        category_id: formData.category_id ? Number(formData.category_id) : undefined,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
      });
      showToast('success', 'Transaction Created', 'New financial transaction recorded.');
      setIsCreateOpen(false);
      fetchTransactions();
    } catch (err: any) {
      showToast('error', 'Creation Failed', err.response?.data?.detail || 'Validation error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTransaction) return;
    setIsSubmitting(true);
    try {
      await transactionService.updateTransaction(activeTransaction.id, {
        transaction_date: formData.transaction_date,
        description: formData.description,
        amount: Number(formData.amount),
        transaction_type: formData.transaction_type,
        payment_method: formData.payment_method,
        reference_number: formData.reference_number || undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        category_id: formData.category_id ? Number(formData.category_id) : undefined,
        vendor_id: formData.vendor_id ? Number(formData.vendor_id) : undefined,
      });
      showToast('success', 'Transaction Updated', 'Transaction details updated.');
      setIsEditOpen(false);
      fetchTransactions();
    } catch (err: any) {
      showToast('error', 'Update Failed', err.response?.data?.detail || 'Validation error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeTransaction) return;
    setIsSubmitting(true);
    try {
      await transactionService.deleteTransaction(activeTransaction.id);
      showToast('success', 'Deleted', 'Transaction deleted successfully.');
      setIsDeleteOpen(false);
      fetchTransactions();
    } catch (err: any) {
      showToast('error', 'Delete Failed', err.response?.data?.detail || 'Could not delete transaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenEdit = (t: Transaction) => {
    setActiveTransaction(t);
    setFormData({
      transaction_date: t.transaction_date,
      description: t.description,
      amount: String(t.amount),
      transaction_type: t.transaction_type,
      payment_method: t.payment_method || '',
      reference_number: t.reference_number || '',
      department_id: t.department_id ? String(t.department_id) : '',
      category_id: t.category_id ? String(t.category_id) : '',
      vendor_id: t.vendor_id ? String(t.vendor_id) : '',
    });
    setIsEditOpen(true);
  };

  const handleCSVUpload = async () => {
    if (!importFile) return;
    setIsImporting(true);
    try {
      const res = await transactionService.importCSV(importFile);
      setImportResult(res);
      if (res.imported_count > 0) {
        showToast('success', 'Import Complete', `Imported ${res.imported_count} transactions successfully.`);
        fetchTransactions();
      } else {
        showToast('warning', 'Import Notice', res.message || 'No new rows imported');
      }
    } catch (err: any) {
      showToast('error', 'CSV Import Failed', err.response?.data?.detail || 'Invalid CSV format');
    } finally {
      setIsImporting(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await transactionService.downloadCSVTemplate();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'money_analysis_transactions_template.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (_err) {
      showToast('error', 'Download Failed', 'Could not download CSV template');
    }
  };

  const canEdit = user?.role === 'Admin' || user?.role === 'Finance Manager' || user?.role === 'Department Manager';
  const canDelete = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-6">
      {/* Header and Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Transaction Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise transaction registry, Pandas CSV ingest engine, and multi-dimensional filtering
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadTemplate}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            Template
          </Button>
          {canEdit && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setImportFile(null);
                setImportResult(null);
                setIsImportOpen(true);
              }}
              leftIcon={<Upload className="w-3.5 h-3.5 text-cyan-400" />}
            >
              Import CSV
            </Button>
          )}
          {canEdit && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setFormData({
                  transaction_date: new Date().toISOString().split('T')[0],
                  description: '',
                  amount: '',
                  transaction_type: 'EXPENSE',
                  payment_method: 'Bank Transfer',
                  reference_number: '',
                  department_id: '',
                  category_id: '',
                  vendor_id: '',
                });
                setIsCreateOpen(true);
              }}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Add Transaction
            </Button>
          )}
        </div>
      </div>

      {/* Filtered Metric Aggregate Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Filtered Records</div>
            <div className="text-xl font-bold text-slate-100 mt-1">{total} Transactions</div>
          </div>
          <Badge variant="secondary">Page {page} of {totalPages}</Badge>
        </div>
        <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 backdrop-blur-md flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">Total Revenue in View</div>
            <div className="text-xl font-bold text-cyan-300 mt-1">{formatCurrency(totalRev)}</div>
          </div>
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/5 backdrop-blur-md flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Total Expenses in View</div>
            <div className="text-xl font-bold text-rose-300 mt-1">{formatCurrency(totalExp)}</div>
          </div>
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
            <TrendingDown className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Multi-Dimensional Filter Bar */}
      <Card className="border-slate-800 bg-slate-900/70 p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <Input
            placeholder="Search description, reference..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            leftIcon={<Search className="w-4 h-4" />}
          />

          {/* Department Filter */}
          <Select
            value={selectedDept}
            onChange={(e) => {
              setSelectedDept(e.target.value);
              setPage(1);
            }}
            options={[
              { label: 'All Departments', value: '' },
              ...departments.map((d) => ({ label: d.name, value: d.id })),
            ]}
          />

          {/* Category Filter */}
          <Select
            value={selectedCat}
            onChange={(e) => {
              setSelectedCat(e.target.value);
              setPage(1);
            }}
            options={[
              { label: 'All Categories', value: '' },
              ...categories.map((c) => ({ label: c.name, value: c.id })),
            ]}
          />

          {/* Transaction Type Filter */}
          <Select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setPage(1);
            }}
            options={[
              { label: 'All Types (Expense + Revenue)', value: '' },
              { label: 'EXPENSE Only', value: 'EXPENSE' },
              { label: 'REVENUE Only', value: 'REVENUE' },
            ]}
          />
        </div>

        {/* Secondary Filters: Dates & Vendors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-1 border-t border-slate-800/60">
          <Input
            type="date"
            placeholder="From Date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />
          <Input
            type="date"
            placeholder="To Date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
          <Select
            value={selectedVendor}
            onChange={(e) => {
              setSelectedVendor(e.target.value);
              setPage(1);
            }}
            options={[
              { label: 'All Vendors', value: '' },
              ...vendors.map((v) => ({ label: v.name, value: v.id })),
            ]}
          />
          <Input
            type="number"
            placeholder="Min Amount ($)"
            value={minAmount}
            onChange={(e) => {
              setMinAmount(e.target.value);
              setPage(1);
            }}
          />
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => {
                setSearch('');
                setStartDate('');
                setEndDate('');
                setSelectedDept('');
                setSelectedCat('');
                setSelectedVendor('');
                setSelectedType('');
                setMinAmount('');
                setMaxAmount('');
                setPage(1);
              }}
            >
              Reset Filters
            </Button>
          </div>
        </div>
      </Card>

      {/* Transactions Data Table */}
      <Card className="border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3.5">Date</th>
                <th className="px-4 py-3.5">Description</th>
                <th className="px-4 py-3.5">Department</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Vendor / Source</th>
                <th className="px-4 py-3.5">Type</th>
                <th className="px-4 py-3.5 text-right">Amount</th>
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
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8">
                    <EmptyState
                      title="No transactions found"
                      description="Try adjusting your filter criteria or import a CSV dataset."
                      actionText={canEdit ? 'Add First Transaction' : undefined}
                      onAction={() => setIsCreateOpen(true)}
                    />
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-200 whitespace-nowrap">
                      {formatDate(tx.transaction_date)}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-100 max-w-xs truncate">
                      {tx.description}
                      {tx.reference_number && (
                        <span className="block text-[10px] text-slate-400 font-mono">
                          {tx.reference_number}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {tx.department_name || <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {tx.category_name ? (
                        <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 text-[11px] font-medium">
                          {tx.category_name}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {tx.vendor_name || <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={tx.transaction_type === 'REVENUE' ? 'cyan' : 'destructive'}>
                        {tx.transaction_type}
                      </Badge>
                    </td>
                    <td className={`px-4 py-3 text-right font-bold whitespace-nowrap ${
                      tx.transaction_type === 'REVENUE' ? 'text-cyan-400' : 'text-slate-100'
                    }`}>
                      {tx.transaction_type === 'REVENUE' ? '+' : '-'} {formatCurrency(tx.amount)}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => {
                            setActiveTransaction(tx);
                            setIsDetailOpen(true);
                          }}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                          title="View Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {canEdit && (
                          <button
                            onClick={() => handleOpenEdit(tx)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-indigo-400"
                            title="Edit"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => {
                              setActiveTransaction(tx);
                              setIsDeleteOpen(true);
                            }}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800/80 bg-slate-950/40 text-xs text-slate-400">
          <div>
            Showing <strong className="text-slate-200">{transactions.length}</strong> of{' '}
            <strong className="text-slate-200">{total}</strong> total transactions
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              leftIcon={<ChevronLeft className="w-4 h-4" />}
            >
              Previous
            </Button>
            <span className="px-2 font-medium text-slate-300">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              rightIcon={<ChevronRight className="w-4 h-4" />}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Create Transaction Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Record New Transaction"
        description="Enter financial transaction details for company accounts"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Transaction Date"
              type="date"
              value={formData.transaction_date}
              onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
              required
            />
            <Select
              label="Transaction Type"
              value={formData.transaction_type}
              onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionType })}
              options={[
                { label: 'EXPENSE (Cash Outflow)', value: 'EXPENSE' },
                { label: 'REVENUE (Cash Inflow)', value: 'REVENUE' },
              ]}
            />
          </div>

          <Input
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="e.g. AWS EC2 Cloud Compute Services"
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Amount ($ USD)"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              placeholder="0.00"
              required
            />
            <Input
              label="Reference / Invoice #"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
              placeholder="e.g. INV-2026-889"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Select
              label="Department"
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
              options={[
                { label: 'Select Department', value: '' },
                ...departments.map((d) => ({ label: d.name, value: d.id })),
              ]}
            />
            <Select
              label="Category"
              value={formData.category_id}
              onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              options={[
                { label: 'Select Category', value: '' },
                ...categories.map((c) => ({ label: c.name, value: c.id })),
              ]}
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
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Save Transaction
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Transaction Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Transaction"
        maxWidth="lg"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Transaction Date"
              type="date"
              value={formData.transaction_date}
              onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
              required
            />
            <Select
              label="Transaction Type"
              value={formData.transaction_type}
              onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as TransactionType })}
              options={[
                { label: 'EXPENSE', value: 'EXPENSE' },
                { label: 'REVENUE', value: 'REVENUE' },
              ]}
            />
          </div>

          <Input
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Amount ($ USD)"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
            />
            <Input
              label="Reference #"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Select
              label="Department"
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
              options={[
                { label: 'None', value: '' },
                ...departments.map((d) => ({ label: d.name, value: d.id })),
              ]}
            />
            <Select
              label="Category"
              value={formData.category_id}
              onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              options={[
                { label: 'None', value: '' },
                ...categories.map((c) => ({ label: c.name, value: c.id })),
              ]}
            />
            <Select
              label="Vendor"
              value={formData.vendor_id}
              onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
              options={[
                { label: 'None', value: '' },
                ...vendors.map((v) => ({ label: v.name, value: v.id })),
              ]}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Update Transaction
            </Button>
          </div>
        </form>
      </Modal>

      {/* Transaction Details Viewer Modal */}
      {activeTransaction && (
        <Modal
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          title="Transaction Details"
          maxWidth="md"
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Transaction ID:</span>
                <span className="font-mono text-slate-200">#{activeTransaction.id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Date:</span>
                <span className="font-semibold text-slate-200">{formatDate(activeTransaction.transaction_date)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Amount:</span>
                <span className="text-base font-bold text-slate-100">{formatCurrency(activeTransaction.amount)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Type:</span>
                <Badge variant={activeTransaction.transaction_type === 'REVENUE' ? 'cyan' : 'destructive'}>
                  {activeTransaction.transaction_type}
                </Badge>
              </div>
            </div>

            <div className="space-y-2 text-slate-300">
              <div>
                <span className="text-slate-400 block mb-1">Description:</span>
                <p className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 font-medium">
                  {activeTransaction.description}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-2">
                <div>
                  <span className="text-slate-400 block">Department:</span>
                  <span className="font-medium text-slate-200">{activeTransaction.department_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Category:</span>
                  <span className="font-medium text-slate-200">{activeTransaction.category_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Vendor:</span>
                  <span className="font-medium text-slate-200">{activeTransaction.vendor_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Reference:</span>
                  <span className="font-medium font-mono text-slate-200">{activeTransaction.reference_number || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-slate-800">
              <Button variant="secondary" size="sm" onClick={() => setIsDetailOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* CSV Import Modal */}
      <Modal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        title="Import Transactions via CSV"
        description="Upload batch transaction data with Pandas automated validation and duplicate detection"
        maxWidth="lg"
      >
        <div className="space-y-4 text-xs">
          {/* File Picker */}
          <div className="p-6 rounded-xl border-2 border-dashed border-slate-800 hover:border-indigo-500/50 bg-slate-950/40 text-center transition-colors">
            <FileSpreadsheet className="w-10 h-10 text-indigo-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-200 mb-1">
              {importFile ? importFile.name : 'Select or drop CSV file'}
            </p>
            <p className="text-xs text-slate-400 mb-4">
              Columns expected: <code className="text-indigo-300">date, description, amount, type, department, vendor</code>
            </p>
            <input
              type="file"
              accept=".csv"
              id="csv-file-input"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setImportFile(e.target.files[0]);
                  setImportResult(null);
                }
              }}
            />
            <label htmlFor="csv-file-input">
              <span className="cursor-pointer inline-flex items-center justify-center font-medium text-xs px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg transition-all">
                Choose CSV File
              </span>
            </label>
          </div>

          {/* Validation Result Box */}
          {importResult && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-semibold text-slate-100">Batch Ingestion Summary</span>
                <Badge variant={importResult.success ? 'success' : 'destructive'}>
                  {importResult.imported_count} / {importResult.total_rows} Imported
                </Badge>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                  <div className="font-bold text-base">{importResult.imported_count}</div>
                  <div className="text-[10px]">Valid Saved</div>
                </div>
                <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300">
                  <div className="font-bold text-base">{importResult.duplicates_count}</div>
                  <div className="text-[10px]">Duplicates Skipped</div>
                </div>
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300">
                  <div className="font-bold text-base">{importResult.rejected_count}</div>
                  <div className="text-[10px]">Errors / Rejected</div>
                </div>
              </div>

              {/* Error messages list */}
              {importResult.errors && importResult.errors.length > 0 && (
                <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                  <div className="text-[11px] font-semibold text-rose-400">Row Validation Errors:</div>
                  {importResult.errors.map((err: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-rose-500/5 border border-rose-500/10 text-rose-300 text-[11px] flex items-start gap-2">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                      <span><strong>Row {err.row} ({err.column}):</strong> {err.error}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <Button variant="ghost" size="sm" onClick={handleDownloadTemplate} leftIcon={<Download className="w-3.5 h-3.5" />}>
              Download Sample CSV
            </Button>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={() => setIsImportOpen(false)}>
                Done
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCSVUpload}
                disabled={!importFile}
                isLoading={isImporting}
                leftIcon={<Upload className="w-3.5 h-3.5" />}
              >
                Upload & Process
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Transaction"
        message={`Are you sure you want to delete "${activeTransaction?.description}" for ${formatCurrency(activeTransaction?.amount)}? This action will be logged in the audit ledger.`}
        confirmText="Delete Transaction"
        isDestructive
        isLoading={isSubmitting}
      />
    </div>
  );
};
