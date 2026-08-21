from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    reliability_score = Column(Float, default=95.0, nullable=False)  # 0 - 100
    quality_score = Column(Float, default=90.0, nullable=False)      # 0 - 100
    average_delivery_days = Column(Float, default=3.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="vendors")
    transactions = relationship("Transaction", back_populates="vendor")
    subscriptions = relationship("Subscription", back_populates="vendor_rel")
    invoices = relationship("Invoice", back_populates="vendor")
