from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.alert import CostAlert, AlertStatus
from app.schemas.budget import BudgetStatus
from app.schemas.dashboard import (
    KPICards, MonthlyComparisonItem, CategoryExpenseItem,
    DepartmentSpendingItem, BudgetVsActualItem, ExpenseTrendPoint, DashboardCharts
)


def calculate_total_revenue(
    db: Session,
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None
) -> float:
    query = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type == TransactionType.REVENUE
    )
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if department_id:
        query = query.filter(Transaction.department_id == department_id)
    return float(query.scalar() or 0.0)


def calculate_total_expenses(
    db: Session,
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None
) -> float:
    query = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type == TransactionType.EXPENSE
    )
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if department_id:
        query = query.filter(Transaction.department_id == department_id)
    return float(query.scalar() or 0.0)


def calculate_net_profit(total_revenue: float, total_expenses: float) -> float:
    return round(total_revenue - total_expenses, 2)


def calculate_budget_usage(allocated_amount: float, spent_amount: float) -> Dict[str, Any]:
    if allocated_amount <= 0:
        usage_pct = 100.0 if spent_amount > 0 else 0.0
    else:
        usage_pct = round((spent_amount / allocated_amount) * 100.0, 2)
    
    remaining = round(max(0.0, allocated_amount - spent_amount), 2)
    overspent = round(max(0.0, spent_amount - allocated_amount), 2)
    
    if usage_pct < 70.0:
        status = BudgetStatus.SAFE
    elif 70.0 <= usage_pct < 85.0:
        status = BudgetStatus.WARNING
    elif 85.0 <= usage_pct <= 100.0:
        status = BudgetStatus.CRITICAL
    else:
        status = BudgetStatus.EXCEEDED

    return {
        "usage_percentage": usage_pct,
        "remaining_amount": remaining,
        "overspent_amount": overspent,
        "status": status
    }


def calculate_department_spending(
    db: Session,
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DepartmentSpendingItem]:
    departments = db.query(Department).filter(Department.company_id == company_id).all()
    results = []
    
    current_year = date.today().year
    
    for dept in departments:
        spend_query = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
            Transaction.company_id == company_id,
            Transaction.department_id == dept.id,
            Transaction.transaction_type == TransactionType.EXPENSE
        )
        if start_date:
            spend_query = spend_query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            spend_query = spend_query.filter(Transaction.transaction_date <= end_date)
        
        spent = float(spend_query.scalar() or 0.0)
        
        # Calculate budget allocated for department
        budget_query = db.query(func.coalesce(func.sum(Budget.allocated_amount), 0.0)).filter(
            Budget.company_id == company_id,
            Budget.department_id == dept.id,
            Budget.year == current_year
        )
        budget = float(budget_query.scalar() or 0.0)
        
        pct = round((spent / budget * 100.0), 2) if budget > 0 else 0.0
        
        results.append(DepartmentSpendingItem(
            department_id=dept.id,
            department_name=dept.name,
            spent_amount=round(spent, 2),
            budget_amount=round(budget, 2),
            percentage=pct
        ))
    
    return results


def calculate_category_spending(
    db: Session,
    company_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[CategoryExpenseItem]:
    categories = db.query(Category).filter(Category.company_id == company_id).all()
    total_expenses = calculate_total_expenses(db, company_id, start_date, end_date)
    
    results = []
    for cat in categories:
        query = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
            Transaction.company_id == company_id,
            Transaction.category_id == cat.id,
            Transaction.transaction_type == TransactionType.EXPENSE
        )
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        amount = float(query.scalar() or 0.0)
        if amount > 0:
            percentage = round((amount / total_expenses * 100.0), 2) if total_expenses > 0 else 0.0
            results.append(CategoryExpenseItem(
                category_id=cat.id,
                category_name=cat.name,
                amount=round(amount, 2),
                percentage=percentage,
                color=cat.color_code or "#6366F1"
            ))
    
    # Sort descending by amount
    results.sort(key=lambda x: x.amount, reverse=True)
    return results


def calculate_vendor_spending(db: Session, vendor_id: int) -> Dict[str, Any]:
    transactions = db.query(Transaction).filter(
        Transaction.vendor_id == vendor_id,
        Transaction.transaction_type == TransactionType.EXPENSE
    ).all()
    
    total_spend = sum(t.amount for t in transactions)
    count = len(transactions)
    avg_val = round(total_spend / count, 2) if count > 0 else 0.0
    
    return {
        "total_spend": round(total_spend, 2),
        "transaction_count": count,
        "average_transaction_value": avg_val
    }


def calculate_subscription_cost(sub: Subscription) -> Dict[str, Any]:
    annual_cost = round(sub.monthly_cost * 12.0, 2)
    total_lic = max(1, sub.total_licenses)
    active_lic = min(total_lic, max(0, sub.active_licenses))
    unused = max(0, total_lic - active_lic)
    utilization_pct = round((active_lic / total_lic) * 100.0, 2)
    
    # Deterministic rule for potential waste: (unused / total) * monthly_cost
    cost_per_seat = sub.monthly_cost / total_lic
    est_monthly_waste = round(unused * cost_per_seat, 2)
    est_annual_waste = round(est_monthly_waste * 12.0, 2)
    has_waste = unused > 0 and est_monthly_waste > 0
    
    return {
        "annual_cost": annual_cost,
        "utilization_percentage": utilization_pct,
        "unused_licenses": unused,
        "estimated_monthly_waste": est_monthly_waste,
        "estimated_annual_waste": est_annual_waste,
        "has_waste_flag": has_waste
    }


