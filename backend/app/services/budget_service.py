from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetOut, BudgetSummaryResponse, BudgetStatus
)
from app.services.finance_service import calculate_budget_usage
from app.core.exceptions import ResourceNotFoundException


def sync_budget_spent(db: Session, budget: Budget) -> float:
    """Calculate actual spent amount from transactions matching the budget's criteria."""
    query = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(
        Transaction.company_id == budget.company_id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        extract("year", Transaction.transaction_date) == budget.year
    )
    if budget.month:
        query = query.filter(extract("month", Transaction.transaction_date) == budget.month)
    if budget.department_id:
        query = query.filter(Transaction.department_id == budget.department_id)
    if budget.category_id:
        query = query.filter(Transaction.category_id == budget.category_id)

    actual_spent = float(query.scalar() or 0.0)
    budget.spent_amount = actual_spent
    db.commit()
    return actual_spent


def get_budgets_summary(
    db: Session,
    company_id: int,
    year: Optional[int] = None,
    department_id: Optional[int] = None
) -> BudgetSummaryResponse:
    query = db.query(Budget).filter(Budget.company_id == company_id)
    if year:
        query = query.filter(Budget.year == year)
    if department_id:
        query = query.filter(Budget.department_id == department_id)

    raw_budgets = query.all()

    total_alloc = 0.0
    total_spent = 0.0
    safe_cnt = 0
    warn_cnt = 0
    crit_cnt = 0
    exceed_cnt = 0

    budget_outs: List[BudgetOut] = []

    for b in raw_budgets:
        # Sync spent amount
        spent = sync_budget_spent(db, b)
        total_alloc += b.allocated_amount
        total_spent += spent

        metrics = calculate_budget_usage(b.allocated_amount, spent)
        st = metrics["status"]
        if st == BudgetStatus.SAFE:
            safe_cnt += 1
        elif st == BudgetStatus.WARNING:
            warn_cnt += 1
        elif st == BudgetStatus.CRITICAL:
            crit_cnt += 1
        else:
            exceed_cnt += 1

        out = BudgetOut(
            id=b.id,
            company_id=b.company_id,
            department_id=b.department_id,
            category_id=b.category_id,
            month=b.month,
            year=b.year,
            allocated_amount=round(b.allocated_amount, 2),
            spent_amount=round(spent, 2),
            notes=b.notes,
            created_at=b.created_at,
            updated_at=b.updated_at,
            department_name=b.department.name if b.department else "All Departments",
            category_name=b.category.name if b.category else "All Categories",
            usage_percentage=metrics["usage_percentage"],
            remaining_amount=metrics["remaining_amount"],
            overspent_amount=metrics["overspent_amount"],
            status=st
        )
        budget_outs.append(out)

    overall_metrics = calculate_budget_usage(total_alloc, total_spent)

    return BudgetSummaryResponse(
        total_allocated=round(total_alloc, 2),
        total_spent=round(total_spent, 2),
        total_remaining=overall_metrics["remaining_amount"],
        overall_usage_percentage=overall_metrics["usage_percentage"],
        safe_count=safe_cnt,
        warning_count=warn_cnt,
        critical_count=crit_cnt,
        exceeded_count=exceed_cnt,
        budgets=budget_outs
    )


def create_budget(db: Session, company_id: int, data: BudgetCreate) -> Budget:
    budget = Budget(
        company_id=company_id,
        department_id=data.department_id,
        category_id=data.category_id,
        month=data.month,
        year=data.year,
        allocated_amount=data.allocated_amount,
        spent_amount=0.0,
        notes=data.notes
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    sync_budget_spent(db, budget)
    return budget


def update_budget(db: Session, budget_id: int, company_id: int, data: BudgetUpdate) -> Budget:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.company_id == company_id
    ).first()
    if not budget:
        raise ResourceNotFoundException("Budget", str(budget_id))

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(budget, field, val)

    db.commit()
    db.refresh(budget)
    sync_budget_spent(db, budget)
    return budget


def delete_budget(db: Session, budget_id: int, company_id: int) -> bool:
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.company_id == company_id
    ).first()
    if not budget:
        raise ResourceNotFoundException("Budget", str(budget_id))

    db.delete(budget)
    db.commit()
    return True
