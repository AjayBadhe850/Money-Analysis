import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    UNDER_REVIEW = "UNDER_REVIEW"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    
    vendor = Column(String(255), nullable=True)  # Name for quick display
    service_name = Column(String(255), nullable=False)
    monthly_cost = Column(Float, nullable=False, default=0.0)
    total_licenses = Column(Integer, nullable=False, default=1)
    active_licenses = Column(Integer, nullable=False, default=1)
    renewal_date = Column(Date, nullable=False, index=True)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_sub_company_status", "company_id", "status"),
        Index("idx_sub_company_renewal", "company_id", "renewal_date"),
    )

    # Relationships
    company = relationship("Company", back_populates="subscriptions")
    department = relationship("Department", back_populates="subscriptions")
    vendor_rel = relationship("Vendor", back_populates="subscriptions")
