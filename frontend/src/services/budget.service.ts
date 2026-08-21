import api from './api';
import { Budget, BudgetSummaryResponse } from '../types';

export const budgetService = {
  async getBudgets(year?: number, departmentId?: number): Promise<BudgetSummaryResponse> {
    const res = await api.get<BudgetSummaryResponse>('/budgets', {
      params: { year, department_id: departmentId },
    });
    return res.data;
  },

  async createBudget(data: Partial<Budget>): Promise<Budget> {
    const res = await api.post<Budget>('/budgets', data);
    return res.data;
  },

  async updateBudget(id: number, data: Partial<Budget>): Promise<Budget> {
    const res = await api.put<Budget>(`/budgets/${id}`, data);
    return res.data;
  },

  async deleteBudget(id: number): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/budgets/${id}`);
    return res.data;
  },
};
