import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class TransactionType(str, enum.Enum):
    EXPENSE = "EXPENSE"
    REVENUE = "REVENUE"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transaction_date = Column(Date, default=date.today, nullable=False, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), default=TransactionType.EXPENSE, nullable=False, index=True)
    payment_method = Column(String(100), default="Bank Transfer", nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Composite indexes for high-performance financial analytics
    __table_args__ = (
        Index("idx_tx_company_date", "company_id", "transaction_date"),
        Index("idx_tx_company_type", "company_id", "transaction_type"),
        Index("idx_tx_company_dept", "company_id", "department_id"),
        Index("idx_tx_company_cat", "company_id", "category_id"),
        Index("idx_tx_company_vendor", "company_id", "vendor_id"),
    )

    # Relationships
    company = relationship("Company", back_populates="transactions")
    department = relationship("Department", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    vendor = relationship("Vendor", back_populates="transactions")
    creator = relationship("User", back_populates="transactions_created")
