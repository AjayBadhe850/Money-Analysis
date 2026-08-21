from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.transaction import TransactionType
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut, TransactionListResponse
)
from app.auth.rbac import get_current_user, require_roles
from app.services.transaction_service import (
    get_transactions_list, create_transaction, update_transaction, delete_transaction
)
from app.services.csv_import_service import import_transactions_from_csv
from app.services.audit_service import log_activity
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = Query("transaction_date"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_transactions_list(
        db=db,
        company_id=company_id,
        page=page,
        page_size=page_size,
        search=search,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        category_id=category_id,
        vendor_id=vendor_id,
        transaction_type=transaction_type,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("", response_model=TransactionOut)
def create_new_transaction(
    data: TransactionCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.DEPARTMENT_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    t = create_transaction(db=db, company_id=company_id, data=data, user_id=current_user.id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="CREATE_TRANSACTION",
        entity="Transaction",
        entity_id=str(t.id),
        details=f"Created {t.transaction_type.value} transaction '${t.amount}' - '{t.description}'"
    )

    return TransactionOut(
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
        creator_name=current_user.name
    )


@router.put("/{transaction_id}", response_model=TransactionOut)
def edit_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.DEPARTMENT_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    t = update_transaction(db=db, transaction_id=transaction_id, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="UPDATE_TRANSACTION",
        entity="Transaction",
        entity_id=str(t.id),
        details=f"Updated transaction {transaction_id}"
    )

    return TransactionOut(
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


@router.delete("/{transaction_id}")
def remove_transaction(
    transaction_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    delete_transaction(db=db, transaction_id=transaction_id, company_id=company_id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="DELETE_TRANSACTION",
        entity="Transaction",
        entity_id=str(transaction_id),
        details=f"Deleted transaction {transaction_id}"
    )
    return {"message": "Transaction deleted successfully"}


@router.post("/import-csv")
async def import_csv_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER, UserRole.DEPARTMENT_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    content = await file.read()
    
    result = import_transactions_from_csv(
        db=db,
        file_bytes=content,
        company_id=company_id,
        user_id=current_user.id
    )

    if result.get("imported_count", 0) > 0:
        log_activity(
            db=db,
            company_id=company_id,
            user_id=current_user.id,
            action="CSV_IMPORT",
            entity="Transaction",
            details=f"Imported {result['imported_count']} transactions from {file.filename}"
        )

    return result


@router.get("/export-csv-template")
def download_csv_template():
    sample_csv = "date,description,amount,type,department,vendor,category,reference_number\n2026-08-01,AWS Cloud Infrastructure,35000,EXPENSE,Engineering,AWS,Cloud,INV-AWS-8831\n2026-08-02,Google Ads Campaign,60000,EXPENSE,Marketing,Google,Marketing,INV-GOOG-2026\n2026-08-05,Enterprise License Sale,250000,REVENUE,Sales,Customer ABC,Software,REC-2026-001\n"
    return Response(
        content=sample_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_template.csv"}
    )
