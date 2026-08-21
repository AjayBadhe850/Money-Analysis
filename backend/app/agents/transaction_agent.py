import logging
from typing import Dict, Any, List, Optional
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
    Specialized agent using Pandas and NumPy to compute deep spending velocity,
    category breakdowns, vendor trends, growth rates, and cash flow relationships.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def analyze(self) -> Dict[str, Any]:
        """
        Execute comprehensive transactional analytics.
        """
        txs = self.db.query(Transaction).filter(Transaction.company_id == self.company_id).all()
        if not txs:
            return {
                "total_transactions": 0,
                "total_expenses": 0.0,
                "total_revenue": 0.0,
                "monthly_burn_rate": 0.0,
                "top_categories": [],
                "top_vendors": [],
                "department_spending": [],
                "expense_growth_rate": 0.0,
            }

        # Convert to Pandas DataFrame
        data = []
        for t in txs:
            data.append({
                "id": t.id,
                "date": pd.to_datetime(t.transaction_date),
                "amount": float(t.amount),
                "type": t.transaction_type.value if hasattr(t.transaction_type, "value") else str(t.transaction_type),
                "department_id": t.department_id,
                "category_id": t.category_id,
                "vendor_id": t.vendor_id,
            })
        df = pd.DataFrame(data)

        # Separate expenses and revenue
        expenses_df = df[df["type"] == TransactionType.EXPENSE.value]
        revenue_df = df[df["type"] == TransactionType.REVENUE.value]

        total_expenses = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0
        total_revenue = float(revenue_df["amount"].sum()) if not revenue_df.empty else 0.0

        # Monthly aggregation
        monthly_trend = []
        growth_rate = 0.0
        if not expenses_df.empty:
            expenses_df["year_month"] = expenses_df["date"].dt.to_period("M").astype(str)
            monthly_grp = expenses_df.groupby("year_month")["amount"].sum().reset_index()
            monthly_trend = monthly_grp.to_dict(orient="records")

            if len(monthly_grp) >= 2:
                recent_month = monthly_grp.iloc[-1]["amount"]
                prev_month = monthly_grp.iloc[-2]["amount"]
                if prev_month > 0:
                    growth_rate = round(((recent_month - prev_month) / prev_month) * 100, 2)

        # Category spending
        cat_map = {c.id: c.name for c in self.db.query(Category).filter(Category.company_id == self.company_id).all()}
        top_categories = []
        if not expenses_df.empty and "category_id" in expenses_df:
            cat_grp = expenses_df.groupby("category_id")["amount"].sum().reset_index()
            cat_grp["category_name"] = cat_grp["category_id"].map(cat_map).fillna("Uncategorized")
            cat_grp = cat_grp.sort_values(by="amount", ascending=False)
            top_categories = cat_grp[["category_name", "amount"]].head(10).to_dict(orient="records")

        # Vendor spending
        vend_map = {v.id: v.name for v in self.db.query(Vendor).filter(Vendor.company_id == self.company_id).all()}
        top_vendors = []
        if not expenses_df.empty and "vendor_id" in expenses_df:
            vend_grp = expenses_df.groupby("vendor_id")["amount"].sum().reset_index()
            vend_grp["vendor_name"] = vend_grp["vendor_id"].map(vend_map).fillna("General Supplier")
            vend_grp = vend_grp.sort_values(by="amount", ascending=False)
            top_vendors = vend_grp[["vendor_name", "amount"]].head(10).to_dict(orient="records")

        # Department spending
        dept_map = {d.id: d.name for d in self.db.query(Department).filter(Department.company_id == self.company_id).all()}
        dept_spending = []
        if not expenses_df.empty and "department_id" in expenses_df:
            dept_grp = expenses_df.groupby("department_id")["amount"].sum().reset_index()
            dept_grp["department_name"] = dept_grp["department_id"].map(dept_map).fillna("General Operations")
            dept_grp = dept_grp.sort_values(by="amount", ascending=False)
            dept_spending = dept_grp[["department_name", "amount"]].to_dict(orient="records")

        # Average Monthly Burn
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
