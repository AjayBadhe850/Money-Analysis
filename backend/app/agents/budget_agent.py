import logging
from datetime import datetime, timezone
import calendar
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.models.department import Department
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)


class BudgetAgent:
    """
    Specialized agent monitoring budget allocations, spending burn velocity,
    month-end projections, and overspending warning risks.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def analyze(self) -> Dict[str, Any]:
        """
        Evaluate all company budgets and project overrun risks.
        """
        now = datetime.now(timezone.utc)
        current_year = now.year
        current_month = now.month
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        day_of_month = max(1, now.day)
        month_progress_pct = (day_of_month / days_in_month) * 100

        budgets = self.db.query(Budget).filter(
            Budget.company_id == self.company_id,
            Budget.year == current_year
        ).all()

        dept_map = {d.id: d.name for d in self.db.query(Department).filter(Department.company_id == self.company_id).all()}
        cat_map = {c.id: c.name for c in self.db.query(Category).filter(Category.company_id == self.company_id).all()}

        total_allocated = 0.0
        total_spent = 0.0
        budget_lines = []
        at_risk_departments = []

        for b in budgets:
            allocated = float(b.allocated_amount)
            spent = float(b.spent_amount)
            total_allocated += allocated
            total_spent += spent

            # Spending Velocity and Month-End Projection
            daily_run_rate = spent / day_of_month if day_of_month > 0 else 0.0
            projected_month_end = round(daily_run_rate * days_in_month, 2)
            expected_overspend = max(0.0, projected_month_end - allocated)
            usage_pct = (spent / allocated * 100) if allocated > 0 else 0.0

            status = "SAFE"
            if usage_pct > 100 or expected_overspend > 0:
                status = "EXCEEDED" if usage_pct > 100 else "CRITICAL"
            elif usage_pct >= 85:
                status = "CRITICAL"
            elif usage_pct >= 70:
                status = "WARNING"

            dept_name = dept_map.get(b.department_id, "All Departments") if b.department_id else "All Departments"
            cat_name = cat_map.get(b.category_id, "All Categories") if b.category_id else "All Categories"

            item = {
                "budget_id": b.id,
                "department": dept_name,
                "category": cat_name,
                "allocated": allocated,
                "spent": spent,
                "usage_percentage": round(usage_pct, 1),
                "daily_burn_rate": round(daily_run_rate, 2),
                "projected_month_end": projected_month_end,
                "expected_overspend": round(expected_overspend, 2),
                "status": status,
                "is_at_risk": status in ["WARNING", "CRITICAL", "EXCEEDED"],
            }
            budget_lines.append(item)

            if item["is_at_risk"] and dept_name != "All Departments":
                at_risk_departments.append({
                    "department": dept_name,
                    "allocated": allocated,
                    "spent": spent,
                    "projected_overspend": round(expected_overspend, 2),
                    "status": status,
                    "severity": "CRITICAL" if status in ["CRITICAL", "EXCEEDED"] else "WARNING",
                })

        overall_usage = (total_spent / total_allocated * 100) if total_allocated > 0 else 0.0

        return {
            "total_allocated": round(total_allocated, 2),
            "total_spent": round(total_spent, 2),
            "overall_usage_pct": round(overall_usage, 1),
            "month_progress_pct": round(month_progress_pct, 1),
            "days_remaining_in_month": days_in_month - day_of_month,
            "budget_lines": budget_lines,
            "at_risk_departments": at_risk_departments,
            "critical_count": len([b for b in budget_lines if b["status"] in ["CRITICAL", "EXCEEDED"]]),
            "safe_count": len([b for b in budget_lines if b["status"] == "SAFE"]),
        }
