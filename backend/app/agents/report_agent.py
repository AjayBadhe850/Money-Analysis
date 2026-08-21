import io
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.report_service import ReportService

logger = logging.getLogger("costwise.agent.report")


class ReportAgent:
    """Agent responsible for compiling enterprise financial controller reports and exporting verified PDFs."""
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self.report_service = ReportService(db=db, company_id=company_id)

    def generate_monthly_cfo_report(self) -> Dict[str, Any]:
        """Synthesizes structured narrative and numeric breakdown for the Monthly CFO Report."""
        logger.info(f"ReportAgent: Compiling monthly report for company {self.company_id}...")
        return self.report_service.generate_monthly_report_data()

    def export_pdf(self) -> io.BytesIO:
        """Exports the verified Monthly Finance Controller Report as a high-fidelity PDF byte stream."""
        logger.info(f"ReportAgent: Rendering PDF report for company {self.company_id}...")
        return self.report_service.generate_pdf_report()
