import api from './api';
import {
  ChatResponse,
  AnomalyItem,
  AnomalyScanResponse,
  ForecastResponse,
  WhatIfResponse,
  SavingsOpportunitiesResponse,
  CostOptimizationPlanResponse,
  ApprovalResponse,
  CategorizeResponse,
  DocumentRecord,
  DocumentQueryResponse,
  CostEfficiencyScoreResponse,
} from '../types';

export const aiService = {
  async sendMessage(message: string): Promise<ChatResponse> {
    const res = await api.post<ChatResponse>('/ai/chat', { message });
    return res.data;
  },

  async getAnomalies(): Promise<AnomalyItem[]> {
    const res = await api.get<AnomalyItem[]>('/ai/anomalies');
    return res.data;
  },

  async scanAnomalies(contamination: number = 0.08): Promise<AnomalyScanResponse> {
    const res = await api.post<AnomalyScanResponse>('/ai/anomalies/scan', null, {
      params: { contamination },
    });
    return res.data;
  },

  async updateAnomalyStatus(id: number, status: string): Promise<any> {
    const res = await api.put(`/ai/anomalies/${id}/status`, { status });
    return res.data;
  },

  async generateForecast(horizon_days: number = 90, department_id?: number): Promise<ForecastResponse> {
    const res = await api.post<ForecastResponse>('/ai/forecasts/generate', {
      horizon_days,
      department_id,
    });
    return res.data;
  },

  async simulateWhatIf(payload: {
    department_spend_adjustments?: Record<string, number>;
    vendor_price_adjustments?: Record<string, number>;
    license_utilization_threshold_cut?: number;
    revenue_growth_adjustment?: number;
  }): Promise<WhatIfResponse> {
    const res = await api.post<WhatIfResponse>('/ai/what-if', payload);
    return res.data;
  },

  async getRecommendations(): Promise<SavingsOpportunitiesResponse> {
    const res = await api.get<SavingsOpportunitiesResponse>('/ai/recommendations');
    return res.data;
  },

  async generateOptimizationPlan(
    target_savings_amount: number,
    timeframe_months: number = 3,
    risk_tolerance: string = 'MEDIUM'
  ): Promise<CostOptimizationPlanResponse> {
    const res = await api.post<CostOptimizationPlanResponse>('/ai/optimize', {
      target_savings_amount,
      timeframe_months,
      risk_tolerance,
    });
    return res.data;
  },

  async getApprovals(status_filter?: string): Promise<ApprovalResponse[]> {
    const res = await api.get<ApprovalResponse[]>('/ai/approvals', {
      params: status_filter ? { status_filter } : {},
    });
    return res.data;
  },

  async createApproval(payload: {
    request_type: string;
    title: string;
    details: string;
    impact_savings_monthly: number;
    risk_level: string;
    action_payload?: Record<string, any>;
  }): Promise<ApprovalResponse> {
    const res = await api.post<ApprovalResponse>('/ai/approvals', payload);
    return res.data;
  },

  async approveRequest(id: number, notes?: string): Promise<any> {
    const res = await api.post(`/ai/approvals/${id}/approve`, { notes });
    return res.data;
  },

  async rejectRequest(id: number, notes?: string): Promise<any> {
    const res = await api.post(`/ai/approvals/${id}/reject`, { notes });
    return res.data;
  },

  async categorize(description: string, vendor?: string): Promise<CategorizeResponse> {
    const res = await api.post<CategorizeResponse>('/ai/categorize', { description, vendor });
    return res.data;
  },

  async correctCategory(keyword: string, correct_category: string): Promise<any> {
    const res = await api.post('/ai/categorize/correct', { keyword, correct_category });
    return res.data;
  },

  async getDocuments(): Promise<DocumentRecord[]> {
    const res = await api.get<DocumentRecord[]>('/ai/documents');
    return res.data;
  },

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/ai/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async queryDocuments(query: string, top_k: number = 4): Promise<DocumentQueryResponse> {
    const res = await api.post<DocumentQueryResponse>('/ai/documents/query', { query, top_k });
    return res.data;
  },

  async getCostEfficiencyScore(): Promise<CostEfficiencyScoreResponse> {
    const res = await api.get<CostEfficiencyScoreResponse>('/ai/cost-efficiency-score');
    return res.data;
  },
};
