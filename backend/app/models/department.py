from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="departments")
    manager = relationship("User", foreign_keys=[manager_id])
    transactions = relationship("Transaction", back_populates="department")
    budgets = relationship("Budget", back_populates="department")
    subscriptions = relationship("Subscription", back_populates="department")
