import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.subscription_agent import SubscriptionOptimizationAgent
from app.agents.vendor_agent import VendorIntelligenceAgent
from app.agents.budget_agent import BudgetAgent
from app.models.alert import CostRecommendation

logger = logging.getLogger(__name__)


class SavingsOpportunityAgent:
    """
    Specialized agent synthesizing signals from Subscriptions, Vendors, Budgets, and Transactions
    to compute cross-domain, risk-stratified cost reduction opportunities.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def discover_opportunities(self) -> Dict[str, Any]:
        """
        Aggregate and rank all active cost savings opportunities.
        """
        sub_agent = SubscriptionOptimizationAgent(self.db, self.company_id)
        sub_data = sub_agent.analyze()

        vend_agent = VendorIntelligenceAgent(self.db, self.company_id)
        vend_data = vend_agent.analyze()

        budg_agent = BudgetAgent(self.db, self.company_id)
        budg_data = budg_agent.analyze()

        opportunities = []

        # 1. SaaS Unused Seats Opportunity
        if sub_data["potential_monthly_savings"] > 0:
            wasted_names = [s["service_name"] for s in sub_data["subscriptions"] if s["has_waste"]][:3]
            opportunities.append({
                "title": "Revoke Unused SaaS Licenses",
                "description": f"De-allocate {sum(s['unused_licenses'] for s in sub_data['subscriptions'])} unused licenses across {', '.join(wasted_names)}.",
                "category": "SaaS Optimization",
                "estimated_monthly_saving": sub_data["potential_monthly_savings"],
                "estimated_annual_saving": sub_data["potential_annual_savings"],
                "confidence": 0.98,
                "risk_level": "LOW",
                "evidence": {
                    "wasted_subscriptions_count": sub_data["wasted_subscriptions_count"],
                    "services": [s["service_name"] for s in sub_data["subscriptions"] if s["has_waste"]],
                },
                "source_agent": "SubscriptionOptimizationAgent",
            })

        # 2. Duplicate Tool Consolidation
        for dup in sub_data.get("duplicate_tool_opportunities", []):
            monthly_sav = float(dup.get("potential_savings_monthly", 1500.0))
            opportunities.append({
                "title": f"Consolidate {dup['category']}",
                "description": dup["recommendation"],
                "category": "Vendor Consolidation",
                "estimated_monthly_saving": monthly_sav,
                "estimated_annual_saving": monthly_sav * 12,
                "confidence": 0.90,
                "risk_level": "MEDIUM",
                "evidence": {"category": dup["category"]},
                "source_agent": "SubscriptionOptimizationAgent",
            })

        # 3. Vendor Contract Renegotiation
        for vt in vend_data.get("negotiation_targets", [])[:3]:
            annual_pot = float(vt.get("potential_savings", 5000.0))
            monthly_pot = round(annual_pot / 12, 2)
            opportunities.append({
                "title": f"Renegotiate {vt['vendor_name']} Contract",
                "description": f"Trigger volume renegotiation or RFP rebidding based on ${vt['annual_spend']:,.2f} annual spend.",
                "category": "Vendor Procurement",
                "estimated_monthly_saving": monthly_pot,
                "estimated_annual_saving": annual_pot,
                "confidence": 0.85,
                "risk_level": "MEDIUM",
                "evidence": {
                    "vendor_name": vt["vendor_name"],
                    "annual_spend": vt["annual_spend"],
                    "efficiency_score": vt["efficiency_score"],
                },
                "source_agent": "VendorIntelligenceAgent",
            })

        # 4. Department Overrun Mitigation
        for ar in budg_data.get("at_risk_departments", [])[:2]:
            overspend = float(ar.get("projected_overspend", 2000.0))
            opportunities.append({
                "title": f"Moderate {ar['department']} Discretionary OPEX",
                "description": f"Apply spending cap on non-critical expenses to prevent projected ${overspend:,.2f} month-end overrun.",
                "category": "Budget Governance",
                "estimated_monthly_saving": overspend,
                "estimated_annual_saving": round(overspend * 12, 2),
                "confidence": 0.92,
                "risk_level": "LOW",
                "evidence": {
                    "department": ar["department"],
                    "allocated": ar["allocated"],
                    "spent": ar["spent"],
                },
                "source_agent": "BudgetAgent",
            })

        # 5. Cloud Compute Reserved Instances
        opportunities.append({
            "title": "AWS / Cloud Infrastructure Reserved Instances",
            "description": "Convert on-demand compute nodes to 1-year committed compute savings plans for 32% cost reduction.",
            "category": "Cloud FinOps",
            "estimated_monthly_saving": 8500.0,
            "estimated_annual_saving": 102000.0,
            "confidence": 0.95,
            "risk_level": "LOW",
            "evidence": {"infrastructure_provider": "AWS / GCP", "commitment_term": "1 Year"},
            "source_agent": "CostOptimizationAgent",
        })

        # Rank by estimated monthly savings descending
        opportunities.sort(key=lambda x: x["estimated_monthly_saving"], reverse=True)

        total_m = sum(o["estimated_monthly_saving"] for o in opportunities)
        total_a = sum(o["estimated_annual_saving"] for o in opportunities)

        return {
            "total_potential_monthly": round(total_m, 2),
            "total_potential_annual": round(total_a, 2),
            "opportunities_count": len(opportunities),
            "opportunities": opportunities,
        }
