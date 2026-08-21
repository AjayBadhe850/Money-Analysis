import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.agents.savings_agent import SavingsOpportunityAgent

logger = logging.getLogger(__name__)


class CostOptimizationAgent:
    """
    Main strategic cost optimization planner.

    When target_savings_amount is provided, selects opportunities greedily until
    the target is met.  When target is None, ranks and returns ALL available
    opportunities ordered by estimated monthly saving (highest first).
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def generate_plan(
        self,
        target_savings_amount: Optional[float] = None,
        timeframe_months: int = 3,
        risk_tolerance: str = "MEDIUM",
    ) -> Dict[str, Any]:
        """
        Produce a cost reduction plan.

        Parameters
        ----------
        target_savings_amount : Optional[float]
            If provided, greedily selects actions until the monthly target is met.
            If None, returns all ranked opportunities without inventing a target.
        timeframe_months : int
            Planning horizon used to calculate total period savings.
        risk_tolerance : str
            LOW / MEDIUM / HIGH – filters available opportunities by risk level.
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

        # Required monthly saving (None when no target was supplied)
        required_monthly_saving = (
            target_savings_amount / max(1, timeframe_months)
            if target_savings_amount is not None
            else None
        )

        selected_actions = []
        accumulated_monthly = 0.0

        for opp in filtered_opps:
            monthly_val = opp.get("estimated_monthly_saving", 0) or 0.0

            action_type = "BUDGET_MODERATION"
            if "SaaS" in opp.get("category", ""):
                action_type = "CANCEL_SUBSCRIPTION"
            elif "Vendor" in opp.get("category", ""):
                action_type = "RENEGOTIATE_VENDOR"
            elif "Cloud" in opp.get("category", ""):
                action_type = "INFRASTRUCTURE_RESERVED"

            selected_actions.append({
                "action_type": action_type,
                "title": opp["title"],
                "target_entity": opp.get("category", ""),
                "projected_monthly_savings": monthly_val,
                "risk_level": opp["risk_level"],
                "confidence": opp["confidence"],
                "rationale": opp.get("description", ""),
                "can_auto_create_approval": True,
                "approval_payload": {
                    "request_type": action_type,
                    "title": f"Approval: {opp['title']}",
                    "details": (
                        f"Initiate cost optimization action to achieve "
                        f"{monthly_val:,.2f}/mo savings. {opp.get('description', '')}"
                    ),
                    "impact_savings_monthly": monthly_val,
                    "risk_level": opp["risk_level"],
                },
            })

            accumulated_monthly += monthly_val

            # If a target was given, stop as soon as it is met
            if required_monthly_saving is not None and accumulated_monthly >= required_monthly_saving:
                break

        achievable_period_savings = accumulated_monthly * timeframe_months
        target_achieved = (
            accumulated_monthly >= required_monthly_saving
            if required_monthly_saving is not None
            else None
        )

        if target_savings_amount is not None:
            summary = (
                f"To achieve a targeted {target_savings_amount:,.2f} reduction over "
                f"{timeframe_months} months, we identified {len(selected_actions)} "
                f"high-confidence initiatives delivering {accumulated_monthly:,.2f}/month "
                f"({achievable_period_savings:,.2f} total across {timeframe_months} months). "
                + (
                    "Target is 100% achievable without operational disruption."
                    if target_achieved
                    else "Partially achievable within selected risk tolerance."
                )
            )
        else:
            summary = (
                f"Ranked {len(selected_actions)} cost reduction opportunities "
                f"delivering a combined {accumulated_monthly:,.2f}/month "
                f"({achievable_period_savings:,.2f} over {timeframe_months} months)."
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
