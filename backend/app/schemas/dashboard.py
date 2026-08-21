from typing import List, Optional
from pydantic import BaseModel


class KPICards(BaseModel):
    total_revenue: float
    total_expenses: float
    net_profit: float
    profit_margin_pct: float
    monthly_budget: float
    budget_used: float
    budget_remaining: float
    budget_used_pct: float
    potential_savings: float
    open_alerts_count: int
    active_subscriptions_count: int
    total_vendors_count: int


class MonthlyComparisonItem(BaseModel):
    month: str           # "Jan 2026", "2026-01"
    revenue: float
    expenses: float
    net_profit: float


class CategoryExpenseItem(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    amount: float
    percentage: float
    color: str


class DepartmentSpendingItem(BaseModel):
    department_id: Optional[int] = None
    department_name: str
    spent_amount: float
    budget_amount: float
    percentage: float


class BudgetVsActualItem(BaseModel):
    name: str            # Department or Category name
    budget: float
    actual: float
    variance: float
    status: str          # SAFE, WARNING, CRITICAL, EXCEEDED


class ExpenseTrendPoint(BaseModel):
    date: str            # "YYYY-MM" or "YYYY-MM-DD"
    amount: float
    cumulative: float


class DashboardCharts(BaseModel):
    revenue_vs_expenses: List[MonthlyComparisonItem]
    expense_categories: List[CategoryExpenseItem]
    department_spending: List[DepartmentSpendingItem]
    budget_vs_actual: List[BudgetVsActualItem]
    monthly_expense_trend: List[ExpenseTrendPoint]


class DashboardResponse(BaseModel):
    kpis: KPICards
    charts: DashboardCharts
