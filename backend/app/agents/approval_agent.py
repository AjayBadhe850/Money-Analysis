import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.future_ai import ApprovalRequest
from app.models.subscription import Subscription
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class ApprovalAgent:
    """
    Human-in-the-Loop governance agent managing authorization lifecycles,
    financial audit boundaries, and non-destructive action orchestration.
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id

    def create_request(
        self,
        request_type: str,
        title: str,
        details: str,
        impact_savings_monthly: float = 0.0,
        risk_level: str = "LOW",
        action_payload: Optional[Dict[str, Any]] = None,
        requester_id: Optional[int] = None,
    ) -> ApprovalRequest:
        """
        Register a new pending financial optimization approval request.
        """
        req = ApprovalRequest(
            company_id=self.company_id,
            requester_id=requester_id,
            request_type=request_type,
            title=title,
            details=details,
            impact_savings_monthly=impact_savings_monthly,
            risk_level=risk_level,
            action_payload=action_payload,
            status="PENDING",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def process_action(
        self,
        request_id: int,
        action: str,  # "APPROVE", "REJECT"
        approver_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve or reject a pending request and orchestrate controlled execution.
        """
        req = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.company_id == self.company_id,
            ApprovalRequest.id == request_id
        ).first()

        if not req:
            raise ValueError(f"Approval request #{request_id} not found.")

        if req.status != "PENDING":
            raise ValueError(f"Request #{request_id} is already in state '{req.status}'.")

        now = datetime.now(timezone.utc)
        req.approver_id = approver_id
        req.resolved_at = now
        req.response_notes = notes

        if action.upper() == "APPROVE":
            req.status = "APPROVED"
            # Attempt automated execution if payload specifies
            execution_success = self._execute_action(req)
            if execution_success:
                req.status = "EXECUTED"
        else:
            req.status = "REJECTED"

        # Log audit trail
        audit = AuditLog(
            company_id=self.company_id,
            user_id=approver_id,
            action=f"APPROVAL_{req.status}",
            entity="ApprovalRequest",
            entity_id=req.id,
            details=f"Approval request '{req.title}' was {req.status}. Notes: {notes or 'None'}",
            timestamp=now
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(req)

        return {
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "resolved_at": req.resolved_at.isoformat(),
            "notes": req.response_notes,
        }

    def _execute_action(self, req: ApprovalRequest) -> bool:
        """
        Execute the approved financial action non-destructively.
        """
        try:
            payload = req.action_payload or {}
            if req.request_type == "CANCEL_SUBSCRIPTION" and "subscription_id" in payload:
                sub_id = payload["subscription_id"]
                sub = self.db.query(Subscription).filter(
                    Subscription.company_id == self.company_id,
                    Subscription.id == sub_id
                ).first()
                if sub:
                    sub.status = "UNDER_REVIEW"  # Safe status change
                    self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error executing approval action: {e}")
            return False