def get_dashboard_summary(db: Session, company_id: int) -> Dict[str, Any]:
    # 1. Total Revenue and Expenses (all-time & current period)
    total_revenue = calculate_total_revenue(db, company_id)
    total_expenses = calculate_total_expenses(db, company_id)
    net_profit = calculate_net_profit(total_revenue, total_expenses)
    margin_pct = round((net_profit / total_revenue * 100.0), 2) if total_revenue > 0 else 0.0

    # 2. Budgets
    current_year = date.today().year
    budgets = db.query(Budget).filter(
        Budget.company_id == company_id,
        Budget.year == current_year
    ).all()
    
    total_budget_alloc = sum(b.allocated_amount for b in budgets)
    total_budget_spent = sum(b.spent_amount for b in budgets)
    budget_usage = calculate_budget_usage(total_budget_alloc, total_budget_spent)

    # 3. Subscriptions & Potential Savings
    subscriptions = db.query(Subscription).filter(
        Subscription.company_id == company_id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    potential_savings = 0.0
    for sub in subscriptions:
        sub_metrics = calculate_subscription_cost(sub)
        potential_savings += sub_metrics["estimated_monthly_waste"]
    
    # 4. Open Alerts & Vendor Counts
    open_alerts_count = db.query(CostAlert).filter(
        CostAlert.company_id == company_id,
        CostAlert.status == AlertStatus.OPEN
    ).count()

    vendors_count = db.query(Vendor).filter(Vendor.company_id == company_id).count()

    kpis = KPICards(
        total_revenue=round(total_revenue, 2),
        total_expenses=round(total_expenses, 2),
        net_profit=round(net_profit, 2),
        profit_margin_pct=margin_pct,
        monthly_budget=round(total_budget_alloc, 2),
        budget_used=round(total_budget_spent, 2),
        budget_remaining=budget_usage["remaining_amount"],
        budget_used_pct=budget_usage["usage_percentage"],
        potential_savings=round(potential_savings, 2),
        open_alerts_count=open_alerts_count,
        active_subscriptions_count=len(subscriptions),
        total_vendors_count=vendors_count
    )

    # 5. Monthly Revenue vs Expenses Chart Data
    # Fetch transactions grouped by month
    all_transactions = db.query(Transaction).filter(
        Transaction.company_id == company_id
    ).order_by(Transaction.transaction_date.asc()).all()

    monthly_data: Dict[str, Dict[str, float]] = {}
    for t in all_transactions:
        m_key = t.transaction_date.strftime("%Y-%m")
        if m_key not in monthly_data:
            monthly_data[m_key] = {"revenue": 0.0, "expenses": 0.0}
        if t.transaction_type == TransactionType.REVENUE:
            monthly_data[m_key]["revenue"] += t.amount
        else:
            monthly_data[m_key]["expenses"] += t.amount

    rev_vs_exp_items = []
    trend_points = []
    cumulative_spend = 0.0

    for m_key in sorted(monthly_data.keys()):
        rev = round(monthly_data[m_key]["revenue"], 2)
        exp = round(monthly_data[m_key]["expenses"], 2)
        cumulative_spend += exp
        
        # Human readable month e.g. "Aug 2026"
        dt = datetime.strptime(m_key, "%Y-%m")
        month_label = dt.strftime("%b %Y")

        rev_vs_exp_items.append(MonthlyComparisonItem(
            month=month_label,
            revenue=rev,
            expenses=exp,
            net_profit=round(rev - exp, 2)
        ))

        trend_points.append(ExpenseTrendPoint(
            date=month_label,
            amount=exp,
            cumulative=round(cumulative_spend, 2)
        ))

    # 6. Categories Chart Data
    cat_items = calculate_category_spending(db, company_id)

    # 7. Department Spending Chart Data
    dept_items = calculate_department_spending(db, company_id)

    # 8. Budget vs Actual Comparison Chart Data
    budget_vs_actual_items = []
    for b in budgets:
        name = "Company Wide"
        if b.department:
            name = f"{b.department.name}"
        elif b.category:
            name = f"{b.category.name}"
        
        b_metrics = calculate_budget_usage(b.allocated_amount, b.spent_amount)
        budget_vs_actual_items.append(BudgetVsActualItem(
            name=name,
            budget=round(b.allocated_amount, 2),
            actual=round(b.spent_amount, 2),
            variance=round(b.allocated_amount - b.spent_amount, 2),
            status=b_metrics["status"].value
        ))

    charts = DashboardCharts(
        revenue_vs_expenses=rev_vs_exp_items,
        expense_categories=cat_items,
        department_spending=dept_items,
        budget_vs_actual=budget_vs_actual_items,
        monthly_expense_trend=trend_points
    )

    return {
        "kpis": kpis,
        "charts": charts
    }
