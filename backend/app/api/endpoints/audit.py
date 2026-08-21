from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogOut
from app.auth.rbac import get_current_user, require_roles
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.AUDITOR])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_audit_logs(db=db, company_id=company_id, limit=limit, offset=offset)
