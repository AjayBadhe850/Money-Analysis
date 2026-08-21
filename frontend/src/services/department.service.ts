import api from './api';
import { Department, Category, AuditLog } from '../types';

export const departmentService = {
  async getDepartments(): Promise<Department[]> {
    const res = await api.get<Department[]>('/departments');
    return res.data;
  },

  async createDepartment(data: { name: string; manager_id?: number }): Promise<Department> {
    const res = await api.post<Department>('/departments', data);
    return res.data;
  },

  async getCategories(): Promise<Category[]> {
    const res = await api.get<Category[]>('/categories');
    return res.data;
  },

  async createCategory(data: { name: string; color_code: string }): Promise<Category> {
    const res = await api.post<Category>('/categories', data);
    return res.data;
  },
};

export const auditService = {
  async getLogs(limit: number = 100, offset: number = 0): Promise<AuditLog[]> {
    const res = await api.get<AuditLog[]>('/audit', {
      params: { limit, offset },
    });
    return res.data;
  },
};
