from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class VendorBase(BaseModel):
    name: str
    contact_email: Optional[EmailStr] = None
    category: Optional[str] = None
    reliability_score: float = Field(default=95.0, ge=0.0, le=100.0)
    quality_score: float = Field(default=90.0, ge=0.0, le=100.0)
    average_delivery_days: float = Field(default=3.0, ge=0.0)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    category: Optional[str] = None
    reliability_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    average_delivery_days: Optional[float] = Field(default=None, ge=0.0)


class VendorOut(VendorBase):
    id: int
    company_id: int
    created_at: datetime
    total_spend: Optional[float] = 0.0
    transaction_count: Optional[int] = 0
    average_transaction_value: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)
