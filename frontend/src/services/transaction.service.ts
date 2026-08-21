import api from './api';
import { Transaction, TransactionListResponse } from '../types';

export interface TransactionQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  start_date?: string;
  end_date?: string;
  department_id?: number;
  category_id?: number;
  vendor_id?: number;
  transaction_type?: string;
  min_amount?: number;
  max_amount?: number;
  sort_by?: string;
  sort_order?: string;
}

export const transactionService = {
  async getTransactions(params?: TransactionQueryParams): Promise<TransactionListResponse> {
    const res = await api.get<TransactionListResponse>('/transactions', { params });
    return res.data;
  },

  async createTransaction(data: Partial<Transaction>): Promise<Transaction> {
    const res = await api.post<Transaction>('/transactions', data);
    return res.data;
  },

  async updateTransaction(id: number, data: Partial<Transaction>): Promise<Transaction> {
    const res = await api.put<Transaction>(`/transactions/${id}`, data);
    return res.data;
  },

  async deleteTransaction(id: number): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/transactions/${id}`);
    return res.data;
  },

  async importCSV(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/transactions/import-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async downloadCSVTemplate(): Promise<Blob> {
    const res = await api.get('/transactions/export-csv-template', {
      responseType: 'blob',
    });
    return res.data;
  },
};
