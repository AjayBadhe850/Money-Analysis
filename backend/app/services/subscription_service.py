from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.department import Department
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionOut, SubscriptionSummaryResponse
)
from app.services.finance_service import calculate_subscription_cost
from app.core.exceptions import ResourceNotFoundException


def get_subscriptions_summary(
    db: Session,
    company_id: int,
    status: Optional[SubscriptionStatus] = None
) -> SubscriptionSummaryResponse:
    query = db.query(Subscription).filter(Subscription.company_id == company_id)
    if status:
        query = query.filter(Subscription.status == status)

    raw_subs = query.all()

    total_monthly = 0.0
    total_annual = 0.0
    total_lic = 0
    total_active_lic = 0
    total_unused_lic = 0
    total_potential_monthly_savings = 0.0

    sub_outs: List[SubscriptionOut] = []

    for sub in raw_subs:
        metrics = calculate_subscription_cost(sub)
        
        total_monthly += sub.monthly_cost
        total_annual += metrics["annual_cost"]
        total_lic += sub.total_licenses
        total_active_lic += sub.active_licenses
        total_unused_lic += metrics["unused_licenses"]
        total_potential_monthly_savings += metrics["estimated_monthly_waste"]

        out = SubscriptionOut(
            id=sub.id,
            company_id=sub.company_id,
            department_id=sub.department_id,
            vendor_id=sub.vendor_id,
            vendor=sub.vendor or (sub.vendor_rel.name if sub.vendor_rel else "N/A"),
            service_name=sub.service_name,
            monthly_cost=round(sub.monthly_cost, 2),
            total_licenses=sub.total_licenses,
            active_licenses=sub.active_licenses,
            renewal_date=sub.renewal_date,
            status=sub.status,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            department_name=sub.department.name if sub.department else "All Departments",
            annual_cost=metrics["annual_cost"],
            utilization_percentage=metrics["utilization_percentage"],
            unused_licenses=metrics["unused_licenses"],
            estimated_monthly_waste=metrics["estimated_monthly_waste"],
            estimated_annual_waste=metrics["estimated_annual_waste"],
            has_waste_flag=metrics["has_waste_flag"]
        )
        sub_outs.append(out)

    overall_utilization = (
        round((total_active_lic / total_lic) * 100.0, 2) if total_lic > 0 else 100.0
    )

    return SubscriptionSummaryResponse(
        total_monthly_spend=round(total_monthly, 2),
        total_annual_spend=round(total_annual, 2),
        total_licenses=total_lic,
        total_active_licenses=total_active_lic,
        total_unused_licenses=total_unused_lic,
        overall_utilization_rate=overall_utilization,
        potential_monthly_savings=round(total_potential_monthly_savings, 2),
        potential_annual_savings=round(total_potential_monthly_savings * 12.0, 2),
        subscriptions=sub_outs
    )


def create_subscription(db: Session, company_id: int, data: SubscriptionCreate) -> Subscription:
    sub = Subscription(
        company_id=company_id,
        department_id=data.department_id,
        vendor_id=data.vendor_id,
        vendor=data.vendor,
        service_name=data.service_name,
        monthly_cost=data.monthly_cost,
        total_licenses=data.total_licenses,
        active_licenses=data.active_licenses,
        renewal_date=data.renewal_date,
        status=data.status
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_subscription(
    db: Session,
    subscription_id: int,
    company_id: int,
    data: SubscriptionUpdate
) -> Subscription:
    sub = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.company_id == company_id
    ).first()
    if not sub:
        raise ResourceNotFoundException("Subscription", str(subscription_id))

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(sub, field, val)

    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, subscription_id: int, company_id: int) -> bool:
    sub = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.company_id == company_id
    ).first()
    if not sub:
        raise ResourceNotFoundException("Subscription", str(subscription_id))

    db.delete(sub)
    db.commit()
    return True
