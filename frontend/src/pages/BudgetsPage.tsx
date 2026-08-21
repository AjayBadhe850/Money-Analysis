import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Plus,
  Edit2,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Layers,
  ArrowUpRight,
} from 'lucide-react';
import { budgetService } from '../services/budget.service';
import { departmentService } from '../services/department.service';
import { Budget, Department, Category, BudgetStatus, BudgetSummaryResponse } from '../types';
import { formatCurrency, formatPercent, getBudgetStatusColor } from '../utils/formatters';
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

export const BudgetsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [data, setData] = useState<BudgetSummaryResponse | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [selectedYear, setSelectedYear] = useState<number>(2026);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [activeBudget, setActiveBudget] = useState<Budget | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    year: 2026,
    month: '',
    allocated_amount: '',
    department_id: '',
    category_id: '',
    notes: '',
  });

  const fetchBudgets = async () => {
    setIsLoading(true);
    try {
      const res = await budgetService.getBudgets(selectedYear);
      setData(res);
    } catch (err) {
      console.error('Failed to load budgets:', err);
      showToast('error', 'Error', 'Failed to fetch budget allocations');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [depts, cats] = await Promise.all([
          departmentService.getDepartments(),
          departmentService.getCategories(),
        ]);
        setDepartments(depts);
        setCategories(cats);
      } catch (err) {
        console.error('Failed to load departments/categories:', err);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    fetchBudgets();
  }, [selectedYear]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await budgetService.createBudget({
        year: Number(formData.year),
        month: formData.month ? Number(formData.month) : undefined,
        allocated_amount: Number(formData.allocated_amount),
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        category_id: formData.category_id ? Number(formData.category_id) : undefined,
        notes: formData.notes || undefined,
      });
      showToast('success', 'Budget Created', 'New budget allocation registered.');
      setIsCreateOpen(false);
      fetchBudgets();
    } catch (err: any) {
      showToast('error', 'Creation Failed', err.response?.data?.detail || 'Validation error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeBudget) return;
    setIsSubmitting(true);
    try {
      await budgetService.updateBudget(activeBudget.id, {
        allocated_amount: Number(formData.allocated_amount),
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        category_id: formData.category_id ? Number(formData.category_id) : undefined,
        notes: formData.notes || undefined,
      });
      showToast('success', 'Budget Updated', 'Budget allocation updated.');
      setIsEditOpen(false);
      fetchBudgets();
    } catch (err: any) {
      showToast('error', 'Update Failed', err.response?.data?.detail || 'Validation error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeBudget) return;
    setIsSubmitting(true);
    try {
      await budgetService.deleteBudget(activeBudget.id);
      showToast('success', 'Budget Deleted', 'Budget allocation removed.');
      setIsDeleteOpen(false);
      fetchBudgets();
    } catch (err: any) {
      showToast('error', 'Delete Failed', err.response?.data?.detail || 'Could not delete budget');
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
            Budget Governance & Control
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Department and category allocation thresholds, real-time burn velocity, and overspending guards
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            options={[
              { label: 'FY 2026', value: 2026 },
              { label: 'FY 2025', value: 2025 },
            ]}
          />
          {canManage && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setFormData({
                  year: selectedYear,
                  month: '',
                  allocated_amount: '',
                  department_id: '',
                  category_id: '',
                  notes: '',
                });
                setIsCreateOpen(true);
              }}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Set New Budget
            </Button>
          )}
        </div>
      </div>

      {/* Summary KPI Ribbon */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Total Allocated Budget</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">{formatCurrency(data.total_allocated)}</div>
            <div className="text-[11px] text-slate-400 mt-1">{data.budgets.length} total budget lines</div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Total Spent to Date</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">{formatCurrency(data.total_spent)}</div>
            <div className="text-[11px] text-slate-400 mt-1">
              Overall Burn: <strong className="text-slate-200">{formatPercent(data.overall_usage_percentage)}</strong>
            </div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Remaining Capital</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{formatCurrency(data.total_remaining)}</div>
            <div className="text-[11px] text-emerald-400/80 mt-1">Available for allocation</div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/60">
            <div className="text-xs font-semibold text-slate-400 uppercase">Threshold Statuses</div>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                {data.safe_count} Safe
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs font-bold border border-amber-500/20">
                {data.warning_count} Warn
              </span>
              <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 text-xs font-bold border border-rose-500/20">
                {data.exceeded_count} Exceeded
              </span>
            </div>
          </Card>
        </div>
      )}

      {/* Budget Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {isLoading ? (
          [...Array(6)].map((_, i) => <Skeleton key={i} className="h-56 rounded-xl" />)
        ) : !data || data.budgets.length === 0 ? (
          <div className="col-span-3">
            <Card className="p-8 text-center border-slate-800">
              <p className="text-slate-400 text-sm">No budget allocations found for FY {selectedYear}.</p>
            </Card>
          </div>
        ) : (
          data.budgets.map((b) => {
            const statusColor = getBudgetStatusColor(b.status);
            return (
              <Card key={b.id} className="hover-glow border-slate-800 flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block mb-0.5">
                        {b.department_name !== 'All Departments' ? 'Department Budget' : 'Category / Global Budget'}
                      </span>
                      <CardTitle className="text-base font-bold text-slate-100">
                        {b.department_name !== 'All Departments' ? b.department_name : b.category_name}
                      </CardTitle>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase ${statusColor.bg} ${statusColor.text} ${statusColor.border}`}
                    >
                      {b.status}
                    </span>
                  </div>
                  {b.notes && <CardDescription className="line-clamp-1">{b.notes}</CardDescription>}
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Metric Row */}
                  <div className="grid grid-cols-2 gap-2 text-xs p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Allocated:</span>
                      <span className="font-bold text-slate-100">{formatCurrency(b.allocated_amount)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Actual Spent:</span>
                      <span className="font-bold text-rose-400">{formatCurrency(b.spent_amount)}</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Burn Percentage</span>
                      <span className="font-bold text-slate-200">{formatPercent(b.usage_percentage)}</span>
                    </div>
                    <Progress value={b.usage_percentage} variant={b.usage_percentage > 85 ? 'rose' : 'default'} />
                  </div>

                  {/* Remaining / Overspend */}
                  <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80">
                    {b.overspent_amount > 0 ? (
                      <span className="text-rose-400 font-medium">
                        Overspent by {formatCurrency(b.overspent_amount)}
                      </span>
                    ) : (
                      <span className="text-emerald-400 font-medium">
                        Remaining: {formatCurrency(b.remaining_amount)}
                      </span>
                    )}

                    {canManage && (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => {
                            setActiveBudget(b);
                            setFormData({
                              year: b.year,
                              month: b.month ? String(b.month) : '',
                              allocated_amount: String(b.allocated_amount),
                              department_id: b.department_id ? String(b.department_id) : '',
                              category_id: b.category_id ? String(b.category_id) : '',
                              notes: b.notes || '',
                            });
                            setIsEditOpen(true);
                          }}
                          className="p-1 rounded text-slate-400 hover:text-indigo-400"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setActiveBudget(b);
                            setIsDeleteOpen(true);
                          }}
                          className="p-1 rounded text-slate-400 hover:text-rose-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {/* Create Budget Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Budget Allocation"
        description="Define target budget limits for department or expense categories"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Fiscal Year"
              type="number"
              value={formData.year}
              onChange={(e) => setFormData({ ...formData, year: Number(e.target.value) })}
              required
            />
            <Input
              label="Allocated Amount ($)"
              type="number"
              step="100"
              value={formData.allocated_amount}
              onChange={(e) => setFormData({ ...formData, allocated_amount: e.target.value })}
              placeholder="e.g. 150000"
              required
            />
          </div>

          <Select
            label="Department"
            value={formData.department_id}
            onChange={(e) => setFormData({ ...formData, department_id: e.target.value, category_id: '' })}
            options={[
              { label: 'None (Company or Category Level)', value: '' },
              ...departments.map((d) => ({ label: d.name, value: d.id })),
            ]}
          />

          <Select
            label="Category (Optional)"
            value={formData.category_id}
            onChange={(e) => setFormData({ ...formData, category_id: e.target.value, department_id: '' })}
            options={[
              { label: 'None', value: '' },
              ...categories.map((c) => ({ label: c.name, value: c.id })),
            ]}
          />

          <Input
            label="Notes / Description"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="e.g. Q1-Q4 R&D Infrastructure Cap"
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Save Budget
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Budget Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Budget Allocation"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Allocated Amount ($)"
            type="number"
            value={formData.allocated_amount}
            onChange={(e) => setFormData({ ...formData, allocated_amount: e.target.value })}
            required
          />
          <Input
            label="Notes"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Update Budget
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Budget"
        message={`Are you sure you want to remove this budget allocation of ${formatCurrency(activeBudget?.allocated_amount)}?`}
        confirmText="Delete Budget"
        isDestructive
        isLoading={isSubmitting}
      />
    </div>
  );
};
