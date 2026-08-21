from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.alert import CostAlert, CostRecommendation, AlertStatus
from app.schemas.alert import CostAlertOut, CostAlertUpdate, CostRecommendationOut
from app.auth.rbac import get_current_user, require_roles
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/alerts", tags=["Alerts & Recommendations"])


@router.get("", response_model=List[CostAlertOut])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return db.query(CostAlert).filter(CostAlert.company_id == company_id).order_by(CostAlert.created_at.desc()).all()


@router.put("/{alert_id}/status", response_model=CostAlertOut)
def update_alert_status(
    alert_id: int,
    data: CostAlertUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.DEPARTMENT_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    alert = db.query(CostAlert).filter(CostAlert.id == alert_id, CostAlert.company_id == company_id).first()
    if not alert:
        raise ResourceNotFoundException("Alert", str(alert_id))
    
    alert.status = data.status
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/recommendations", response_model=List[CostRecommendationOut])
def list_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return db.query(CostRecommendation).filter(CostRecommendation.company_id == company_id).all()
