from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.invoice import InvoiceStatus


class InvoiceBase(BaseModel):
    vendor_id: Optional[int] = None
    invoice_number: str
    issue_date: date = Field(default_factory=date.today)
    due_date: date
    amount: float = Field(gt=0)
    status: InvoiceStatus = InvoiceStatus.PENDING


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    vendor_id: Optional[int] = None
    invoice_number: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    amount: Optional[float] = Field(default=None, gt=0)
    status: Optional[InvoiceStatus] = None


class InvoiceOut(InvoiceBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    vendor_name: Optional[str] = None
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)


class InvoiceSummaryResponse(BaseModel):
    total_invoiced: float
    total_paid: float
    total_pending: float
    total_overdue: float
    invoices: List[InvoiceOut]
