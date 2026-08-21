from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    entity: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    company_id: int
    user_id: Optional[int] = None


class AuditLogOut(AuditLogBase):
    id: int
    company_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
