from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    fiscal_year_start = Column(String(10), default="January", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="company", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="company", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="company", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="company", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="company", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="company", cascade="all, delete-orphan")
    alerts = relationship("CostAlert", back_populates="company", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="company", cascade="all, delete-orphan")
