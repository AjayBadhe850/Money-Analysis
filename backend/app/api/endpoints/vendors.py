from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorOut
from app.auth.rbac import get_current_user, require_roles
from app.services.vendor_service import (
    get_vendors_list, get_vendor_by_id, create_vendor, update_vendor, delete_vendor
)
from app.services.audit_service import log_activity

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[VendorOut])
def list_vendors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_vendors_list(db=db, company_id=company_id)


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    return get_vendor_by_id(db=db, vendor_id=vendor_id, company_id=company_id)


@router.post("", response_model=VendorOut)
def create_new_vendor(
    data: VendorCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    v = create_vendor(db=db, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="CREATE_VENDOR",
        entity="Vendor",
        entity_id=str(v.id),
        details=f"Created vendor '{v.name}'"
    )

    return get_vendor_by_id(db=db, vendor_id=v.id, company_id=company_id)


@router.put("/{vendor_id}", response_model=VendorOut)
def edit_vendor(
    vendor_id: int,
    data: VendorUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    v = update_vendor(db=db, vendor_id=vendor_id, company_id=company_id, data=data)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="UPDATE_VENDOR",
        entity="Vendor",
        entity_id=str(v.id),
        details=f"Updated vendor '{v.name}'"
    )

    return get_vendor_by_id(db=db, vendor_id=v.id, company_id=company_id)


@router.delete("/{vendor_id}")
def remove_vendor(
    vendor_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER])),
    db: Session = Depends(get_db)
):
    company_id = current_user.company_id or 1
    delete_vendor(db=db, vendor_id=vendor_id, company_id=company_id)
    
    log_activity(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        action="DELETE_VENDOR",
        entity="Vendor",
        entity_id=str(vendor_id),
        details=f"Deleted vendor {vendor_id}"
    )
    return {"message": "Vendor deleted successfully"}
