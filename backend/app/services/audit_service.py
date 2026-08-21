from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogOut


def log_activity(
    db: Session,
    company_id: int,
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    log_entry = AuditLog(
        company_id=company_id,
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    company_id: int,
    limit: int = 100,
    offset: int = 0
) -> List[AuditLogOut]:
    logs = db.query(AuditLog).filter(
        AuditLog.company_id == company_id
    ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    result = []
    for log in logs:
        out = AuditLogOut(
            id=log.id,
            company_id=log.company_id,
            user_id=log.user_id,
            action=log.action,
            entity=log.entity,
            entity_id=log.entity_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
            user_name=log.user.name if log.user else "System",
            user_email=log.user.email if log.user else None
        )
        result.append(out)
    return result
