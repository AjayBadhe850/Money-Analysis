import api from './api';
import { Subscription, SubscriptionSummaryResponse, SubscriptionStatus } from '../types';

export const subscriptionService = {
  async getSubscriptions(status?: SubscriptionStatus): Promise<SubscriptionSummaryResponse> {
    const res = await api.get<SubscriptionSummaryResponse>('/subscriptions', {
      params: { status },
    });
    return res.data;
  },

  async createSubscription(data: Partial<Subscription>): Promise<Subscription> {
    const res = await api.post<Subscription>('/subscriptions', data);
    return res.data;
  },

  async updateSubscription(id: number, data: Partial<Subscription>): Promise<Subscription> {
    const res = await api.put<Subscription>(`/subscriptions/${id}`, data);
    return res.data;
  },

  async deleteSubscription(id: number): Promise<{ message: string }> {
    const res = await api.delete<{ message: string }>(`/subscriptions/${id}`);
    return res.data;
  },
};
