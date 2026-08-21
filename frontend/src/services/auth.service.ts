import api from './api';
import { AuthResponse, User } from '../types';

export const authService = {
  async register(data: { name: string; email: string; password: string; role?: string; company_name?: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/register', data);
    return res.data;
  },

  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/login', data);
    return res.data;
  },

  async getCurrentUser(): Promise<User> {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
};
