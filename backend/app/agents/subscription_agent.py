import logging
from datetime import datetime, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

MONEY_PLACES = Decimal("0.01")
PERCENT_PLACES = Decimal("0.1")


class SubscriptionOptimizationAgent:
    """
    Specialized agent for detecting unused and underutilized software
    licenses, calculating deterministic seat waste, tracking renewals,
    and identifying duplicate tooling.

    All authoritative monetary calculations use Decimal.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def analyze(self) -> Dict[str, Any]:
        """
        Audit SaaS subscriptions for license reclamation and
        consolidation opportunities.

        All database queries are isolated by company_id.
        """
        subs = (
            self.db.query(Subscription)
            .filter(Subscription.company_id == self.company_id)
            .all()
        )

        departments = (
            self.db.query(Department)
            .filter(Department.company_id == self.company_id)
            .all()
        )

        dept_map = {
            department.id: department.name
            for department in departments
        }

        total_monthly = Decimal("0.00")
        total_monthly_waste = Decimal("0.00")

        optimization_items = []
        upcoming_renewals = []

        today = datetime.now(timezone.utc).date()

        for subscription in subs:
            # ---------------------------------------------------------
            # Monetary values
            # ---------------------------------------------------------
            monthly_cost = Decimal(
                str(subscription.monthly_cost or 0)
            ).quantize(
                MONEY_PLACES,
                rounding=ROUND_HALF_UP,
            )

            # ---------------------------------------------------------
            # License counts
            # ---------------------------------------------------------
            total_licenses = max(
                0,
                subscription.total_licenses or 0,
            )

            active_licenses = max(
                0,
                subscription.active_licenses or 0,
            )

            if total_licenses > 0:
                active_licenses = min(
                    active_licenses,
                    total_licenses,
                )

                unused_licenses = (
                    total_licenses - active_licenses
                )

                utilization_pct = (
                    Decimal(active_licenses)
                    / Decimal(total_licenses)
                    * Decimal(100)
                ).quantize(
                    PERCENT_PLACES,
                    rounding=ROUND_HALF_UP,
                )

                per_seat_cost = (
                    monthly_cost
                    / Decimal(total_licenses)
                ).quantize(
                    MONEY_PLACES,
                    rounding=ROUND_HALF_UP,
                )

            else:
                active_licenses = 0
                unused_licenses = 0
                utilization_pct = Decimal("0.0")
                per_seat_cost = Decimal("0.00")

            # ---------------------------------------------------------
            # Deterministic waste calculations
            # ---------------------------------------------------------
            monthly_waste = (
                Decimal(unused_licenses)
                * per_seat_cost
            ).quantize(
                MONEY_PLACES,
                rounding=ROUND_HALF_UP,
            )

            annual_waste = (
                monthly_waste * Decimal(12)
            ).quantize(
                MONEY_PLACES,
                rounding=ROUND_HALF_UP,
            )

            annual_cost = (
                monthly_cost * Decimal(12)
            ).quantize(
                MONEY_PLACES,
                rounding=ROUND_HALF_UP,
            )

            total_monthly += monthly_cost
            total_monthly_waste += monthly_waste

            has_waste = (
                unused_licenses > 0
                and monthly_waste > Decimal("0.00")
            )

            # ---------------------------------------------------------
            # Department
            # ---------------------------------------------------------
            if subscription.department_id:
                department_name = dept_map.get(
                    subscription.department_id,
                    "Unknown Department",
                )
            else:
                department_name = "Global"

            # ---------------------------------------------------------
            # Renewal date
            # ---------------------------------------------------------
            days_to_renewal = None
            renewal_date_value = None

            if subscription.renewal_date:
                try:
                    if isinstance(subscription.renewal_date, datetime):
                        renewal_date = subscription.renewal_date.date()
                    elif isinstance(subscription.renewal_date, date):
                        renewal_date = subscription.renewal_date
                    elif isinstance(subscription.renewal_date, str):
                        renewal_date = datetime.strptime(
                            subscription.renewal_date[:10],
                            "%Y-%m-%d",
                        ).date()
                    else:
                        raise TypeError(
                            f"Unsupported renewal date type: {type(subscription.renewal_date).__name__}"
                        )

                    renewal_date_value = str(renewal_date)
                    days_to_renewal = (renewal_date - today).days

                except (ValueError, TypeError) as exc:
                    logger.warning(
                        "Invalid renewal date for subscription %s: %s",
                        subscription.id,
                        exc,
                    )

            # ---------------------------------------------------------
            # Subscription result
            # ---------------------------------------------------------
            item = {
                "subscription_id": subscription.id,
                "service_name": subscription.service_name,
                "vendor": (
                    subscription.vendor
                    or "Direct Supplier"
                ),
                "department": department_name,
                "monthly_cost": float(monthly_cost),
                "annual_cost": float(annual_cost),
                "total_licenses": total_licenses,
                "active_licenses": active_licenses,
                "unused_licenses": unused_licenses,
                "utilization_percentage": float(utilization_pct),
                "per_seat_cost": float(per_seat_cost),
                "estimated_monthly_waste": float(monthly_waste),
                "estimated_annual_waste": float(annual_waste),
                "has_waste": has_waste,
                "renewal_date": renewal_date_value,
                "days_to_renewal": days_to_renewal,
            }

            optimization_items.append(item)

            # ---------------------------------------------------------
            # Upcoming renewals
            # ---------------------------------------------------------
            if (
                days_to_renewal is not None
                and 0 <= days_to_renewal <= 60
            ):
                if has_waste:
                    action = (
                        f"Review {unused_licenses} unused seats before renewal."
                    )
                else:
                    action = (
                        "Review contract pricing and renewal terms."
                    )

                upcoming_renewals.append({
                    "subscription_id": subscription.id,
                    "service_name": subscription.service_name,
                    "monthly_cost": float(monthly_cost),
                    "renewal_date": renewal_date_value,
                    "days_remaining": days_to_renewal,
                    "action": action,
                })

        # -------------------------------------------------------------
        # Duplicate / overlapping tool detection
        # -------------------------------------------------------------
        tool_names = [
            str(subscription.service_name or "").lower()
            for subscription in subs
        ]

        duplicate_clusters = []

        communication_count = sum(
            1
            for name in tool_names
            if any(
                tool in name
                for tool in (
                    "slack",
                    "teams",
                    "zoom",
                    "meet",
                )
            )
        )

        if communication_count >= 2:
            duplicate_clusters.append({
                "category": "Team Communication & Conferencing",
                "recommendation": (
                    "Multiple communication and meeting platforms were detected. "
                    "Review whether these tools can be consolidated."
                ),
                "potential_savings_monthly": None,
                "calculation_status": "INSUFFICIENT_DATA",
            })

        project_management_count = sum(
            1
            for name in tool_names
            if any(
                tool in name
                for tool in (
                    "jira",
                    "asana",
                    "notion",
                    "monday",
                    "trello",
                )
            )
        )

        if project_management_count >= 2:
            duplicate_clusters.append({
                "category": "Project & Task Management",
                "recommendation": (
                    "Multiple project-management tools were detected. "
                    "Review consolidation opportunities."
                ),
                "potential_savings_monthly": None,
                "calculation_status": "INSUFFICIENT_DATA",
            })

        # -------------------------------------------------------------
        # Sort largest verified waste first
        # -------------------------------------------------------------
        optimization_items.sort(
            key=lambda item: item["estimated_monthly_waste"],
            reverse=True,
        )

        # -------------------------------------------------------------
        # Final deterministic totals
        # -------------------------------------------------------------
        total_monthly = total_monthly.quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

        total_monthly_waste = total_monthly_waste.quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

        total_annual = (total_monthly * Decimal(12)).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

        total_annual_waste = (total_monthly_waste * Decimal(12)).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

        return {
            "total_monthly_spend": float(total_monthly),
            "total_annual_spend": float(total_annual),
            "potential_monthly_savings": float(total_monthly_waste),
            "potential_annual_savings": float(total_annual_waste),
            "subscriptions_count": len(subs),
            "wasted_subscriptions_count": sum(
                1 for item in optimization_items if item["has_waste"]
            ),
            "subscriptions": optimization_items,
            "upcoming_renewals": upcoming_renewals,
            "duplicate_tool_opportunities": duplicate_clusters,
        }