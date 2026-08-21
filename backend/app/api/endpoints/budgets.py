from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetOut, BudgetSummaryResponse
)
from app.auth.rbac import get_current_user, require_roles
from app.services.budget_service import (
    get_budgets_summary, create_budget, update_budget, delete_budget
)
from app.services.audit_service import log_activity

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=BudgetSummaryResponse)
def list_budgets(
    year: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_budgets_summary(db=db, company_id=company_id, year=year, department_id=department_id)


@router.post("", response_model=BudgetOut)
def create_new_budget(
    data: BudgetCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    b = create_budget(db=db, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="CREATE_BUDGET",
        entity="Budget",
        entity_id=str(b.id),
        details=f"Created budget for year {b.year} allocated ${b.allocated_amount}"
    )

    # Return refreshed summary single budget
    summary = get_budgets_summary(db=db, company_id=company_id, year=b.year)
    for bo in summary.budgets:
        if bo.id == b.id:
            return bo
    
    # Fallback output
    return BudgetOut(
        id=b.id,
        company_id=b.company_id,
        department_id=b.department_id,
        category_id=b.category_id,
        month=b.month,
        year=b.year,
        allocated_amount=b.allocated_amount,
        spent_amount=b.spent_amount,
        notes=b.notes,
        created_at=b.created_at,
        updated_at=b.updated_at
    )


@router.put("/{budget_id}", response_model=BudgetOut)
def edit_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    b = update_budget(db=db, budget_id=budget_id, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="UPDATE_BUDGET",
        entity="Budget",
        entity_id=str(b.id),
        details=f"Updated budget {budget_id}"
    )

    summary = get_budgets_summary(db=db, company_id=company_id, year=b.year)
    for bo in summary.budgets:
        if bo.id == b.id:
            return bo

    return BudgetOut(
        id=b.id,
        company_id=b.company_id,
        department_id=b.department_id,
        category_id=b.category_id,
        month=b.month,
        year=b.year,
        allocated_amount=b.allocated_amount,
        spent_amount=b.spent_amount,
        notes=b.notes,
        created_at=b.created_at,
        updated_at=b.updated_at
    )


@router.delete("/{budget_id}")
def remove_budget(
    budget_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    delete_budget(db=db, budget_id=budget_id, company_id=company_id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="DELETE_BUDGET",
        entity="Budget",
        entity_id=str(budget_id),
        details=f"Deleted budget {budget_id}"
    )
    return {"message": "Budget deleted successfully"}
