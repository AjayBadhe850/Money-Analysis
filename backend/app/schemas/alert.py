from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.alert import AlertSeverity, AlertStatus


class CostAlertBase(BaseModel):
    department_id: Optional[int] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    title: str
    message: str
    status: AlertStatus = AlertStatus.OPEN


class CostAlertCreate(CostAlertBase):
    pass


class CostAlertUpdate(BaseModel):
    status: AlertStatus


class CostAlertOut(CostAlertBase):
    id: int
    company_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CostRecommendationOut(BaseModel):
    id: int
    company_id: int
    title: str
    category: str
    potential_monthly_savings: float
    description: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
