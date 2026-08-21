import logging
from typing import Dict, Any, List, Optional
from datetime import date
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


class TransactionAnalysisAgent:
    """
    Specialized agent using Pandas and NumPy to compute spending velocity,
    category breakdowns, vendor trends, growth rates, and cash flow relationships.

    All queries are scoped to self.company_id (tenant isolation).
    Optional date range and department filters enable period-aware metrics.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def analyze(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        department_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute comprehensive transactional analytics.

        Parameters
        ----------
        start_date : Optional[date]
            Inclusive lower bound for transaction_date filter.
        end_date : Optional[date]
            Inclusive upper bound for transaction_date filter.
        department_name : Optional[str]
            If provided, restrict expense calculations to this department only.
        """
        # ── Base query – always company-scoped ───────────────────────────────
        query = self.db.query(Transaction).filter(
            Transaction.company_id == self.company_id
        )

        # ── Optional date filters ─────────────────────────────────────────────
        if start_date is not None:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date is not None:
            query = query.filter(Transaction.transaction_date <= end_date)

        # ── Optional department filter ────────────────────────────────────────
        dept_id: Optional[int] = None
        if department_name:
            dept_obj = (
                self.db.query(Department)
                .filter(
                    Department.company_id == self.company_id,
                    Department.name.ilike(f"%{department_name}%"),
                )
                .first()
            )
            if dept_obj:
                dept_id = dept_obj.id
                query = query.filter(Transaction.department_id == dept_id)

        txs = query.all()

        empty = {
            "total_transactions": 0,
            "total_expenses": 0.0,
            "total_revenue": 0.0,
            "net_profit": 0.0,
            "monthly_burn_rate": 0.0,
            "expense_growth_rate": 0.0,
            "monthly_trend": [],
            "top_categories": [],
            "top_vendors": [],
            "department_spending": [],
        }

        if not txs:
            return empty

        # ── Build DataFrame ───────────────────────────────────────────────────
        data = []
        for t in txs:
            data.append({
                "id": t.id,
                "date": pd.to_datetime(t.transaction_date),
                "amount": float(t.amount),
                "type": (
                    t.transaction_type.value
                    if hasattr(t.transaction_type, "value")
                    else str(t.transaction_type)
                ),
                "department_id": t.department_id,
                "category_id": t.category_id,
                "vendor_id": t.vendor_id,
            })
        df = pd.DataFrame(data)

        expenses_df = df[df["type"] == TransactionType.EXPENSE.value]
        revenue_df = df[df["type"] == TransactionType.REVENUE.value]

        total_expenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
        total_revenue = float(revenue_df["amount"].sum()) if not revenue_df.empty else 0.0

        # ── Monthly aggregation ───────────────────────────────────────────────
        monthly_trend: List[Dict] = []
        growth_rate = 0.0
        if not expenses_df.empty:
            expenses_df = expenses_df.copy()
            expenses_df["year_month"] = expenses_df["date"].dt.to_period("M").astype(str)
            monthly_grp = expenses_df.groupby("year_month")["amount"].sum().reset_index()
            monthly_trend = monthly_grp.to_dict(orient="records")

            if len(monthly_grp) >= 2:
                recent_month = monthly_grp.iloc[-1]["amount"]
                prev_month = monthly_grp.iloc[-2]["amount"]
                if prev_month > 0:
                    growth_rate = round(((recent_month - prev_month) / prev_month) * 100, 2)

        # ── Category breakdown (company-scoped) ───────────────────────────────
        cat_map = {
            c.id: c.name
            for c in self.db.query(Category)
            .filter(Category.company_id == self.company_id)
            .all()
        }
        top_categories: List[Dict] = []
        if not expenses_df.empty and "category_id" in expenses_df.columns:
            cat_grp = expenses_df.groupby("category_id")["amount"].sum().reset_index()
            cat_grp["category_name"] = cat_grp["category_id"].map(cat_map).fillna("Uncategorized")
            cat_grp = cat_grp.sort_values(by="amount", ascending=False)
            top_categories = cat_grp[["category_name", "amount"]].head(10).to_dict(orient="records")

        # ── Vendor breakdown (company-scoped) ─────────────────────────────────
        vend_map = {
            v.id: v.name
            for v in self.db.query(Vendor)
            .filter(Vendor.company_id == self.company_id)
            .all()
        }
        top_vendors: List[Dict] = []
        if not expenses_df.empty and "vendor_id" in expenses_df.columns:
            vend_grp = expenses_df.groupby("vendor_id")["amount"].sum().reset_index()
            vend_grp["vendor_name"] = vend_grp["vendor_id"].map(vend_map).fillna("General Supplier")
            vend_grp = vend_grp.sort_values(by="amount", ascending=False)
            top_vendors = vend_grp[["vendor_name", "amount"]].head(10).to_dict(orient="records")

        # ── Department breakdown (company-scoped) ─────────────────────────────
        dept_map = {
            d.id: d.name
            for d in self.db.query(Department)
            .filter(Department.company_id == self.company_id)
            .all()
        }
        dept_spending: List[Dict] = []
        if not expenses_df.empty and "department_id" in expenses_df.columns:
            dept_grp = expenses_df.groupby("department_id")["amount"].sum().reset_index()
            dept_grp["department_name"] = dept_grp["department_id"].map(dept_map).fillna("General Operations")
            dept_grp = dept_grp.sort_values(by="amount", ascending=False)
            dept_spending = dept_grp[["department_name", "amount"]].to_dict(orient="records")

        # ── Monthly burn (average per month in scope) ─────────────────────────
        num_months = max(1, len(monthly_trend))
        monthly_burn = round(total_expenses / num_months, 2)

        return {
            "total_transactions": len(df),
            "total_expenses": round(total_expenses, 2),
            "total_revenue": round(total_revenue, 2),
            "net_profit": round(total_revenue - total_expenses, 2),
            "monthly_burn_rate": monthly_burn,
            "expense_growth_rate": growth_rate,
            "monthly_trend": monthly_trend,
            "top_categories": top_categories,
            "top_vendors": top_vendors,
            "department_spending": dept_spending,
        }
