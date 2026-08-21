export type UserRole =
  | 'Admin'
  | 'Finance Manager'
  | 'Department Manager'
  | 'Employee'
  | 'Auditor';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  company_id: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type TransactionType = 'EXPENSE' | 'REVENUE';

export interface Transaction {
  id: number;
  company_id: number;
  department_id?: number;
  department_name?: string;
  category_id?: number;
  category_name?: string;
  category_color?: string;
  vendor_id?: number;
  vendor_name?: string;
  transaction_date: string;
  description: string;
  amount: number;
  transaction_type: TransactionType;
  payment_method?: string;
  reference_number?: string;
  created_by?: number;
  created_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  total_expenses_amount: number;
  total_revenue_amount: number;
  net_amount: number;
}

export interface TransactionQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  department_id?: number;
  category_id?: number;
  vendor_id?: number;
  transaction_type?: TransactionType;
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface CSVImportResult {
  success: boolean;
  message: string;
  total_rows: number;
  imported_count: number;
  rejected_count: number;
  duplicates_count: number;
  errors: Array<{ row: number; error: string; data?: any }>;
  imported_transactions?: Array<{
    date: string;
    description: string;
    amount: number;
    type: string;
    department?: string;
    vendor?: string;
  }>;
}

export type BudgetStatus = 'SAFE' | 'WARNING' | 'CRITICAL' | 'EXCEEDED';

export interface Budget {
  id: number;
  company_id: number;
  department_id?: number;
  department_name?: string;
  category_id?: number;
  category_name?: string;
  month?: number;
  year: number;
  allocated_amount: number;
  spent_amount: number;
  usage_percentage: number;
  remaining_amount: number;
  overspent_amount: number;
  status: BudgetStatus;
  notes?: string;
  created_at: string;
}

export interface BudgetSummaryResponse {
  year: number;
  month?: number;
  total_allocated: number;
  total_spent: number;
  total_remaining: number;
  overall_usage_percentage: number;
  safe_count: number;
  warning_count: number;
  critical_count: number;
  exceeded_count: number;
  budgets: Budget[];
}

export interface Vendor {
  id: number;
  company_id: number;
  name: string;
  contact_email?: string;
  category?: string;
  reliability_score: number;
  quality_score: number;
  average_delivery_days: number;
  total_spend: number;
  transaction_count: number;
  average_transaction_value: number;
  created_at: string;
}

export type SubscriptionStatus = 'ACTIVE' | 'CANCELLED' | 'UNDER_REVIEW';

export interface Subscription {
  id: number;
  company_id: number;
  department_id?: number;
  department_name?: string;
  vendor_id?: number;
  vendor?: string;
  service_name: string;
  monthly_cost: number;
  annual_cost: number;
  total_licenses: number;
  active_licenses: number;
  unused_licenses: number;
  utilization_percentage: number;
  per_seat_cost: number;
  estimated_monthly_waste: number;
  estimated_annual_waste: number;
  has_waste_flag: boolean;
  renewal_date: string;
  status: SubscriptionStatus;
  created_at: string;
}

export interface SubscriptionSummaryResponse {
  total_monthly_spend: number;
  total_annual_spend: number;
  total_licenses: number;
  active_licenses: number;
  overall_utilization_percentage: number;
  potential_monthly_savings: number;
  potential_annual_savings: number;
  subscriptions: Subscription[];
}

export type InvoiceStatus = 'PENDING' | 'PAID' | 'OVERDUE' | 'CANCELLED';

export interface Invoice {
  id: number;
  company_id: number;
  vendor_id?: number;
  vendor_name?: string;
  invoice_number: string;
  issue_date: string;
  due_date: string;
  amount: number;
  status: InvoiceStatus;
  is_overdue: boolean;
  created_at: string;
}

export interface InvoiceSummaryResponse {
  total_invoiced: number;
  total_paid: number;
  total_pending: number;
  total_overdue: number;
  invoices: Invoice[];
}

export interface Department {
  id: number;
  company_id: number;
  name: string;
  manager_id?: number;
  manager_name?: string;
  created_at: string;
}

export interface Category {
  id: number;
  company_id: number;
  name: string;
  color_code: string;
  created_at: string;
}

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface CostAlert {
  id: number;
  company_id: number;
  department_id?: number;
  department_name?: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  status: string;
  created_at: string;
}

export interface CostRecommendation {
  id: number;
  company_id: number;
  title: string;
  category: string;
  potential_monthly_savings: number;
  description: string;
  status: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  company_id: number;
  user_id?: number;
  user_name?: string;
  user_email?: string;
  action: string;
  entity: string;
  entity_id?: number;
  details?: string;
  ip_address?: string;
  timestamp: string;
}

export interface KPICards {
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  profit_margin_pct: number;
  allocated_budget: number;
  budget_used_pct: number;
  budget_remaining: number;
  potential_savings: number;
  active_alerts_count: number;
  monthly_budget?: number;
  budget_used?: number;
  open_alerts_count?: number;
  active_subscriptions_count?: number;
  total_vendors_count?: number;
}

