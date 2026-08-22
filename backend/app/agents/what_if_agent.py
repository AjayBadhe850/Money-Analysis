import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.department import Department
from app.models.vendor import Vendor
from app.models.subscription import Subscription
from app.models.company import Company

logger = logging.getLogger(__name__)


def _currency_symbol(code: str) -> str:
    return {
        "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£",
        "JPY": "¥", "AUD": "A$", "CAD": "C$"
    }.get(code.upper(), code)


class WhatIfSimulationAgent:
    """
    Deterministic scenario simulation engine evaluating complex financial 'What-If'
    adjustments on expenditure, operating margins, budget variance, and annual cash flow.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        company = db.query(Company).filter(Company.id == company_id).first()
        self.currency_code = (company.currency or "USD") if company else "USD"
        self.currency_sym = _currency_symbol(self.currency_code)

    def simulate(
        self,
        department_spend_adjustments: Optional[Dict[str, float]] = None,
        vendor_price_adjustments: Optional[Dict[str, float]] = None,
        license_utilization_threshold_cut: Optional[float] = None,
        revenue_growth_adjustment: Optional[float] = 0.0,
    ) -> Dict[str, Any]:
        """
        Execute deterministic scenario simulation across company ledgers.
        """
        dept_adj = department_spend_adjustments or {}
        vend_adj = vendor_price_adjustments or {}
        rev_adj = revenue_growth_adjustment or 0.0
        sym = self.currency_sym

        # Fetch baseline data
        txs = self.db.query(Transaction).filter(Transaction.company_id == self.company_id).all()
        dept_map = {d.id: d.name for d in self.db.query(Department).filter(Department.company_id == self.company_id).all()}
        vend_map = {v.id: v.name for v in self.db.query(Vendor).filter(Vendor.company_id == self.company_id).all()}
        subs = self.db.query(Subscription).filter(Subscription.company_id == self.company_id).all()

        exp_txs = [t for t in txs if t.transaction_type == TransactionType.EXPENSE]
        rev_txs = [t for t in txs if t.transaction_type == TransactionType.REVENUE]

        # Calculate number of distinct months in dataset for realistic monthly baseline
        distinct_months = set()
        for t in txs:
            if t.transaction_date:
                distinct_months.add(str(t.transaction_date)[:7])
        num_months = max(1, len(distinct_months))

        total_exp = sum(float(t.amount) for t in exp_txs)
        total_rev = sum(float(t.amount) for t in rev_txs)
        baseline_monthly_expense = total_exp / num_months if total_exp > 0 else 0.0
        baseline_monthly_revenue = total_rev / num_months if total_rev > 0 else 0.0

        # Detailed breakdown impacts
        detailed_impacts = []

        # 1. Department spending adjustments
        dept_spends = {}
        for t in exp_txs:
            d_name = dept_map.get(t.department_id, "General Operations")
            dept_spends[d_name] = dept_spends.get(d_name, 0.0) + (float(t.amount) / num_months)

        sim_dept_total = 0.0
        for d_name, baseline_d_spend in dept_spends.items():
            mult = 1.0
            for adj_name, adj_val in dept_adj.items():
                if adj_name.lower() in d_name.lower():
                    mult += adj_val
                    break
            sim_d_spend = baseline_d_spend * mult
            sim_dept_total += sim_d_spend

            if mult != 1.0:
                detailed_impacts.append({
                    "category": "Department Adjustment",
                    "metric": f"{d_name} Monthly Spend",
                    "baseline_value": round(baseline_d_spend, 2),
                    "simulated_value": round(sim_d_spend, 2),
                    "delta_amount": round(sim_d_spend - baseline_d_spend, 2),
                    "delta_percentage": round((mult - 1.0) * 100, 1),
                })

        # 2. Vendor price adjustments
        vend_spends = {}
        for t in exp_txs:
            v_name = vend_map.get(t.vendor_id, "General Supplier")
            vend_spends[v_name] = vend_spends.get(v_name, 0.0) + (float(t.amount) / num_months)

        for v_name, baseline_v_spend in vend_spends.items():
            for adj_name, adj_val in vend_adj.items():
                if adj_name.lower() in v_name.lower():
                    sim_v_spend = baseline_v_spend * (1.0 + adj_val)
                    detailed_impacts.append({
                        "category": "Vendor Price Shift",
                        "metric": f"{v_name} Spend",
                        "baseline_value": round(baseline_v_spend, 2),
                        "simulated_value": round(sim_v_spend, 2),
                        "delta_amount": round(sim_v_spend - baseline_v_spend, 2),
                        "delta_percentage": round(adj_val * 100, 1),
                    })

        # 3. License utilization threshold cuts
        if license_utilization_threshold_cut is not None:
            sub_cut_savings = 0.0
            for s in subs:
                tot = max(1, s.total_licenses)
                act = min(tot, max(0, s.active_licenses))
                util = act / tot
                if util < license_utilization_threshold_cut:
                    m_cost = float(s.monthly_cost)
                    sub_cut_savings += m_cost
                    detailed_impacts.append({
                        "category": "Underutilized License Cancellation",
                        "metric": f"{s.service_name} (Util: {round(util*100)}%)",
                        "baseline_value": round(m_cost, 2),
                        "simulated_value": 0.0,
                        "delta_amount": round(-m_cost, 2),
                        "delta_percentage": -100.0,
                    })

        # Calculate final aggregated simulation figures
        total_delta = sum(item["delta_amount"] for item in detailed_impacts)
        simulated_monthly_expense = max(0.0, baseline_monthly_expense + total_delta)
        simulated_monthly_revenue = baseline_monthly_revenue * (1.0 + rev_adj)

        baseline_profit = baseline_monthly_revenue - baseline_monthly_expense
        simulated_profit = simulated_monthly_revenue - simulated_monthly_expense

        monthly_savings = baseline_monthly_expense - simulated_monthly_expense
        annual_savings = monthly_savings * 12.0

        baseline_margin = (baseline_profit / baseline_monthly_revenue * 100) if baseline_monthly_revenue > 0 else 0.0
        simulated_margin = (simulated_profit / simulated_monthly_revenue * 100) if simulated_monthly_revenue > 0 else 0.0
        margin_change = simulated_margin - baseline_margin

        narrative = (
            f"Scenario simulation indicates applying the adjustments yields monthly expenditure of "
            f"{sym}{simulated_monthly_expense:,.2f} vs baseline {sym}{baseline_monthly_expense:,.2f} "
            f"({'saving ' + sym if monthly_savings >= 0 else 'increasing ' + sym}{abs(monthly_savings):,.2f}/mo, "
            f"or {'saving ' + sym if annual_savings >= 0 else 'increasing ' + sym}{abs(annual_savings):,.2f} annually). "
            f"Operating profit margin shifts from {baseline_margin:.1f}% to {simulated_margin:.1f}% ({'+' if margin_change >= 0 else ''}{margin_change:.1f}%)."
        )

        return {
            "simulation_name": "Multi-Variable Strategic What-If Simulation",
            "baseline_monthly_expense": round(baseline_monthly_expense, 2),
            "simulated_monthly_expense": round(simulated_monthly_expense, 2),
            "monthly_expense_savings": round(monthly_savings, 2),
            "annual_expense_savings": round(annual_savings, 2),
            "baseline_net_profit": round(baseline_profit, 2),
            "simulated_net_profit": round(simulated_profit, 2),
            "profit_margin_change_pct": round(margin_change, 2),
            "detailed_impacts": detailed_impacts,
            "ai_narrative": narrative,
        }
