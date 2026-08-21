import api from './api';
import { AuditLog } from '../types';

export const auditService = {
  async getLogs(limit: number = 100, offset: number = 0): Promise<AuditLog[]> {
    const res = await api.get<AuditLog[]>('/audit', {
      params: { limit, offset },
    });
    return res.data;
  },
};
