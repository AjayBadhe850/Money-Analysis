import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BudgetStatus(str, enum.Enum):
    SAFE = "SAFE"            # < 70%
    WARNING = "WARNING"      # 70% - 85%
    CRITICAL = "CRITICAL"    # 85% - 100%
    EXCEEDED = "EXCEEDED"    # > 100%


class BudgetBase(BaseModel):
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    month: Optional[int] = Field(default=None, ge=1, le=12)
    year: int
    allocated_amount: float = Field(gt=0)
    notes: Optional[str] = None


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    month: Optional[int] = Field(default=None, ge=1, le=12)
    year: Optional[int] = None
    allocated_amount: Optional[float] = Field(default=None, gt=0)
    notes: Optional[str] = None


class BudgetOut(BudgetBase):
    id: int
    company_id: int
    spent_amount: float
    created_at: datetime
    updated_at: datetime

    # Calculated metrics
    department_name: Optional[str] = None
    category_name: Optional[str] = None
    usage_percentage: float = 0.0
    remaining_amount: float = 0.0
    overspent_amount: float = 0.0
    status: BudgetStatus = BudgetStatus.SAFE

    model_config = ConfigDict(from_attributes=True)


class BudgetSummaryResponse(BaseModel):
    total_allocated: float
    total_spent: float
    total_remaining: float
    overall_usage_percentage: float
    safe_count: int
    warning_count: int
    critical_count: int
    exceeded_count: int
    budgets: List[BudgetOut]
