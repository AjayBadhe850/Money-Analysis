import logging
from typing import Dict, Any, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.models.department import Department

logger = logging.getLogger(__name__)


class SubscriptionOptimizationAgent:
    """
    Specialized agent detecting unused and underutilized software licenses,
    calculating seat waste, tracking contract renewals, and identifying duplicate tooling.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def analyze(self) -> Dict[str, Any]:
        """
        Audit all SaaS subscriptions for license reclamation and consolidation opportunities.
        """
        subs = self.db.query(Subscription).filter(Subscription.company_id == self.company_id).all()
        dept_map = {d.id: d.name for d in self.db.query(Department).filter(Department.company_id == self.company_id).all()}

        total_monthly = 0.0
        total_monthly_waste = 0.0
        optimization_items = []
        upcoming_renewals = []
        today = date.today()

        for s in subs:
            m_cost = float(s.monthly_cost)
            total_licenses = max(1, s.total_licenses)
            active_licenses = min(total_licenses, max(0, s.active_licenses))
            unused_licenses = total_licenses - active_licenses
            utilization_pct = (active_licenses / total_licenses) * 100

            # Deterministic seat cost & waste
            per_seat_cost = m_cost / total_licenses
            monthly_waste = unused_licenses * per_seat_cost
            annual_waste = monthly_waste * 12

            total_monthly += m_cost
            total_monthly_waste += monthly_waste

            has_waste = unused_licenses > 0
            dept_name = dept_map.get(s.department_id, "Global") if s.department_id else "Global"

            # Check renewal urgency
            days_to_renewal = 999
            if s.renewal_date:
                try:
                    if isinstance(s.renewal_date, str):
                        r_date = datetime.strptime(s.renewal_date, "%Y-%m-%d").date()
                    else:
                        r_date = s.renewal_date
                    days_to_renewal = (r_date - today).days
                except Exception:
                    pass

            item = {
                "subscription_id": s.id,
                "service_name": s.service_name,
                "vendor": s.vendor or "Direct Supplier",
                "department": dept_name,
                "monthly_cost": round(m_cost, 2),
                "annual_cost": round(m_cost * 12, 2),
                "total_licenses": total_licenses,
                "active_licenses": active_licenses,
                "unused_licenses": unused_licenses,
                "utilization_percentage": round(utilization_pct, 1),
                "per_seat_cost": round(per_seat_cost, 2),
                "estimated_monthly_waste": round(monthly_waste, 2),
                "estimated_annual_waste": round(annual_waste, 2),
                "has_waste": has_waste,
                "renewal_date": str(s.renewal_date),
                "days_to_renewal": days_to_renewal,
            }
            optimization_items.append(item)

            if 0 <= days_to_renewal <= 60:
                upcoming_renewals.append({
                    "service_name": s.service_name,
                    "monthly_cost": round(m_cost, 2),
                    "renewal_date": str(s.renewal_date),
                    "days_remaining": days_to_renewal,
                    "action": f"Audit {unused_licenses} unused seats before automatic renewal." if has_waste else "Review annual contract rates."
                })

        # Find duplicate / similar tool clusters
        # Group by category heuristics – report as recommendation only, no fabricated savings
        tool_names = [s.service_name.lower() for s in subs]
        duplicate_clusters = []
        if sum(1 for name in tool_names if "slack" in name or "teams" in name or "zoom" in name or "meet" in name) >= 2:
            duplicate_clusters.append({
                "category": "Team Communication & Conferencing",
                "recommendation": "Multiple communication & meeting platforms detected. Standardize on single workspace vendor.",
                "potential_savings_monthly": None,  # Cannot be calculated without actual seat pricing data
            })
        if sum(1 for name in tool_names if "jira" in name or "asana" in name or "notion" in name or "monday" in name or "trello" in name) >= 2:
            duplicate_clusters.append({
                "category": "Project & Task Management",
                "recommendation": "Multiple project management licenses in use across departments. Consolidate to unified seat license.",
                "potential_savings_monthly": None,  # Cannot be calculated without actual seat pricing data
            })

        optimization_items.sort(key=lambda x: x["estimated_monthly_waste"], reverse=True)

        return {
            "total_monthly_spend": round(total_monthly, 2),
            "total_annual_spend": round(total_monthly * 12, 2),
            "potential_monthly_savings": round(total_monthly_waste, 2),
            "potential_annual_savings": round(total_monthly_waste * 12, 2),
            "subscriptions_count": len(subs),
            "wasted_subscriptions_count": len([s for s in optimization_items if s["has_waste"]]),
            "subscriptions": optimization_items,
            "upcoming_renewals": upcoming_renewals,
            "duplicate_tool_opportunities": duplicate_clusters,
        }
