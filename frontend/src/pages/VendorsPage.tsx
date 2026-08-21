import React, { useState, useEffect } from 'react';
import {
  Users,
  Plus,
  Edit2,
  Trash2,
  Star,
  Clock,
  ShieldCheck,
  Search,
  ExternalLink,
} from 'lucide-react';
import { vendorService } from '../services/vendor.service';
import { Vendor } from '../types';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { Skeleton } from '../components/ui/Skeleton';
import { Progress } from '../components/ui/Progress';

export const VendorsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [activeVendor, setActiveVendor] = useState<Vendor | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    contact_email: '',
    category: '',
    reliability_score: '95',
    quality_score: '90',
    average_delivery_days: '2',
  });

  const fetchVendors = async () => {
    setIsLoading(true);
    try {
      const list = await vendorService.getVendors();
      setVendors(list);
    } catch (err) {
      console.error('Failed to load vendors:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await vendorService.createVendor({
        name: formData.name,
        contact_email: formData.contact_email || undefined,
        category: formData.category || undefined,
        reliability_score: Number(formData.reliability_score),
        quality_score: Number(formData.quality_score),
        average_delivery_days: Number(formData.average_delivery_days),
      });
      showToast('success', 'Vendor Added', `Vendor "${formData.name}" contracted.`);
      setIsCreateOpen(false);
      fetchVendors();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to create vendor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeVendor) return;
    setIsSubmitting(true);
    try {
      await vendorService.updateVendor(activeVendor.id, {
        name: formData.name,
        contact_email: formData.contact_email || undefined,
        category: formData.category || undefined,
        reliability_score: Number(formData.reliability_score),
        quality_score: Number(formData.quality_score),
        average_delivery_days: Number(formData.average_delivery_days),
      });
      showToast('success', 'Vendor Updated', 'Vendor metrics updated.');
      setIsEditOpen(false);
      fetchVendors();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to update vendor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeVendor) return;
    setIsSubmitting(true);
    try {
      await vendorService.deleteVendor(activeVendor.id);
      showToast('success', 'Vendor Deleted', 'Vendor record removed.');
      setIsDeleteOpen(false);
      fetchVendors();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Could not delete vendor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredVendors = vendors.filter((v) =>
    v.name.toLowerCase().includes(search.toLowerCase()) ||
    (v.category && v.category.toLowerCase().includes(search.toLowerCase()))
  );

  const canManage = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Vendor Directory & Performance
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Supplier spend aggregation, reliability grading, and delivery SLAs
          </p>
        </div>
        {canManage && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setFormData({
                name: '',
                contact_email: '',
                category: 'Cloud Infrastructure',
                reliability_score: '95',
                quality_score: '90',
                average_delivery_days: '2',
              });
              setIsCreateOpen(true);
            }}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add New Vendor
          </Button>
        )}
      </div>

      {/* Search Input */}
      <div className="max-w-md">
        <Input
          placeholder="Filter vendors by name or category..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          leftIcon={<Search className="w-4 h-4" />}
        />
      </div>

      {/* Vendors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {isLoading ? (
          [...Array(6)].map((_, i) => <Skeleton key={i} className="h-60 rounded-xl" />)
        ) : filteredVendors.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-slate-400">
            No vendors match your search query.
          </div>
        ) : (
          filteredVendors.map((v) => (
            <Card key={v.id} className="hover-glow border-slate-800 flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 block mb-0.5">
                      {v.category || 'Enterprise Vendor'}
                    </span>
                    <CardTitle className="text-base font-bold text-slate-100">{v.name}</CardTitle>
                  </div>
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                {v.contact_email && (
                  <CardDescription className="font-mono text-[11px] text-slate-400">
                    {v.contact_email}
                  </CardDescription>
                )}
              </CardHeader>

              <CardContent className="space-y-3.5">
                {/* Spend Stats */}
                <div className="grid grid-cols-3 gap-2 text-center p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <div>
                    <div className="text-[10px] text-slate-400">Total Spend</div>
                    <div className="font-bold text-slate-100 mt-0.5">{formatCurrency(v.total_spend)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Transactions</div>
                    <div className="font-bold text-slate-100 mt-0.5">{v.transaction_count}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Avg Value</div>
                    <div className="font-bold text-slate-100 mt-0.5">{formatCurrency(v.average_transaction_value)}</div>
                  </div>
                </div>

                {/* Reliability & Quality Meters */}
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Reliability Score
                    </span>
                    <span className="font-semibold text-emerald-400">{v.reliability_score}%</span>
                  </div>
                  <Progress value={v.reliability_score} variant="emerald" size="sm" />

                  <div className="flex items-center justify-between text-slate-400 pt-1">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-indigo-400" /> Avg Delivery Days
                    </span>
                    <span className="font-semibold text-slate-200">{v.average_delivery_days} days</span>
                  </div>
                </div>

                {/* Footer Controls */}
                {canManage && (
                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
                    <button
                      onClick={() => {
                        setActiveVendor(v);
                        setFormData({
                          name: v.name,
                          contact_email: v.contact_email || '',
                          category: v.category || '',
                          reliability_score: String(v.reliability_score),
                          quality_score: String(v.quality_score),
                          average_delivery_days: String(v.average_delivery_days),
                        });
                        setIsEditOpen(true);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors"
                      title="Edit Vendor"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => {
                        setActiveVendor(v);
                        setIsDeleteOpen(true);
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                      title="Delete Vendor"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Create Vendor Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Add Supplier / Vendor">
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <Input
            label="Vendor Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g. Amazon Web Services"
            required
          />
          <Input
            label="Contact Email"
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
            placeholder="billing@vendor.com"
          />
          <Input
            label="Category"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            placeholder="e.g. Cloud Infrastructure"
          />
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Reliability (0-100)"
              type="number"
              value={formData.reliability_score}
              onChange={(e) => setFormData({ ...formData, reliability_score: e.target.value })}
              required
            />
            <Input
              label="Quality (0-100)"
              type="number"
              value={formData.quality_score}
              onChange={(e) => setFormData({ ...formData, quality_score: e.target.value })}
              required
            />
            <Input
              label="Avg Delivery (Days)"
              type="number"
              step="0.1"
              value={formData.average_delivery_days}
              onChange={(e) => setFormData({ ...formData, average_delivery_days: e.target.value })}
              required
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Save Vendor
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Vendor Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Edit Vendor">
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          <Input
            label="Vendor Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Contact Email"
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
          />
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Reliability"
              type="number"
              value={formData.reliability_score}
              onChange={(e) => setFormData({ ...formData, reliability_score: e.target.value })}
              required
            />
            <Input
              label="Quality"
              type="number"
              value={formData.quality_score}
              onChange={(e) => setFormData({ ...formData, quality_score: e.target.value })}
              required
            />
            <Input
              label="Delivery Days"
              type="number"
              step="0.1"
              value={formData.average_delivery_days}
              onChange={(e) => setFormData({ ...formData, average_delivery_days: e.target.value })}
              required
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Update Vendor
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Dialog */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Vendor"
        message={`Are you sure you want to delete "${activeVendor?.name}"?`}
        confirmText="Delete Vendor"
        isDestructive
        isLoading={isSubmitting}
      />
    </div>
  );
};
