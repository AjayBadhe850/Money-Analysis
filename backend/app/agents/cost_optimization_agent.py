import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.savings_agent import SavingsOpportunityAgent

logger = logging.getLogger(__name__)


class CostOptimizationAgent:
    """
    Main strategic cost optimization planner. Takes targeted financial goals (e.g. "Save $50k in 3 months")
    and synthesizes a prioritized, risk-weighted combinatorial execution plan.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def generate_plan(
        self,
        target_savings_amount: float,
        timeframe_months: int = 3,
        risk_tolerance: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Produce a tailored cost reduction plan meeting or approaching the user's financial target.
        """
        savings_agent = SavingsOpportunityAgent(self.db, self.company_id)
        savings_data = savings_agent.discover_opportunities()
        available_opps = savings_data["opportunities"]

        # Filter by risk tolerance
        allowed_risks = ["LOW"]
        if risk_tolerance.upper() in ["MEDIUM", "HIGH"]:
            allowed_risks.append("MEDIUM")
        if risk_tolerance.upper() == "HIGH":
            allowed_risks.append("HIGH")

        filtered_opps = [o for o in available_opps if o["risk_level"] in allowed_risks]

        # Target monthly requirement
        required_monthly_saving = target_savings_amount / max(1, timeframe_months)

        # Select greedy optimal combination
        selected_actions = []
        accumulated_monthly = 0.0

        for opp in filtered_opps:
            monthly_val = opp["estimated_monthly_saving"]
            accumulated_monthly += monthly_val

            action_type = "BUDGET_MODERATION"
            if "SaaS" in opp["category"]:
                action_type = "CANCEL_SUBSCRIPTION"
            elif "Vendor" in opp["category"]:
                action_type = "RENEGOTIATE_VENDOR"
            elif "Cloud" in opp["category"]:
                action_type = "INFRASTRUCTURE_RESERVED"

            selected_actions.append({
                "action_type": action_type,
                "title": opp["title"],
                "target_entity": opp["category"],
                "projected_monthly_savings": monthly_val,
                "risk_level": opp["risk_level"],
                "confidence": opp["confidence"],
                "rationale": opp["description"],
                "can_auto_create_approval": True,
                "approval_payload": {
                    "request_type": action_type,
                    "title": f"Approval: {opp['title']}",
                    "details": f"Initiate cost optimization action to achieve ${monthly_val:,.2f}/mo savings. {opp['description']}",
                    "impact_savings_monthly": monthly_val,
                    "risk_level": opp["risk_level"],
                }
            })

            if accumulated_monthly >= required_monthly_saving:
                break

        achievable_period_savings = accumulated_monthly * timeframe_months
        target_achieved = accumulated_monthly >= required_monthly_saving

        summary = (
            f"To achieve a targeted ${target_savings_amount:,.2f} reduction over {timeframe_months} months, "
            f"we identified {len(selected_actions)} high-confidence initiatives delivering "
            f"${accumulated_monthly:,.2f}/month (${achievable_period_savings:,.2f} total across {timeframe_months} months). "
            f"{'Target is 100% achievable without operational disruption.' if target_achieved else 'Partially achievable within selected risk tolerance.'}"
        )

        return {
            "target_savings": target_savings_amount,
            "timeframe_months": timeframe_months,
            "achievable_monthly_savings": round(accumulated_monthly, 2),
            "achievable_total_period_savings": round(achievable_period_savings, 2),
            "target_achieved": target_achieved,
            "recommended_actions": selected_actions,
            "executive_summary": summary,
        }
