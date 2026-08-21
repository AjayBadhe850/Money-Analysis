from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String(100), nullable=False, index=True)  # LOGIN, CREATE_TRANSACTION, UPDATE_BUDGET, etc.
    entity = Column(String(100), nullable=False)               # Transaction, Budget, Vendor, etc.
    entity_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)                      # JSON string or description
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    company = relationship("Company", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
