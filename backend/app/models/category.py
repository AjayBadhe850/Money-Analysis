from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    color_code = Column(String(50), default="#6366F1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
