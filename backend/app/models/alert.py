import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class CostAlert(Base):
    __tablename__ = "cost_alerts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    company = relationship("Company", back_populates="alerts")


class CostRecommendation(Base):
    __tablename__ = "cost_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    potential_monthly_savings = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="NEW", nullable=False)  # NEW, APPLIED, DISMISSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