export interface MonthlyComparisonItem {
  month: string;
  revenue: number;
  expenses: number;
  net: number;
}

export interface CategoryExpenseItem {
  category_name: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface DepartmentSpendingItem {
  department_name: string;
  spent_amount: number;
  budget_amount: number;
}

export interface BudgetVsActualItem {
  name: string;
  allocated: number;
  spent: number;
  variance: number;
  status: string;
}

export interface ExpenseTrendPoint {
  date: string;
  amount: number;
}

export interface DashboardCharts {
  revenue_vs_expenses: MonthlyComparisonItem[];
  expense_categories: CategoryExpenseItem[];
  department_spending: DepartmentSpendingItem[];
  budget_vs_actual: BudgetVsActualItem[];
  expense_trend: ExpenseTrendPoint[];
  monthly_expense_trend?: ExpenseTrendPoint[];
}

export interface DashboardResponse {
  kpis: KPICards;
  charts: DashboardCharts;
  recent_transactions: Transaction[];
  active_alerts: CostAlert[];
}

// ================= STAGE 2 AI MULTI-AGENT TYPES =================

export interface CitationItem {
  source: string;
  detail: string;
  url?: string;
}

export interface ChatResponse {
  message: string;
  agents_involved: string[];
  tools_executed: string[];
  evidence_cards: Array<{
    title: string;
    value: string;
    detail: string;
    type: 'savings' | 'warning' | 'anomaly' | 'forecast';
  }>;
  suggested_actions: Array<{
    action: string;
    label: string;
    savings?: number;
    severity?: string;
  }>;
  citations: CitationItem[];
}

export interface AnomalyItem {
  id: number;
  transaction_id?: number;
  transaction_date?: string;
  transaction_description?: string;
  transaction_amount?: number;
  vendor_name?: string;
  department_name?: string;
  anomaly_score: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  explanation: string;
  reasons: string[];
  status: string;
  detected_at: string;
}

export interface AnomalyScanResponse {
  scanned_count: number;
  anomalies_detected: number;
  anomalies: AnomalyItem[];
  scan_timestamp: string;
}

export interface ForecastSeriesItem {
  period: string;
  predicted_amount: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

export interface ForecastResponse {
  horizon_days: number;
  model_type: string;
  total_projected_spend: number;
  historical_growth_rate: number;
  trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  confidence_score: number;
  projected_budget_problems: Array<{
    risk: string;
    description: string;
    severity: string;
  }>;
  series: ForecastSeriesItem[];
}

export interface WhatIfImpactItem {
  category: string;
  metric: string;
  baseline_value: number;
  simulated_value: number;
  delta_amount: number;
  delta_percentage: number;
}

export interface WhatIfResponse {
  simulation_name: string;
  baseline_monthly_expense: number;
  simulated_monthly_expense: number;
  monthly_expense_savings: number;
  annual_expense_savings: number;
  baseline_net_profit: number;
  simulated_net_profit: number;
  profit_margin_change_pct: number;
  detailed_impacts: WhatIfImpactItem[];
  ai_narrative: string;
}

export interface SavingsOpportunityItem {
  id?: number;
  title: string;
  description: string;
  category: string;
  estimated_monthly_saving: number;
  estimated_annual_saving: number;
  confidence: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  evidence: Record<string, any>;
  source_agent: string;
}

export interface SavingsOpportunitiesResponse {
  total_potential_monthly: number;
  total_potential_annual: number;
  opportunities_count: number;
  opportunities: SavingsOpportunityItem[];
}

export interface OptimizationActionItem {
  action_type: string;
  title: string;
  target_entity: string;
  projected_monthly_savings: number;
  risk_level: string;
  confidence: number;
  rationale: string;
  can_auto_create_approval: boolean;
  approval_payload?: Record<string, any>;
}

export interface CostOptimizationPlanResponse {
  target_savings: number;
  timeframe_months: number;
  achievable_monthly_savings: number;
  achievable_total_period_savings: number;
  target_achieved: boolean;
  recommended_actions: OptimizationActionItem[];
  executive_summary: string;
}

export interface ApprovalResponse {
  id: number;
  request_type: string;
  title: string;
  details: string;
  impact_savings_monthly: number;
  risk_level: string;
  action_payload?: Record<string, any>;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED';
  requester_name?: string;
  approver_name?: string;
  response_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export interface CategorizeResponse {
  description: string;
  predicted_category: string;
  confidence_score: number;
  prediction_method: string;
}

export interface DocumentRecord {
  id: number;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  uploaded_at: string;
}

export interface DocumentQueryResponse {
  query: string;
  answer: string;
  retrieved_chunks: Array<{
    document_id: number;
    filename: string;
    chunk_index: number;
    chunk_text: string;
    similarity_score: number;
  }>;
}

export interface CostEfficiencyScoreResponse {
  overall_score: number;
  grade: string;
  components: {
    budget_control: { score: number; max: number; metric: string };
    vendor_efficiency: { score: number; max: number; metric: string };
    subscription_utilization: { score: number; max: number; metric: string };
    expense_stability: { score: number; max: number; metric: string };
    anomaly_control: { score: number; max: number; metric: string };
  };
}
