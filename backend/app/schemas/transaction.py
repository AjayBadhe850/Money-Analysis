from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    transaction_date: date
    description: str
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    transaction_type: TransactionType = TransactionType.EXPENSE
    payment_method: str = "Bank Transfer"
    reference_number: Optional[str] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    vendor_id: Optional[int] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    transaction_date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    transaction_type: Optional[TransactionType] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    vendor_id: Optional[int] = None


class TransactionOut(TransactionBase):
    id: int
    company_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Display names
    department_name: Optional[str] = None
    category_name: Optional[str] = None
    vendor_name: Optional[str] = None
    creator_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: List[TransactionOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_revenue: float
    total_expense: float
