import React, { useState, useEffect } from 'react';
import { Building2, Plus, Users, FolderTree, Sparkles } from 'lucide-react';
import { departmentService } from '../services/department.service';
import { Department, Category } from '../types';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';

export const DepartmentsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [isDeptModalOpen, setIsDeptModalOpen] = useState(false);
  const [isCatModalOpen, setIsCatModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [deptName, setDeptName] = useState('');
  const [catName, setCatName] = useState('');
  const [catColor, setCatColor] = useState('#6366F1');

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [depts, cats] = await Promise.all([
        departmentService.getDepartments(),
        departmentService.getCategories(),
      ]);
      setDepartments(depts);
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load departments/categories:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await departmentService.createDepartment({ name: deptName });
      showToast('success', 'Department Added', `Department "${deptName}" created.`);
      setIsDeptModalOpen(false);
      setDeptName('');
      fetchData();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to create department');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateCat = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await departmentService.createCategory({ name: catName, color_code: catColor });
      showToast('success', 'Category Added', `Category "${catName}" registered.`);
      setIsCatModalOpen(false);
      setCatName('');
      fetchData();
    } catch (err: any) {
      showToast('error', 'Error', err.response?.data?.detail || 'Failed to create category');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canManage = user?.role === 'Admin' || user?.role === 'Finance Manager';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Departments & Taxonomies
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Organizational hierarchy, spend centers, and financial classification categories
          </p>
        </div>
        {canManage && (
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCatModalOpen(true)}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              New Category
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsDeptModalOpen(true)}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              New Department
            </Button>
          </div>
        )}
      </div>

      {/* Departments Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-indigo-400" />
            Company Cost Centers ({departments.length})
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {isLoading ? (
            [...Array(5)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)
          ) : (
            departments.map((dept) => (
              <Card key={dept.id} className="hover-glow border-slate-800 p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    ID: #{dept.id}
                  </span>
                </div>
                <h3 className="font-bold text-slate-100 text-base">{dept.name}</h3>
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                  <span>Lead: <strong className="text-slate-300">{dept.manager_name || 'Executive Staff'}</strong></span>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* Categories Taxonomy Section */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <FolderTree className="w-4 h-4 text-cyan-400" />
            Expense Categories ({categories.length})
          </h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {isLoading ? (
            [...Array(12)].map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)
          ) : (
            categories.map((cat) => (
              <div
                key={cat.id}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md flex flex-col justify-between hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                    style={{ backgroundColor: cat.color_code }}
                  />
                  <span className="font-semibold text-xs text-slate-200 truncate">{cat.name}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">{cat.color_code}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create Department Modal */}
      <Modal isOpen={isDeptModalOpen} onClose={() => setIsDeptModalOpen(false)} title="Add Department">
        <form onSubmit={handleCreateDept} className="space-y-4 text-xs">
          <Input
            label="Department Name"
            value={deptName}
            onChange={(e) => setDeptName(e.target.value)}
            placeholder="e.g. AI & Data Science"
            required
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsDeptModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Create Department
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Category Modal */}
      <Modal isOpen={isCatModalOpen} onClose={() => setIsCatModalOpen(false)} title="Add Expense Category">
        <form onSubmit={handleCreateCat} className="space-y-4 text-xs">
          <Input
            label="Category Name"
            value={catName}
            onChange={(e) => setCatName(e.target.value)}
            placeholder="e.g. Generative AI Subscriptions"
            required
          />
          <Input
            label="Color Hex Code"
            type="text"
            value={catColor}
            onChange={(e) => setCatColor(e.target.value)}
            placeholder="#6366F1"
            required
          />
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="secondary" size="sm" type="button" onClick={() => setIsCatModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Create Category
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
