import pytest
from app.auth.jwt import create_access_token
from app.models.user import User, UserRole
from app.auth.hashing import hash_password


@pytest.fixture
def auth_headers(db_session, test_company):
    user = User(
        name="Admin Test",
        email="admin.test@moneyanalysis.ai",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        company_id=test_company.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_ai_chat_endpoint(client, auth_headers):
    payload = {"message": "How can we reduce our SaaS and cloud spending next quarter?"}
    response = client.post("/api/ai/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "agents_involved" in data
    assert "tools_executed" in data


def test_ai_anomalies_scan_and_list(client, auth_headers):
    # Trigger scan
    scan_res = client.post("/api/ai/anomalies/scan", headers=auth_headers)
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert "anomalies_detected" in scan_data

    # List anomalies
    list_res = client.get("/api/ai/anomalies", headers=auth_headers)
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)


def test_ai_forecasts_generate(client, auth_headers):
    payload = {"horizon_days": 90}
    res = client.post("/api/ai/forecasts/generate", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["horizon_days"] == 90
    assert "total_projected_spend" in data
    assert len(data["series"]) > 0


def test_ai_what_if_simulation(client, auth_headers):
    payload = {
        "department_spend_adjustments": {"Engineering": -0.10, "Marketing": -0.05},
        "license_utilization_threshold_cut": 0.20,
        "revenue_growth_adjustment": 0.08
    }
    res = client.post("/api/ai/what-if", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "simulated_monthly_expense" in data
    assert "profit_margin_change_pct" in data
    assert len(data["detailed_impacts"]) > 0


def test_ai_recommendations_and_optimize(client, auth_headers):
    # Recommendations
    rec_res = client.get("/api/ai/recommendations", headers=auth_headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "opportunities" in rec_data

    # Optimization planner
    opt_payload = {"target_savings_amount": 35000.0, "timeframe_months": 3}
    opt_res = client.post("/api/ai/optimize", json=opt_payload, headers=auth_headers)
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["target_savings"] == 35000.0
    assert "recommended_actions" in opt_data


def test_ai_approval_workflow_endpoints(client, auth_headers):
    # Create request
    create_payload = {
        "request_type": "CANCEL_SUBSCRIPTION",
        "title": "Revoke 12 Idle Zoom Pro Seats",
        "details": "Automated deprovisioning of inactive licenses",
        "impact_savings_monthly": 1800.0,
        "risk_level": "LOW",
        "action_payload": {"service": "Zoom Pro", "seats": 12}
    }
    create_res = client.post("/api/ai/approvals", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 200
    req_id = create_res.json()["id"]

    # List pending
    list_res = client.get("/api/ai/approvals?status_filter=PENDING", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(r["id"] == req_id for r in list_res.json())

    # Approve
    approve_res = client.post(f"/api/ai/approvals/{req_id}/approve", json={"notes": "Approved by CFO"}, headers=auth_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] in ["APPROVED", "EXECUTED"]


def test_ai_categorize_endpoint(client, auth_headers):
    payload = {"description": "Google Ads Campaign Q3 Lead Gen", "vendor": "Google LLC"}
    res = client.post("/api/ai/categorize", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_category"] == "Marketing & Advertising"
    assert data["prediction_method"] == "RULE"


def test_ai_cost_efficiency_score(client, auth_headers):
    res = client.get("/api/ai/cost-efficiency-score", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100
    assert "components" in data
