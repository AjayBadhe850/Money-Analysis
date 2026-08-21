from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.auth.rbac import get_current_user, require_roles
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(tags=["Departments & Categories"])


@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    depts = db.query(Department).filter(Department.company_id == company_id).all()
    results = []
    for d in depts:
        results.append(DepartmentOut(
            id=d.id,
            company_id=d.company_id,
            name=d.name,
            manager_id=d.manager_id,
            created_at=d.created_at,
            manager_name=d.manager.name if d.manager else None
        ))
    return results


@router.post("/departments", response_model=DepartmentOut)
def create_new_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    d = Department(
        company_id=company_id,
        name=data.name,
        manager_id=data.manager_id
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return DepartmentOut(
        id=d.id,
        company_id=d.company_id,
        name=d.name,
        manager_id=d.manager_id,
        created_at=d.created_at,
        manager_name=d.manager.name if d.manager else None
    )


@router.get("/categories", response_model=List[CategoryOut])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    cats = db.query(Category).filter(Category.company_id == company_id).all()
    return cats


@router.post("/categories", response_model=CategoryOut)
def create_new_category(
    data: CategoryCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    c = Category(
        company_id=company_id,
        name=data.name,
        color_code=data.color_code
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
