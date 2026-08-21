from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    company_id: int
    manager_id: Optional[int] = None


class DepartmentCreate(BaseModel):
    name: str
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime
    manager_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
