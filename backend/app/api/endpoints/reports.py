from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.auth.rbac import get_current_user
from app.models.user import User
from app.agents.report_agent import ReportAgent
from app.core.tasks import TASK_EXECUTION_REGISTRY

router = APIRouter(prefix="/reports", tags=["Reports & Automation"])


@router.get("/monthly", summary="Get structured data for Monthly Finance Controller Report")
def get_monthly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = ReportAgent(db=db, company_id=current_user.company_id)
    return agent.generate_monthly_cfo_report()


@router.get("/monthly/pdf", summary="Export Monthly Finance Controller Report as PDF")
def download_monthly_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = ReportAgent(db=db, company_id=current_user.company_id)
    pdf_buffer = agent.export_pdf()
    filename = f"Money_Analysis_Financial_Report_{current_user.company_id}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/automation-status", summary="Get status and last-run timestamps of scheduled financial automation jobs")
def get_automation_status(
    current_user: User = Depends(get_current_user)
):
    return {
        "tasks": TASK_EXECUTION_REGISTRY,
        "scheduler": "Celery Beat & Redis",
        "active": True
    }
