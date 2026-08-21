import io
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.models.department import Department
from app.models.vendor import Vendor
from app.models.category import Category


def import_transactions_from_csv(
    db: Session,
    file_bytes: bytes,
    company_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    imported_records: List[Dict[str, Any]] = []
    duplicates_count = 0

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to parse CSV file: {str(e)}",
            "total_rows": 0,
            "imported_count": 0,
            "rejected_count": 0,
            "duplicates_count": 0,
            "errors": [{"row": 0, "column": "file", "error": "Invalid CSV structure"}],
            "imported_transactions": []
        }

    # Normalize column names (lowercase, strip whitespace)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Required columns check
    required_cols = {"date", "description", "amount", "type"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        return {
            "success": False,
            "message": f"CSV missing required columns: {', '.join(missing_cols)}. Required: date, description, amount, type, department (optional), vendor (optional)",
            "total_rows": len(df),
            "imported_count": 0,
            "rejected_count": len(df),
            "duplicates_count": 0,
            "errors": [{"row": 0, "column": col, "error": "Missing column header"} for col in missing_cols],
            "imported_transactions": []
        }

    total_rows = len(df)
    
    # Pre-fetch existing entities for efficient lookups
    dept_map = {d.name.lower(): d.id for d in db.query(Department).filter(Department.company_id == company_id).all()}
    vendor_map = {v.name.lower(): v.id for v in db.query(Vendor).filter(Vendor.company_id == company_id).all()}
    category_map = {c.name.lower(): c.id for c in db.query(Category).filter(Category.company_id == company_id).all()}

    # Existing transactions for duplicate check
    existing_transactions = db.query(Transaction).filter(Transaction.company_id == company_id).all()
    seen_fingerprints = {
        (t.transaction_date.isoformat(), round(t.amount, 2), t.description.strip().lower(), (t.reference_number or "").strip().lower())
        for t in existing_transactions
    }

    new_transactions_to_add = []

    for index, row in df.iterrows():
        row_num = index + 2  # 1-indexed plus header row
        row_has_error = False

        # 1. Parse Date
        date_val = None
        raw_date = row.get("date")
        if pd.isna(raw_date) or not str(raw_date).strip():
            errors.append({"row": row_num, "column": "date", "error": "Date is required"})
            row_has_error = True
        else:
            try:
                # Try standard parsing
                dt_obj = pd.to_datetime(raw_date, errors="raise")
                date_val = dt_obj.date()
            except Exception:
                errors.append({"row": row_num, "column": "date", "error": f"Invalid date format '{raw_date}'. Use YYYY-MM-DD"})
                row_has_error = True

        # 2. Parse Description
        raw_desc = row.get("description")
        desc_val = ""
        if pd.isna(raw_desc) or not str(raw_desc).strip():
            errors.append({"row": row_num, "column": "description", "error": "Description is required"})
            row_has_error = True
        else:
            desc_val = str(raw_desc).strip()

        # 3. Parse Amount
        amount_val = None
        raw_amount = row.get("amount")
        if pd.isna(raw_amount):
            errors.append({"row": row_num, "column": "amount", "error": "Amount is required"})
            row_has_error = True
        else:
            try:
                # Clean currency symbols or commas
                cleaned_amt = str(raw_amount).replace("$", "").replace(",", "").strip()
                amount_val = float(cleaned_amt)
                if amount_val <= 0:
                    errors.append({"row": row_num, "column": "amount", "error": "Amount must be greater than 0"})
                    row_has_error = True
            except Exception:
                errors.append({"row": row_num, "column": "amount", "error": f"Invalid amount '{raw_amount}'"})
                row_has_error = True

        # 4. Parse Type
        type_val = None
        raw_type = row.get("type")
        if pd.isna(raw_type) or not str(raw_type).strip():
            errors.append({"row": row_num, "column": "type", "error": "Transaction type is required (EXPENSE or REVENUE)"})
            row_has_error = True
        else:
            norm_type = str(raw_type).strip().upper()
            if norm_type in ["EXPENSE", "REVENUE"]:
                type_val = TransactionType(norm_type)
            else:
                errors.append({"row": row_num, "column": "type", "error": f"Invalid type '{raw_type}'. Must be EXPENSE or REVENUE"})
                row_has_error = True

        if row_has_error:
            continue

        # 5. Optional Reference Number & Payment Method
        ref_num = str(row.get("reference_number", "")).strip() if not pd.isna(row.get("reference_number")) else None
        payment_method = str(row.get("payment_method", "Bank Transfer")).strip() if not pd.isna(row.get("payment_method")) else "Bank Transfer"

        # 6. Duplicate check
        fingerprint = (date_val.isoformat(), round(amount_val, 2), desc_val.lower(), (ref_num or "").lower())
        if fingerprint in seen_fingerprints:
            duplicates_count += 1
            errors.append({"row": row_num, "column": "general", "error": f"Duplicate transaction ignored: {desc_val} (${amount_val}) on {date_val}"})
            continue

        seen_fingerprints.add(fingerprint)

        # 7. Department lookup / auto-create
        department_id = None
        raw_dept = row.get("department")
        if not pd.isna(raw_dept) and str(raw_dept).strip():
            dept_name = str(raw_dept).strip()
            dept_key = dept_name.lower()
            if dept_key in dept_map:
                department_id = dept_map[dept_key]
            else:
                # Create department
                new_dept = Department(company_id=company_id, name=dept_name)
                db.add(new_dept)
                db.flush()
                dept_map[dept_key] = new_dept.id
                department_id = new_dept.id

        # 8. Vendor lookup / auto-create
        vendor_id = None
        raw_vendor = row.get("vendor")
        if not pd.isna(raw_vendor) and str(raw_vendor).strip():
            vendor_name = str(raw_vendor).strip()
            vendor_key = vendor_name.lower()
            if vendor_key in vendor_map:
                vendor_id = vendor_map[vendor_key]
            else:
                new_vendor = Vendor(company_id=company_id, name=vendor_name)
                db.add(new_vendor)
                db.flush()
                vendor_map[vendor_key] = new_vendor.id
                vendor_id = new_vendor.id

        # 9. Category lookup / auto-create
        category_id = None
        raw_cat = row.get("category")
        if not pd.isna(raw_cat) and str(raw_cat).strip():
            cat_name = str(raw_cat).strip()
            cat_key = cat_name.lower()
            if cat_key in category_map:
                category_id = category_map[cat_key]
            else:
                new_cat = Category(company_id=company_id, name=cat_name, color_code="#6366F1")
                db.add(new_cat)
                db.flush()
                category_map[cat_key] = new_cat.id
                category_id = new_cat.id

        # Create Transaction
        trans = Transaction(
            company_id=company_id,
            department_id=department_id,
            category_id=category_id,
            vendor_id=vendor_id,
            transaction_date=date_val,
            description=desc_val,
            amount=amount_val,
            transaction_type=type_val,
            payment_method=payment_method,
            reference_number=ref_num,
            created_by=user_id
        )
        new_transactions_to_add.append(trans)
        imported_records.append({
            "date": date_val.isoformat(),
            "description": desc_val,
            "amount": amount_val,
            "type": type_val.value,
            "department": raw_dept if not pd.isna(raw_dept) else None,
            "vendor": raw_vendor if not pd.isna(raw_vendor) else None
        })

    # Save to database
    if new_transactions_to_add:
        db.add_all(new_transactions_to_add)
        db.commit()

    return {
        "success": len(new_transactions_to_add) > 0,
        "message": f"Successfully imported {len(new_transactions_to_add)} transactions. {len(errors)} issues encountered.",
        "total_rows": total_rows,
        "imported_count": len(new_transactions_to_add),
        "rejected_count": total_rows - len(new_transactions_to_add),
        "duplicates_count": duplicates_count,
        "errors": errors,
        "imported_transactions": imported_records[:10]  # Preview first 10
    }
