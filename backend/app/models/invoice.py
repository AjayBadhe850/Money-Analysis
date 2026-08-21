import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.session import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    
    invoice_number = Column(String(100), nullable=False, index=True)
    issue_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
