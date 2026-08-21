from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.subscription import SubscriptionStatus


class SubscriptionBase(BaseModel):
    service_name: str
    vendor: Optional[str] = None
    vendor_id: Optional[int] = None
    department_id: Optional[int] = None
    monthly_cost: float = Field(ge=0)
    total_licenses: int = Field(ge=1, default=1)
    active_licenses: int = Field(ge=0, default=1)
    renewal_date: date
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    service_name: Optional[str] = None
    vendor: Optional[str] = None
    vendor_id: Optional[int] = None
    department_id: Optional[int] = None
    monthly_cost: Optional[float] = Field(default=None, ge=0)
    total_licenses: Optional[int] = Field(default=None, ge=1)
    active_licenses: Optional[int] = Field(default=None, ge=0)
    renewal_date: Optional[date] = None
    status: Optional[SubscriptionStatus] = None


class SubscriptionOut(SubscriptionBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    # Deterministic analytics
    department_name: Optional[str] = None
    annual_cost: float = 0.0
    utilization_percentage: float = 100.0
    unused_licenses: int = 0
    estimated_monthly_waste: float = 0.0
    estimated_annual_waste: float = 0.0
    has_waste_flag: bool = False

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSummaryResponse(BaseModel):
    total_monthly_spend: float
    total_annual_spend: float
    total_licenses: int
    total_active_licenses: int
    total_unused_licenses: int
    overall_utilization_rate: float
    potential_monthly_savings: float
    potential_annual_savings: float
    subscriptions: List[SubscriptionOut]
