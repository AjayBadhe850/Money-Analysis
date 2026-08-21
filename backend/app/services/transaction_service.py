import math
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models.transaction import Transaction, TransactionType
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut, TransactionListResponse
)
from app.core.exceptions import ResourceNotFoundException


def get_transactions_list(
    db: Session,
    company_id: int,
    page: int = 1,
    page_size: int = 25,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "transaction_date",
    sort_order: str = "desc"
) -> TransactionListResponse:
    query = db.query(Transaction).filter(Transaction.company_id == company_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(s),
                Transaction.reference_number.ilike(s),
                Transaction.payment_method.ilike(s)
            )
        )
    
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if department_id:
        query = query.filter(Transaction.department_id == department_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if vendor_id:
        query = query.filter(Transaction.vendor_id == vendor_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    # Calculate filtered aggregates
    all_filtered = query.all()
    total_count = len(all_filtered)
    total_rev = sum(t.amount for t in all_filtered if t.transaction_type == TransactionType.REVENUE)
    total_exp = sum(t.amount for t in all_filtered if t.transaction_type == TransactionType.EXPENSE)

    # Sorting
    sort_col = getattr(Transaction, sort_by, Transaction.transaction_date)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    # Pagination
    offset = (max(1, page) - 1) * page_size
    items_raw = query.offset(offset).limit(page_size).all()

    items = []
    for t in items_raw:
        out = TransactionOut(
            id=t.id,
            company_id=t.company_id,
            department_id=t.department_id,
            category_id=t.category_id,
            vendor_id=t.vendor_id,
            transaction_date=t.transaction_date,
            description=t.description,
            amount=t.amount,
            transaction_type=t.transaction_type,
            payment_method=t.payment_method,
            reference_number=t.reference_number,
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
            department_name=t.department.name if t.department else None,
            category_name=t.category.name if t.category else None,
            vendor_name=t.vendor.name if t.vendor else None,
            creator_name=t.creator.name if t.creator else None
        )
        items.append(out)

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    return TransactionListResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_revenue=round(total_rev, 2),
        total_expense=round(total_exp, 2)
    )


def create_transaction(
    db: Session,
    company_id: int,
    data: TransactionCreate,
    user_id: Optional[int] = None
) -> Transaction:
    trans = Transaction(
        company_id=company_id,
        department_id=data.department_id,
        category_id=data.category_id,
        vendor_id=data.vendor_id,
        transaction_date=data.transaction_date,
        description=data.description,
        amount=data.amount,
        transaction_type=data.transaction_type,
        payment_method=data.payment_method,
        reference_number=data.reference_number,
        created_by=user_id
    )
    db.add(trans)
    db.commit()
    db.refresh(trans)
    return trans


def update_transaction(
    db: Session,
    transaction_id: int,
    company_id: int,
    data: TransactionUpdate
) -> Transaction:
    trans = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.company_id == company_id
    ).first()
    if not trans:
        raise ResourceNotFoundException("Transaction", str(transaction_id))

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(trans, field, val)

    db.commit()
    db.refresh(trans)
    return trans


def delete_transaction(db: Session, transaction_id: int, company_id: int) -> bool:
    trans = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.company_id == company_id
    ).first()
    if not trans:
        raise ResourceNotFoundException("Transaction", str(transaction_id))

    db.delete(trans)
    db.commit()
    return True
