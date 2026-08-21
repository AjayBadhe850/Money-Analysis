from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# --- Chat & Supervisor Schemas ---
class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class CitationItem(BaseModel):
    source: str
    detail: str
    url: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    agents_involved: List[str] = []
    tools_executed: List[str] = []
    evidence_cards: List[Dict[str, Any]] = []
    suggested_actions: List[Dict[str, Any]] = []
    citations: List[CitationItem] = []


# --- Anomaly Schemas ---
class AnomalyItem(BaseModel):
    id: int
    transaction_id: Optional[int] = None
    transaction_date: Optional[str] = None
    transaction_description: Optional[str] = None
    transaction_amount: Optional[float] = None
    vendor_name: Optional[str] = None
    department_name: Optional[str] = None
    anomaly_score: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str
    reasons: List[str] = []
    status: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyScanResponse(BaseModel):
    scanned_count: int
    anomalies_detected: int
    anomalies: List[AnomalyItem]
    scan_timestamp: datetime


class AnomalyStatusUpdate(BaseModel):
    status: str  # CONFIRMED, FALSE_POSITIVE, RESOLVED


# --- Forecast Schemas ---
class ForecastSeriesItem(BaseModel):
    period: str
    predicted_amount: float
    lower_bound: float
    upper_bound: float
    confidence: float


class ForecastResponse(BaseModel):
    horizon_days: int
    model_type: str
    total_projected_spend: float
    historical_growth_rate: float
    trend: str  # INCREASING, DECREASING, STABLE
    confidence_score: float
    projected_budget_problems: List[Dict[str, Any]] = []
    series: List[ForecastSeriesItem] = []


class ForecastGenerateRequest(BaseModel):
    horizon_days: int = Field(default=90, description="30, 90, 180, 365")
    department_id: Optional[int] = None
    category_id: Optional[int] = None


# --- What-If Simulation Schemas ---
class WhatIfRequest(BaseModel):
    department_spend_adjustments: Optional[Dict[str, float]] = {}  # {"Engineering": -0.15, "Marketing": -0.10}
    vendor_price_adjustments: Optional[Dict[str, float]] = {}  # {"Amazon Web Services": 0.20}
    license_utilization_threshold_cut: Optional[float] = None  # e.g. 0.20 (cancel licenses with <20% utilization)
    revenue_growth_adjustment: Optional[float] = 0.0  # e.g. 0.05 (+5%)


class WhatIfImpactItem(BaseModel):
    category: str
    metric: str
    baseline_value: float
    simulated_value: float
    delta_amount: float
    delta_percentage: float


class WhatIfResponse(BaseModel):
    simulation_name: str
    baseline_monthly_expense: float
    simulated_monthly_expense: float
    monthly_expense_savings: float
    annual_expense_savings: float
    baseline_net_profit: float
    simulated_net_profit: float
    profit_margin_change_pct: float
    detailed_impacts: List[WhatIfImpactItem]
    ai_narrative: str


# --- Savings & Cost Optimization Schemas ---
class SavingsOpportunityItem(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    category: str
    estimated_monthly_saving: float
    estimated_annual_saving: float
    confidence: float
    risk_level: str  # LOW, MEDIUM, HIGH
    evidence: Dict[str, Any] = {}
    source_agent: str


class SavingsOpportunitiesResponse(BaseModel):
    total_potential_monthly: float
    total_potential_annual: float
    opportunities: List[SavingsOpportunityItem]


class CostOptimizationRequest(BaseModel):
    target_savings_amount: float
    timeframe_months: int = 3
    risk_tolerance: str = "MEDIUM"  # LOW, MEDIUM, HIGH


class OptimizationActionItem(BaseModel):
    action_type: str
    title: str
    target_entity: str
    projected_monthly_savings: float
    risk_level: str
    confidence: float
    rationale: str
    can_auto_create_approval: bool = True
    approval_payload: Optional[Dict[str, Any]] = None


class CostOptimizationPlanResponse(BaseModel):
    target_savings: float
    timeframe_months: int
    achievable_monthly_savings: float
    achievable_total_period_savings: float
    target_achieved: bool
    recommended_actions: List[OptimizationActionItem]
    executive_summary: str


# --- Approval Workflow Schemas ---
class ApprovalCreateRequest(BaseModel):
    request_type: str  # CANCEL_SUBSCRIPTION, RENEGOTIATE_VENDOR, BUDGET_OVERRIDE, FLAG_TRANSACTION
    title: str
    details: str
    impact_savings_monthly: float = 0.0
    risk_level: str = "LOW"
    action_payload: Optional[Dict[str, Any]] = None


class ApprovalActionRequest(BaseModel):
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    request_type: str
    title: str
    details: str
    impact_savings_monthly: float
    risk_level: str
    action_payload: Optional[Dict[str, Any]] = None
    status: str  # PENDING, APPROVED, REJECTED, EXECUTED
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    response_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Expense Categorization Schemas ---
class CategorizeRequest(BaseModel):
    description: str
    vendor: Optional[str] = None
    amount: Optional[float] = None


class CategorizeResponse(BaseModel):
    description: str
    predicted_category: str
    confidence_score: float
    prediction_method: str  # RULE, HISTORY, ML, LLM_FALLBACK


class UserCategorizationCorrectionRequest(BaseModel):
    keyword: str
    correct_category: str


# --- Document & RAG Schemas ---
class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_type: str
    chunks_indexed: int
    status: str


class DocumentQueryRequest(BaseModel):
    query: str
    top_k: int = 4


class DocumentQueryResultItem(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    chunk_text: str
    similarity_score: float


class DocumentQueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[DocumentQueryResultItem]
