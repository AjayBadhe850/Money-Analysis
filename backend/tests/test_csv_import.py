import io
from app.services.csv_import_service import import_transactions_from_csv
from app.models.company import Company
from app.models.transaction import Transaction


def test_csv_import_valid_and_invalid(db_session):
    # Setup test company
    company = Company(name="CSV Testing Inc", industry="Tech", currency="USD")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    # Valid CSV content
    valid_csv = (
        "date,description,amount,type,department,vendor\n"
        "2026-08-01,AWS Cloud Hosting,3500.00,EXPENSE,Engineering,AWS\n"
        "2026-08-02,Google Search Ads,1200.00,EXPENSE,Marketing,Google\n"
        "2026-08-05,Client Enterprise Payout,25000.00,REVENUE,Sales,Client X\n"
    ).encode("utf-8")

    res = import_transactions_from_csv(db_session, valid_csv, company_id=company.id)
    assert res["success"] is True
    assert res["imported_count"] == 3
    assert res["rejected_count"] == 0

    # Test Duplicate prevention on re-import
    res_dup = import_transactions_from_csv(db_session, valid_csv, company_id=company.id)
    assert res_dup["duplicates_count"] == 3
    assert res_dup["imported_count"] == 0

    # Test Invalid Rows (Negative amount, bad date, bad type)
    invalid_csv = (
        "date,description,amount,type,department,vendor\n"
        "not-a-date,Invalid Date Row,100.00,EXPENSE,IT,VendorA\n"
        "2026-08-10,Negative Amount,-50.00,EXPENSE,IT,VendorB\n"
        "2026-08-11,Bad Type,500.00,INVALID_TYPE,IT,VendorC\n"
        "2026-08-12,Good Row,850.00,EXPENSE,Engineering,VendorD\n"
    ).encode("utf-8")

    res_inv = import_transactions_from_csv(db_session, invalid_csv, company_id=company.id)
    assert res_inv["imported_count"] == 1
    assert res_inv["rejected_count"] == 3
    assert len(res_inv["errors"]) == 3
