from app.services.finance_service import calculate_budget_usage
from app.schemas.budget import BudgetStatus


def test_budget_threshold_calculations():
    # SAFE (< 70%)
    safe_res = calculate_budget_usage(allocated_amount=10000.0, spent_amount=5000.0)
    assert safe_res["usage_percentage"] == 50.0
    assert safe_res["remaining_amount"] == 5000.0
    assert safe_res["overspent_amount"] == 0.0
    assert safe_res["status"] == BudgetStatus.SAFE

    # WARNING (70% - 85%)
    warn_res = calculate_budget_usage(allocated_amount=10000.0, spent_amount=7500.0)
    assert warn_res["usage_percentage"] == 75.0
    assert warn_res["status"] == BudgetStatus.WARNING

    # CRITICAL (85% - 100%)
    crit_res = calculate_budget_usage(allocated_amount=10000.0, spent_amount=9500.0)
    assert crit_res["usage_percentage"] == 95.0
    assert crit_res["status"] == BudgetStatus.CRITICAL

    # EXCEEDED (> 100%)
    exceed_res = calculate_budget_usage(allocated_amount=10000.0, spent_amount=12000.0)
    assert exceed_res["usage_percentage"] == 120.0
    assert exceed_res["remaining_amount"] == 0.0
    assert exceed_res["overspent_amount"] == 2000.0
    assert exceed_res["status"] == BudgetStatus.EXCEEDED


def test_budget_api_endpoints(client):
    reg = client.post("/api/auth/register", json={
        "name": "Finance Head",
        "email": "fin.head@test.com",
        "password": "Password123!",
        "role": "Finance Manager",
        "company_name": "Budget Corp"
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Budget
    b_payload = {
        "year": 2026,
        "month": 8,
        "allocated_amount": 50000.0,
        "notes": "Q3 Marketing budget"
    }
    resp = client.post("/api/budgets", json=b_payload, headers=headers)
    assert resp.status_code == 200
    b_data = resp.json()
    assert b_data["allocated_amount"] == 50000.0
    assert b_data["year"] == 2026
