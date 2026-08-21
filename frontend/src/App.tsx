import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { AppLayout } from './components/layout/AppLayout';

import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { BudgetsPage } from './pages/BudgetsPage';
import { DepartmentsPage } from './pages/DepartmentsPage';
import { VendorsPage } from './pages/VendorsPage';
import { SubscriptionsPage } from './pages/SubscriptionsPage';
import { InvoicesPage } from './pages/InvoicesPage';
import { ReportsPage } from './pages/ReportsPage';
import { AlertsPage } from './pages/AlertsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AgentTimelinePage } from './pages/AgentTimelinePage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { ForecastsPage } from './pages/ForecastsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { DocumentsRAGPage } from './pages/DocumentsRAGPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Application Workspace */}
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/budgets" element={<BudgetsPage />} />
              <Route path="/departments" element={<DepartmentsPage />} />
              <Route path="/vendors" element={<VendorsPage />} />
              <Route path="/subscriptions" element={<SubscriptionsPage />} />
              <Route path="/invoices" element={<InvoicesPage />} />
              <Route path="/reports" element={<ReportsPage />} />

              {/* Stage 2 & 3 Multi-Agent AI Routes */}
              <Route path="/ai/assistant" element={<AIAssistantPage />} />
              <Route path="/ai-assistant" element={<Navigate to="/ai/assistant" replace />} />
              <Route path="/ai/timeline" element={<AgentTimelinePage />} />
              <Route path="/ai/optimization" element={<OptimizationPage />} />
              <Route path="/optimization" element={<Navigate to="/ai/optimization" replace />} />
              <Route path="/ai/anomalies" element={<AnomaliesPage />} />
              <Route path="/ai/forecasts" element={<ForecastsPage />} />
              <Route path="/ai/approvals" element={<ApprovalsPage />} />
              <Route path="/ai/documents" element={<DocumentsRAGPage />} />

              {/* System */}
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/audit-logs" element={<AuditLogsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
