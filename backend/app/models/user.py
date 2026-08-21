import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    FINANCE_MANAGER = "Finance Manager"
    DEPARTMENT_MANAGER = "Department Manager"
    EMPLOYEE = "Employee"
    AUDITOR = "Auditor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="users")
    transactions_created = relationship("Transaction", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")
