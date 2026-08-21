from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auth.rbac import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services.finance_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    data = get_dashboard_summary(db=db, company_id=company_id)
    return DashboardResponse(
        kpis=data["kpis"],
        charts=data["charts"]
    )
