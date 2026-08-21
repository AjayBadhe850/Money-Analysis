from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceOut, InvoiceSummaryResponse
)
from app.auth.rbac import get_current_user, require_roles
from app.services.invoice_service import (
    get_invoices_summary, create_invoice, update_invoice, delete_invoice
)
from app.services.audit_service import log_activity

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=InvoiceSummaryResponse)
def list_invoices(
    vendor_id: Optional[int] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_invoices_summary(db=db, company_id=company_id, vendor_id=vendor_id, status=status)


@router.post("", response_model=InvoiceOut)
def create_new_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    inv = create_invoice(db=db, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="CREATE_INVOICE",
        entity="Invoice",
        entity_id=str(inv.id),
        details=f"Created invoice #{inv.invoice_number} for ${inv.amount}"
    )

    summary = get_invoices_summary(db=db, company_id=company_id)
    for io in summary.invoices:
        if io.id == inv.id:
            return io

    return InvoiceOut(
        id=inv.id,
        company_id=inv.company_id,
        vendor_id=inv.vendor_id,
        invoice_number=inv.invoice_number,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        amount=inv.amount,
        status=inv.status,
        created_at=inv.created_at,
        updated_at=inv.updated_at
    )


@router.put("/{invoice_id}", response_model=InvoiceOut)
def edit_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    inv = update_invoice(db=db, invoice_id=invoice_id, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="UPDATE_INVOICE",
        entity="Invoice",
        entity_id=str(inv.id),
        details=f"Updated invoice #{inv.invoice_number} status to {inv.status.value}"
    )

    summary = get_invoices_summary(db=db, company_id=company_id)
    for io in summary.invoices:
        if io.id == inv.id:
            return io

    return InvoiceOut(
        id=inv.id,
        company_id=inv.company_id,
        vendor_id=inv.vendor_id,
        invoice_number=inv.invoice_number,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        amount=inv.amount,
        status=inv.status,
        created_at=inv.created_at,
        updated_at=inv.updated_at
    )


@router.delete("/{invoice_id}")
def remove_invoice(
    invoice_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    delete_invoice(db=db, invoice_id=invoice_id, company_id=company_id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="DELETE_INVOICE",
        entity="Invoice",
        entity_id=str(invoice_id),
        details=f"Deleted invoice {invoice_id}"
    )
    return {"message": "Invoice deleted successfully"}
