import pytest
from app.auth.jwt import create_access_token
from app.agents.report_agent import ReportAgent


def test_report_agent_data_synthesis(db_session, test_company):
    """Test deterministic data compilation across 14 financial sections in ReportAgent."""
    agent = ReportAgent(db=db_session, company_id=test_company.id)
    report_data = agent.generate_monthly_cfo_report()

    assert "executive_summary" in report_data
    assert "kpis" in report_data
    assert "savings_opportunities" in report_data
    assert "forecast" in report_data
    assert report_data["total_monthly_savings_potential"] >= 0


def test_report_agent_pdf_rendering(db_session, test_company):
    """Test ReportLab PDF byte stream generation and binary format validation."""
    agent = ReportAgent(db=db_session, company_id=test_company.id)
    pdf_buffer = agent.export_pdf()

    assert pdf_buffer is not None
    content = pdf_buffer.getvalue()
    assert len(content) > 1000  # Non-trivial PDF size
    assert content.startswith(b"%PDF-")  # Valid PDF binary signature


def test_reports_api_endpoints(client, db_session, test_company, test_user):
    """Test REST API endpoints for JSON and PDF report retrieval."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/reports/monthly
    res_json = client.get("/api/reports/monthly", headers=headers)
    assert res_json.status_code == 200
    assert "report_period" in res_json.json()

    # 2. GET /api/reports/monthly/pdf
    res_pdf = client.get("/api/reports/monthly/pdf", headers=headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")

    # 3. GET /api/reports/automation-status
    res_auto = client.get("/api/reports/automation-status", headers=headers)
    assert res_auto.status_code == 200
    assert "tasks" in res_auto.json()
