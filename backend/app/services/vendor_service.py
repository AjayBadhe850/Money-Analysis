from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.vendor import Vendor
from app.models.transaction import Transaction, TransactionType
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorOut
from app.services.finance_service import calculate_vendor_spending
from app.core.exceptions import ResourceNotFoundException


def get_vendors_list(db: Session, company_id: int) -> List[VendorOut]:
    vendors = db.query(Vendor).filter(Vendor.company_id == company_id).all()
    results = []
    for v in vendors:
        spending_metrics = calculate_vendor_spending(db, v.id)
        out = VendorOut(
            id=v.id,
            company_id=v.company_id,
            name=v.name,
            contact_email=v.contact_email,
            category=v.category,
            reliability_score=v.reliability_score,
            quality_score=v.quality_score,
            average_delivery_days=v.average_delivery_days,
            created_at=v.created_at,
            total_spend=spending_metrics["total_spend"],
            transaction_count=spending_metrics["transaction_count"],
            average_transaction_value=spending_metrics["average_transaction_value"]
        )
        results.append(out)
    return results


def get_vendor_by_id(db: Session, vendor_id: int, company_id: int) -> VendorOut:
    v = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.company_id == company_id).first()
    if not v:
        raise ResourceNotFoundException("Vendor", str(vendor_id))
    
    spending_metrics = calculate_vendor_spending(db, v.id)
    return VendorOut(
        id=v.id,
        company_id=v.company_id,
        name=v.name,
        contact_email=v.contact_email,
        category=v.category,
        reliability_score=v.reliability_score,
        quality_score=v.quality_score,
        average_delivery_days=v.average_delivery_days,
        created_at=v.created_at,
        total_spend=spending_metrics["total_spend"],
        transaction_count=spending_metrics["transaction_count"],
        average_transaction_value=spending_metrics["average_transaction_value"]
    )


def create_vendor(db: Session, company_id: int, data: VendorCreate) -> Vendor:
    vendor = Vendor(
        company_id=company_id,
        name=data.name,
        contact_email=data.contact_email,
        category=data.category,
        reliability_score=data.reliability_score,
        quality_score=data.quality_score,
        average_delivery_days=data.average_delivery_days
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def update_vendor(db: Session, vendor_id: int, company_id: int, data: VendorUpdate) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.company_id == company_id).first()
    if not vendor:
        raise ResourceNotFoundException("Vendor", str(vendor_id))

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(vendor, field, val)

    db.commit()
    db.refresh(vendor)
    return vendor


def delete_vendor(db: Session, vendor_id: int, company_id: int) -> bool:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.company_id == company_id).first()
    if not vendor:
        raise ResourceNotFoundException("Vendor", str(vendor_id))

    db.delete(vendor)
    db.commit()
    return True
