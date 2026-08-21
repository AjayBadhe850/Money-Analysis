from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.subscription import SubscriptionStatus
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionOut, SubscriptionSummaryResponse
)
from app.auth.rbac import get_current_user, require_roles
from app.services.subscription_service import (
    get_subscriptions_summary, create_subscription, update_subscription, delete_subscription
)
from app.services.audit_service import log_activity

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=SubscriptionSummaryResponse)
def list_subscriptions(
    status: Optional[SubscriptionStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_subscriptions_summary(db=db, company_id=company_id, status=status)


@router.post("", response_model=SubscriptionOut)
def create_new_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    s = create_subscription(db=db, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="CREATE_SUBSCRIPTION",
        entity="Subscription",
        entity_id=str(s.id),
        details=f"Created subscription for '{s.service_name}' (${s.monthly_cost}/mo)"
    )

    summary = get_subscriptions_summary(db=db, company_id=company_id)
    for so in summary.subscriptions:
        if so.id == s.id:
            return so

    return SubscriptionOut(
        id=s.id,
        company_id=s.company_id,
        department_id=s.department_id,
        vendor_id=s.vendor_id,
        vendor=s.vendor,
        service_name=s.service_name,
        monthly_cost=s.monthly_cost,
        total_licenses=s.total_licenses,
        active_licenses=s.active_licenses,
        renewal_date=s.renewal_date,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at
    )


@router.put("/{subscription_id}", response_model=SubscriptionOut)
def edit_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    s = update_subscription(db=db, subscription_id=subscription_id, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="UPDATE_SUBSCRIPTION",
        entity="Subscription",
        entity_id=str(s.id),
        details=f"Updated subscription {subscription_id} ({s.service_name})"
    )

    summary = get_subscriptions_summary(db=db, company_id=company_id)
    for so in summary.subscriptions:
        if so.id == s.id:
            return so

    return SubscriptionOut(
        id=s.id,
        company_id=s.company_id,
        department_id=s.department_id,
        vendor_id=s.vendor_id,
        vendor=s.vendor,
        service_name=s.service_name,
        monthly_cost=s.monthly_cost,
        total_licenses=s.total_licenses,
        active_licenses=s.active_licenses,
        renewal_date=s.renewal_date,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at
    )


@router.delete("/{subscription_id}")
def remove_subscription(
    subscription_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    delete_subscription(db=db, subscription_id=subscription_id, company_id=company_id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="DELETE_SUBSCRIPTION",
        entity="Subscription",
        entity_id=str(subscription_id),
        details=f"Deleted subscription {subscription_id}"
    )
    return {"message": "Subscription deleted successfully"}
