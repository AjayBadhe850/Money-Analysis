from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True, index=True)
    anomaly_score = Column(Float, nullable=False, default=0.0)  # 0 to 100
    severity = Column(String(50), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    explanation = Column(Text, nullable=False)
    reasons = Column(JSON, nullable=True)  # List of string reasons
    features_snapshot = Column(JSON, nullable=True)
    status = Column(String(50), default="DETECTED", nullable=False, index=True)  # DETECTED, CONFIRMED, FALSE_POSITIVE, RESOLVED
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_anom_company_status", "company_id", "status"),
        Index("idx_anom_company_severity", "company_id", "severity"),
    )

    # Relationships
    transaction = relationship("Transaction")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    period_date = Column(String(50), nullable=False)  # e.g. "2026-09-01" or "2026-Q4"
    horizon_days = Column(Integer, default=30, nullable=False, index=True)  # 30, 90, 180, 365
    predicted_amount = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.95, nullable=False)
    model_type = Column(String(100), default="IsolationRidgeRegression/Ensemble", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_fc_company_horizon", "company_id", "horizon_days"),
    )


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)  # e.g. "SupervisorAgent", "CostOptimizationAgent"
    input_prompt = Column(Text, nullable=False)
    tools_called = Column(JSON, nullable=True)  # List of tool names & timestamps
    evidence_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="SUCCESS", nullable=False, index=True)  # RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_run_company_agent", "company_id", "agent_name"),
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    request_type = Column(String(100), nullable=False, index=True)  # CANCEL_SUBSCRIPTION, RENEGOTIATE_VENDOR, BUDGET_OVERRIDE, FLAG_TRANSACTION
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=False)
    impact_savings_monthly = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String(50), default="LOW", nullable=False, index=True)  # LOW, MEDIUM, HIGH
    action_payload = Column(JSON, nullable=True)  # Specific target IDs and parameter adjustments
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXECUTED
    response_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_appr_company_status", "company_id", "status"),
    )


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # "PDF", "CSV", "TXT", "DOCX"
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="INDEXED", nullable=False, index=True)  # UPLOADED, INDEXED, FAILED
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    embeddings = relationship("EmbeddingRecord", back_populates="document", cascade="all, delete-orphan")


class EmbeddingRecord(Base):
    __tablename__ = "embedding_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, default=0, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(JSON, nullable=True)  # Prepared for pgvector integration
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_emb_company_doc", "company_id", "document_id"),
    )

    # Relationships
    document = relationship("UploadedDocument", back_populates="embeddings")


class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    category_name = Column(String(100), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    source = Column(String(50), default="USER_CORRECTION", nullable=False)  # RULE, USER_CORRECTION, ML
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_catrule_company_keyword", "company_id", "keyword"),
    )
