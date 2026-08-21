from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    currency: str = "USD"
    fiscal_year_start: str = "January"


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
