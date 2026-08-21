from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, InvoiceStatus
from app.models.vendor import Vendor
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceOut, InvoiceSummaryResponse
)
from app.core.exceptions import ResourceNotFoundException


def get_invoices_summary(
    db: Session,
    company_id: int,
    vendor_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None
) -> InvoiceSummaryResponse:
    query = db.query(Invoice).filter(Invoice.company_id == company_id)
    if vendor_id:
        query = query.filter(Invoice.vendor_id == vendor_id)
    if status:
        query = query.filter(Invoice.status == status)

    raw_invoices = query.order_by(Invoice.due_date.asc()).all()

    total_invoiced = 0.0
    total_paid = 0.0
    total_pending = 0.0
    total_overdue = 0.0

    today = date.today()
    invoice_outs: List[InvoiceOut] = []

    for inv in raw_invoices:
        total_invoiced += inv.amount
        is_overdue = (inv.due_date < today and inv.status == InvoiceStatus.PENDING) or (inv.status == InvoiceStatus.OVERDUE)
        
        if inv.status == InvoiceStatus.PAID:
            total_paid += inv.amount
        elif is_overdue:
            total_overdue += inv.amount
        elif inv.status == InvoiceStatus.PENDING:
            total_pending += inv.amount

        out = InvoiceOut(
            id=inv.id,
            company_id=inv.company_id,
            vendor_id=inv.vendor_id,
            invoice_number=inv.invoice_number,
            issue_date=inv.issue_date,
            due_date=inv.due_date,
            amount=round(inv.amount, 2),
            status=inv.status,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            vendor_name=inv.vendor.name if inv.vendor else "Unknown Vendor",
            is_overdue=is_overdue
        )
        invoice_outs.append(out)

    return InvoiceSummaryResponse(
        total_invoiced=round(total_invoiced, 2),
        total_paid=round(total_paid, 2),
        total_pending=round(total_pending, 2),
        total_overdue=round(total_overdue, 2),
        invoices=invoice_outs
    )


def create_invoice(db: Session, company_id: int, data: InvoiceCreate) -> Invoice:
    inv = Invoice(
        company_id=company_id,
        vendor_id=data.vendor_id,
        invoice_number=data.invoice_number,
        issue_date=data.issue_date,
        due_date=data.due_date,
        amount=data.amount,
        status=data.status
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def update_invoice(db: Session, invoice_id: int, company_id: int, data: InvoiceUpdate) -> Invoice:
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.company_id == company_id
    ).first()
    if not inv:
        raise ResourceNotFoundException("Invoice", str(invoice_id))

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(inv, field, val)

    db.commit()
    db.refresh(inv)
    return inv


def delete_invoice(db: Session, invoice_id: int, company_id: int) -> bool:
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.company_id == company_id
    ).first()
    if not inv:
        raise ResourceNotFoundException("Invoice", str(invoice_id))

    db.delete(inv)
    db.commit()
    return True
