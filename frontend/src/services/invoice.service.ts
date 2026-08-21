import api from './api';
import { Invoice, InvoiceSummaryResponse, InvoiceStatus } from '../types';

export const invoiceService = {
  async getInvoices(vendorId?: number, status?: InvoiceStatus): Promise<InvoiceSummaryResponse> {
    const res = await api.get<InvoiceSummaryResponse>('/invoices', {
      params: { vendor_id: vendorId, status },
    });
    return res.data;
  },

  async createInvoice(data: Partial<Invoice>): Promise<Invoice> {
    const res = await api.post<Invoice>('/invoices', data);
    return res.data;
  },

  async updateInvoice(id: number, data: Partial<Invoice>): Promise<Invoice> {
    const res = await api.put<Invoice>(`/invoices/${id}`, data);
    return res.data;
  },

  async deleteInvoice(id: number): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/invoices/${id}`);
    return res.data;
  },
};
