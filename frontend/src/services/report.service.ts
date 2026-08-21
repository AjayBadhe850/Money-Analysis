import api from './api';

export interface AutomationStatusResponse {
  tasks: Record<string, { last_run: string | null; status: string; details: string }>;
  scheduler: string;
  active: boolean;
}

export const reportService = {
  async getMonthlyReport(): Promise<any> {
    const res = await api.get('/reports/monthly');
    return res.data;
  },

  async downloadMonthlyPdf(): Promise<void> {
    const res = await api.get('/reports/monthly/pdf', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Money_Analysis_Financial_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async getAutomationStatus(): Promise<AutomationStatusResponse> {
    const res = await api.get<AutomationStatusResponse>('/reports/automation-status');
    return res.data;
  },
};
