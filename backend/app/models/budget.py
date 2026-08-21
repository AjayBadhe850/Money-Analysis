from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    month = Column(Integer, nullable=True)  # 1-12 or NULL for annual
    year = Column(Integer, nullable=False, index=True)
    allocated_amount = Column(Float, nullable=False, default=0.0)
    spent_amount = Column(Float, nullable=False, default=0.0)
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_bg_company_year_dept", "company_id", "year", "department_id"),
        Index("idx_bg_company_year_cat", "company_id", "year", "category_id"),
    )

    # Relationships
    company = relationship("Company", back_populates="budgets")
    department = relationship("Department", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
