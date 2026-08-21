from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str
    color_code: str = "#6366F1"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color_code: Optional[str] = None


class CategoryOut(CategoryBase):
    id: int
    company_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
