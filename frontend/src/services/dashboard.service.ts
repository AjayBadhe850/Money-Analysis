import api from './api';
import { DashboardResponse, CostAlert, CostRecommendation } from '../types';

export const dashboardService = {
  async getSummary(): Promise<DashboardResponse> {
    const res = await api.get<DashboardResponse>('/dashboard/summary');
    return res.data;
  },

  async getAlerts(): Promise<CostAlert[]> {
    const res = await api.get<CostAlert[]>('/alerts');
    return res.data;
  },

  async updateAlertStatus(alertId: number, status: string): Promise<CostAlert> {
    const res = await api.put<CostAlert>(`/alerts/${alertId}/status`, { status });
    return res.data;
  },

  async getRecommendations(): Promise<CostRecommendation[]> {
    const res = await api.get<CostRecommendation[]>('/alerts/recommendations');
    return res.data;
  },
};
