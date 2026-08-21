import api from './api';
import { Vendor } from '../types';

export const vendorService = {
  async getVendors(): Promise<Vendor[]> {
    const res = await api.get<Vendor[]>('/vendors');
    return res.data;
  },

  async getVendor(id: number): Promise<Vendor> {
    const res = await api.get<Vendor>(`/vendors/${id}`);
    return res.data;
  },

  async createVendor(data: Partial<Vendor>): Promise<Vendor> {
    const res = await api.post<Vendor>('/vendors', data);
    return res.data;
  },

  async updateVendor(id: number, data: Partial<Vendor>): Promise<Vendor> {
    const res = await api.put<Vendor>(`/vendors/${id}`, data);
    return res.data;
  },

  async deleteVendor(id: number): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/vendors/${id}`);
    return res.data;
  },
};
