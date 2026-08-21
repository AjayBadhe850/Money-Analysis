import logging
import time
from decimal import Decimal
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.agents.transaction_agent import TransactionAnalysisAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.anomaly_agent import AnomalyDetectionAgent
from app.agents.vendor_agent import VendorIntelligenceAgent
from app.agents.subscription_agent import SubscriptionOptimizationAgent
from app.agents.forecasting_agent import ForecastingAgent
from app.agents.savings_agent import SavingsOpportunityAgent
from app.agents.cost_optimization_agent import CostOptimizationAgent
from app.agents.what_if_agent import WhatIfSimulationAgent
from app.agents.approval_agent import ApprovalAgent
from app.agents.report_agent import ReportAgent
from app.services.rag_service import FinanceRAGService
from app.core.llm import llm_client
from app.models.future_ai import AgentRun, AgentMessage
from app.models.company import Company

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """
    Typed structured state passed across LangGraph nodes in the multi-agent workflow.
    """
    user_prompt: str
    company_id: int
    user_id: Optional[int]
    currency: str
    selected_agents: List[str]
    executed_tools: List[str]
    transaction_data: Optional[Dict[str, Any]]
    budget_data: Optional[Dict[str, Any]]
    anomaly_data: Optional[List[Dict[str, Any]]]
    vendor_data: Optional[Dict[str, Any]]
    subscription_data: Optional[Dict[str, Any]]
    forecast_data: Optional[Dict[str, Any]]
    savings_data: Optional[Dict[str, Any]]
    optimization_plan: Optional[Dict[str, Any]]
    what_if_results: Optional[Dict[str, Any]]
    rag_results: Optional[Dict[str, Any]]
    evidence_cards: List[Dict[str, Any]]
    suggested_actions: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    final_response: str


def _currency_symbol(code: str) -> str:
    """Return currency symbol for common currency codes."""
    return {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥", "AUD": "A$", "CAD": "C$"}.get(
        code.upper(), code
    )


class SupervisorAgent:
    """
    LangGraph-compatible Supervisor Orchestrator.
    Analyses intent, executes specialized subagents selectively, passes structured state,
    synthesises final responses, and logs agent execution for auditing.

    Routing guarantees:
    - FINANCIAL_METRIC queries → TransactionAgent only (no optimisation agents)
    - COST_OPTIMIZATION queries → SavingsAgent + CostOptimizationAgent + supporting agents
    - Citations, evidence cards, and suggested actions are dynamically built from
      agents that were *actually* executed. No static/fabricated data is included.
    """

    # ── Intent keyword sets ──────────────────────────────────────────────────
    _FINANCIAL_METRIC_PHRASES = frozenset([
        "total expenses", "total expense", "total spending", "total spend",
        "how much did we spend", "how much have we spent", "how much did we pay",
        "total revenue", "total income", "net profit", "net loss", "gross profit",
        "expenses this month", "revenue this month", "spending this month",
        "income this month", "what did we spend", "what is our spend",
        "how much was spent", "overall expenses", "overall revenue",
        "total cost", "total costs", "department spending", "department spend",
        "category spending", "category spend",
    ])

    _OPTIMIZATION_KEYWORDS = frozenset([
        "save", "saving", "reduce", "cut", "opportunity", "optimize",
        "optimization", "cost reduction", "reduce expenses", "reduce costs",
        "lower our costs", "cut costs", "spend less", "efficiency",
        "how can we save", "find savings", "cost saving", "cheaper",
    ])

    _ANOMALY_KEYWORDS = frozenset([
        "abnormal", "anomaly", "anomalies", "suspicious", "fraud",
        "spike", "outlier", "unusual", "irregular", "detect",
    ])

    _FORECAST_KEYWORDS = frozenset([
        "forecast", "predict", "prediction", "next month", "next quarter",
        "runway", "future", "project spending", "projected", "outlook",
        "what will we spend", "spend in",
    ])

    _WHATIF_KEYWORDS = frozenset([
        "what if", "simulate", "simulation", "scenario", "if we reduce",
        "if we increase", "what happens if",
    ])

    _SUBSCRIPTION_KEYWORDS = frozenset([
        "subscription", "saas", "license", "licences", "seats",
        "software tool", "salesforce", "zoom", "slack", "jira", "asana",
        "unused license", "unused seat",
    ])

    _VENDOR_KEYWORDS = frozenset([
        "vendor", "supplier", "contract", "sla", "aws", "which vendor",
        "most expensive vendor", "compare vendor", "supplier cost",
    ])

    _BUDGET_KEYWORDS = frozenset([
        "budget", "overspend", "burn rate", "department budget",
        "budget utilization", "budget usage", "over budget",
        "exceeding budget", "budget allocation",
    ])

    _RAG_KEYWORDS = frozenset([
        "policy", "document", "contract clause", "terms and conditions",
        "compliance", "regulation", "uploaded document",
    ])

    def __init__(self, db: Session, company_id: int, user_id: Optional[int] = None):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id
        # Resolve company currency once at construction time
        company = db.query(Company).filter(Company.id == company_id).first()
        self.currency_code: str = (company.currency or "USD") if company else "USD"
        self.currency_sym: str = _currency_symbol(self.currency_code)

    async def execute(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-agent execution pipeline.
        """
        start_time = time.time()
        p_lower = prompt.lower()

        # Initialise structured agent state
        state: AgentState = {
            "user_prompt": prompt,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "currency": self.currency_code,
            "selected_agents": [],
            "executed_tools": [],
            "evidence_cards": [],
            "suggested_actions": [],
            "citations": [],
            "final_response": "",
        }

        # ── 1. Intent Classification & Selective Routing ─────────────────────
        selected_agents = self._route_intent(p_lower)
        state["selected_agents"] = selected_agents

        # ── 2. Execute Selected Specialised Agents ───────────────────────────
        if "SubscriptionAgent" in selected_agents:
            try:
                sub_agent = SubscriptionOptimizationAgent(self.db, self.company_id)
                state["subscription_data"] = sub_agent.analyze()
                state["executed_tools"].append("audit_saas_licenses")
                state["citations"].append({
                    "source": "SaaS License Auditor",
                    "detail": "Deterministic seat-cost analysis from live subscription records.",
                })
                pot_sav = state["subscription_data"].get("potential_monthly_savings", 0)
                if pot_sav and pot_sav > 0:
                    state["evidence_cards"].append({
                        "title": "SaaS License Waste Detected",
                        "value": f"{self.currency_sym}{pot_sav:,.2f}/mo",
                        "detail": (
                            f"{state['subscription_data']['wasted_subscriptions_count']} "
                            "subscriptions have unassigned seats."
                        ),
                        "type": "savings",
                    })
                    state["suggested_actions"].append({
                        "action": "CANCEL_UNUSED_SEATS",
                        "label": (
                            f"Deprovision {sum(s['unused_licenses'] for s in state['subscription_data'].get('subscriptions', []))} "
                            "Unused SaaS Seats"
                        ),
                        "savings": pot_sav,
                    })
            except Exception as exc:
                logger.warning("SubscriptionAgent failed: %s", exc)

        if "BudgetAgent" in selected_agents:
            try:
                budg_agent = BudgetAgent(self.db, self.company_id)
                state["budget_data"] = budg_agent.analyze()
                state["executed_tools"].append("calculate_budget_velocity")
                state["citations"].append({
                    "source": "Budget Ledger",
                    "detail": "Live company budget allocation and burn-rate records.",
                })
                if state["budget_data"]["critical_count"] > 0:
                    state["evidence_cards"].append({
                        "title": "Budget Velocity Alert",
                        "value": f"{state['budget_data']['critical_count']} Overruns",
                        "detail": f"Overall budget burn is at {state['budget_data']['overall_usage_pct']}%.",
                        "type": "warning",
                    })
            except Exception as exc:
                logger.warning("BudgetAgent failed: %s", exc)

        if "VendorAgent" in selected_agents:
            try:
                vend_agent = VendorIntelligenceAgent(self.db, self.company_id)
                state["vendor_data"] = vend_agent.analyze()
                state["executed_tools"].append("evaluate_vendor_efficiency")
                state["citations"].append({
                    "source": "Vendor Intelligence Engine",
                    "detail": "Vendor efficiency scores and spend analysis from procurement records.",
                })
            except Exception as exc:
                logger.warning("VendorAgent failed: %s", exc)

        if "AnomalyAgent" in selected_agents:
            try:
                anom_agent = AnomalyDetectionAgent(self.db, self.company_id)
                state["anomaly_data"] = anom_agent.scan_transactions()
                state["executed_tools"].append("run_isolation_forest_scan")
                state["citations"].append({
                    "source": "Anomaly Detection Engine",
                    "detail": "Isolation Forest statistical scan of company transaction records.",
                })
                if state["anomaly_data"]:
                    state["evidence_cards"].append({
                        "title": "Statistical Anomalies Flagged",
                        "value": f"{len(state['anomaly_data'])} Items",
                        "detail": f"Highest score: {state['anomaly_data'][0].get('anomaly_score', 'N/A')}/100.",
                        "type": "anomaly",
                    })
                    state["suggested_actions"].append({
                        "action": "REVIEW_ANOMALIES",
                        "label": f"Review {len(state['anomaly_data'])} High-Severity Transactions",
                        "severity": "CRITICAL",
                    })
            except Exception as exc:
                logger.warning("AnomalyAgent failed: %s", exc)

        if "ForecastingAgent" in selected_agents:
            try:
                fc_agent = ForecastingAgent(self.db, self.company_id)
                state["forecast_data"] = fc_agent.generate_forecast(horizon_days=90)
                state["executed_tools"].append("run_time_series_forecast")
                state["citations"].append({
                    "source": "Time-Series Forecasting Engine",
                    "detail": "Ridge regression model trained on historical company expenditure data.",
                })
            except Exception as exc:
                logger.warning("ForecastingAgent failed: %s", exc)

        if "SavingsAgent" in selected_agents or "CostOptimizationAgent" in selected_agents:
            try:
                sav_agent = SavingsOpportunityAgent(self.db, self.company_id)
                state["savings_data"] = sav_agent.discover_opportunities()
                state["executed_tools"].append("aggregate_savings_opportunities")
                state["citations"].append({
                    "source": "Savings Opportunity Engine",
                    "detail": "Cross-domain cost reduction analysis: SaaS, Vendors, Budgets.",
                })
            except Exception as exc:
                logger.warning("SavingsAgent failed: %s", exc)

            if "CostOptimizationAgent" in selected_agents:
                try:
                    opt_agent = CostOptimizationAgent(self.db, self.company_id)
                    target = self._extract_amount(prompt) or 50000.0
                    state["optimization_plan"] = opt_agent.generate_plan(target_savings_amount=target)
                    state["executed_tools"].append("synthesize_optimization_plan")
                    state["citations"].append({
                        "source": "Cost Optimisation Planner",
                        "detail": "Risk-stratified action plan derived from multi-agent analysis.",
                    })
                except Exception as exc:
                    logger.warning("CostOptimizationAgent failed: %s", exc)

        if "WhatIfAgent" in selected_agents:
            try:
                wi_agent = WhatIfSimulationAgent(self.db, self.company_id)
                state["what_if_results"] = wi_agent.simulate(
                    department_spend_adjustments={"Marketing": -0.15, "Engineering": -0.10}
                )
                state["executed_tools"].append("run_what_if_simulation")
                state["citations"].append({
                    "source": "What-If Simulation Engine",
                    "detail": "Deterministic P&L simulation using current budget and transaction data.",
                })
            except Exception as exc:
                logger.warning("WhatIfAgent failed: %s", exc)

        if "RAGAgent" in selected_agents:
            try:
                rag_service = FinanceRAGService(self.db, self.company_id)
                state["rag_results"] = rag_service.query(prompt)
                state["executed_tools"].append("query_finance_documents_rag")
                state["citations"].append({
                    "source": "Finance Document RAG",
                    "detail": "Semantic search across uploaded finance policies and contracts.",
                })
            except Exception as exc:
                logger.warning("RAGAgent failed: %s", exc)

        # TransactionAgent – always run when in selected list
        if "TransactionAgent" in selected_agents:
            try:
                tx_agent = TransactionAnalysisAgent(self.db, self.company_id)
                state["transaction_data"] = tx_agent.analyze()
                state["executed_tools"].append("fetch_transaction_trends")
                state["citations"].append({
                    "source": "Financial Ledgers",
                    "detail": "Live PostgreSQL company transaction records (company-isolated).",
                })
                # Build evidence card for financial metric queries
                td = state["transaction_data"]
                sym = self.currency_sym
                state["evidence_cards"].append({
                    "title": "Transaction Summary",
                    "value": f"{sym}{td.get('total_expenses', 0):,.2f} expenses",
                    "detail": (
                        f"{td.get('total_transactions', 0)} transactions | "
                        f"Revenue: {sym}{td.get('total_revenue', 0):,.2f} | "
                        f"Net: {sym}{td.get('net_profit', 0):,.2f}"
                    ),
                    "type": "info",
                })
            except Exception as exc:
                logger.warning("TransactionAgent failed: %s", exc)

        # ── 3. Generate Synthesised Response via LLM ─────────────────────────
        # Build the system instruction based on intent.
        # For financial metric queries: instruct LLM to lead with the verified number.
        is_metric_query = self._is_financial_metric_query(p_lower)
        is_optimization_query = self._is_optimization_query(p_lower)

        system_instruction = self._build_system_instruction(
            is_metric_query=is_metric_query,
            is_optimization_query=is_optimization_query,
            state=state,
        )

        # Context passed to LLM – only data from actually-executed agents.
        # Critically: do NOT include raw DB objects, secrets, or internal IDs.
        context_summary: Dict[str, Any] = {
            "selected_agents": state["selected_agents"],
            "currency_code": self.currency_code,
            "currency_symbol": self.currency_sym,
        }
        if state.get("transaction_data"):
            td = state["transaction_data"]
            context_summary["transaction_summary"] = {
                "total_transactions": td.get("total_transactions"),
                "total_expenses": td.get("total_expenses"),
                "total_revenue": td.get("total_revenue"),
                "net_profit": td.get("net_profit"),
                "monthly_burn_rate": td.get("monthly_burn_rate"),
                "expense_growth_rate": td.get("expense_growth_rate"),
                "top_categories": td.get("top_categories", [])[:5],
                "top_vendors": td.get("top_vendors", [])[:5],
                "department_spending": td.get("department_spending", [])[:5],
            }
        if state.get("budget_data"):
            bd = state["budget_data"]
            context_summary["budget_summary"] = {
                "total_allocated": bd.get("total_allocated"),
                "total_spent": bd.get("total_spent"),
                "overall_usage_pct": bd.get("overall_usage_pct"),
                "critical_count": bd.get("critical_count"),
                "at_risk_departments": bd.get("at_risk_departments", [])[:5],
            }
        if state.get("anomaly_data"):
            context_summary["anomaly_count"] = len(state["anomaly_data"])
            context_summary["top_anomalies"] = state["anomaly_data"][:3]
        if state.get("vendor_data"):
            vd = state["vendor_data"]
            context_summary["vendor_summary"] = {
                "vendor_count": vd.get("vendor_count"),
                "top_vendors_by_spend": vd.get("vendors", [])[:5],
                "negotiation_targets": vd.get("negotiation_targets", [])[:3],
            }
        if state.get("subscription_data"):
            sd = state["subscription_data"]
            context_summary["subscription_summary"] = {
                "total_monthly_spend": sd.get("total_monthly_spend"),
                "potential_monthly_savings": sd.get("potential_monthly_savings"),
                "wasted_subscriptions_count": sd.get("wasted_subscriptions_count"),
                "subscriptions_count": sd.get("subscriptions_count"),
                "upcoming_renewals": sd.get("upcoming_renewals", [])[:3],
            }
        if state.get("forecast_data"):
            context_summary["forecast_data"] = state["forecast_data"]
        if state.get("savings_data"):
            sv = state["savings_data"]
            context_summary["savings_summary"] = {
                "total_potential_monthly": sv.get("total_potential_monthly"),
                "total_potential_annual": sv.get("total_potential_annual"),
                "opportunities_count": sv.get("opportunities_count"),
                "top_opportunities": sv.get("opportunities", [])[:4],
            }
        if state.get("optimization_plan"):
            context_summary["optimization_plan"] = state["optimization_plan"]
        if state.get("what_if_results"):
            context_summary["what_if_results"] = state["what_if_results"]
        if state.get("rag_results"):
            context_summary["rag_results"] = state["rag_results"]

        try:
            final_text = await llm_client.generate_response(
                prompt=prompt,
                system_instruction=system_instruction,
                context_data=context_summary,
            )
        except Exception as exc:
            logger.error("LLM response generation failed: %s", exc)
            final_text = self._build_direct_response(state, p_lower)

        state["final_response"] = final_text

        # ── 4. Log Execution to AgentRun Table ────────────────────────────────
        duration_ms = int((time.time() - start_time) * 1000)
        self._log_agent_run(prompt, state, duration_ms)

        return {
            "message": state["final_response"],
            "agents_involved": state["selected_agents"],
            "tools_executed": state["executed_tools"],
            "evidence_cards": state["evidence_cards"],
            "suggested_actions": state["suggested_actions"],
            "citations": state["citations"],
        }

    # ── Intent routing ────────────────────────────────────────────────────────

    def _route_intent(self, prompt: str) -> List[str]:
        """
        Route user requests to the minimum required specialised agents.
        Uses deterministic phrase/keyword matching – no LLM call required for routing.
        Priorities are evaluated in order; first match wins.
        """
        agents = ["SupervisorAgent"]

        # ── Priority 0: financial metric questions ──
        # Must be checked BEFORE optimization to prevent "reduce expenses" from
        # being confused with "what are our expenses".
        if self._is_financial_metric_query(prompt):
            agents.append("TransactionAgent")
            return list(dict.fromkeys(agents))

        # ── Priority 1: what-if simulation (must come before optimization,
        #    because "what if we reduce..." contains "reduce") ──
        if any(w in prompt for w in self._WHATIF_KEYWORDS):
            agents.append("WhatIfAgent")
            return list(dict.fromkeys(agents))

        # ── Priority 2: cost optimization ──
        if self._is_optimization_query(prompt):
            agents.extend([
                "SavingsAgent",
                "CostOptimizationAgent",
                "SubscriptionAgent",
                "VendorAgent",
                "BudgetAgent",
                "TransactionAgent",
            ])
            return list(dict.fromkeys(agents))

        # ── Priority 3: anomaly detection ──
        if any(w in prompt for w in self._ANOMALY_KEYWORDS):
            agents.extend(["AnomalyAgent", "TransactionAgent"])
            return list(dict.fromkeys(agents))

        # ── Priority 4: forecasting ──
        if any(w in prompt for w in self._FORECAST_KEYWORDS):
            agents.append("ForecastingAgent")
            return list(dict.fromkeys(agents))

        # ── Priority 5: subscription analysis ──
        if any(w in prompt for w in self._SUBSCRIPTION_KEYWORDS):
            agents.append("SubscriptionAgent")
            return list(dict.fromkeys(agents))

        # ── Priority 6: vendor analysis ──
        if any(w in prompt for w in self._VENDOR_KEYWORDS):
            agents.append("VendorAgent")
            return list(dict.fromkeys(agents))

        # ── Priority 7: budget analysis ──
        if any(w in prompt for w in self._BUDGET_KEYWORDS):
            agents.extend(["BudgetAgent", "TransactionAgent"])
            return list(dict.fromkeys(agents))

        # ── Priority 8: document / RAG ──
        if any(w in prompt for w in self._RAG_KEYWORDS):
            agents.append("RAGAgent")
            return list(dict.fromkeys(agents))

        # ── Default: general finance question → TransactionAgent only ──
        agents.append("TransactionAgent")
        return list(dict.fromkeys(agents))

    def _is_financial_metric_query(self, prompt_lower: str) -> bool:
        """Return True if the prompt is asking for a direct financial metric."""
        return any(phrase in prompt_lower for phrase in self._FINANCIAL_METRIC_PHRASES)

    def _is_optimization_query(self, prompt_lower: str) -> bool:
        """Return True if the prompt is asking for cost optimisation advice."""
        return any(kw in prompt_lower for kw in self._OPTIMIZATION_KEYWORDS)

    # ── Response helpers ──────────────────────────────────────────────────────

    def _build_system_instruction(
        self,
        is_metric_query: bool,
        is_optimization_query: bool,
        state: AgentState,
    ) -> str:
        """
        Build a targeted system instruction for the LLM based on intent.
        The instruction prevents LLM from fabricating financial numbers.
        """
        sym = self.currency_sym
        base = (
            "You are the Money Analysis Finance Controller AI. "
            "You must ONLY report financial figures that are explicitly provided in the context data below. "
            "You must NEVER invent, estimate, or hallucinate any monetary amounts, percentages, or counts. "
            f"Use {self.currency_code} ({sym}) as the currency symbol throughout your response.\n\n"
        )

        if is_metric_query and state.get("transaction_data"):
            td = state["transaction_data"]
            return (
                base
                + "The user is asking for a factual financial metric. "
                + "Lead your response directly with the verified number(s) from the context. "
                + "Do NOT lead with optimization recommendations, savings analysis, or suggestions. "
                + f"Verified data: total_expenses={sym}{td.get('total_expenses', 0):,.2f}, "
                + f"total_revenue={sym}{td.get('total_revenue', 0):,.2f}, "
                + f"net_profit={sym}{td.get('net_profit', 0):,.2f}."
            )

        if is_optimization_query:
            return (
                base
                + "The user is asking for cost optimisation advice. "
                + "Provide actionable recommendations based only on the data provided in context. "
                + "Do not fabricate savings figures not present in the context."
            )

        return base + "Answer the user's finance question using only the data provided in the context."

    def _build_direct_response(self, state: AgentState, prompt_lower: str) -> str:
        """
        Build a deterministic response when the LLM is unavailable.
        Uses verified data from executed agents only.
        """
        sym = self.currency_sym
        parts = []

        if state.get("transaction_data"):
            td = state["transaction_data"]
            if any(ph in prompt_lower for ph in ["total expense", "total spending", "how much did we spend", "how much have we spent"]):
                parts.append(f"Your total expenses are {sym}{td.get('total_expenses', 0):,.2f}.")
            elif "total revenue" in prompt_lower or "total income" in prompt_lower:
                parts.append(f"Your total revenue is {sym}{td.get('total_revenue', 0):,.2f}.")
            elif "net profit" in prompt_lower or "net loss" in prompt_lower:
                parts.append(f"Your net profit is {sym}{td.get('net_profit', 0):,.2f}.")
            else:
                parts.append(
                    f"Financial Summary: Total Expenses: {sym}{td.get('total_expenses', 0):,.2f} | "
                    f"Total Revenue: {sym}{td.get('total_revenue', 0):,.2f} | "
                    f"Net Profit: {sym}{td.get('net_profit', 0):,.2f}."
                )

        if state.get("savings_data"):
            sv = state["savings_data"]
            m = sv.get("total_potential_monthly", 0)
            if m and m > 0:
                parts.append(
                    f"Potential monthly savings identified: {sym}{m:,.2f} ({sym}{sv.get('total_potential_annual', 0):,.2f} annually)."
                )

        if not parts:
            parts.append(
                "I have reviewed the available financial data. "
                "Please ask a more specific question or check the dashboard for detailed metrics."
            )

        return " ".join(parts)

    def _extract_amount(self, prompt: str) -> Optional[float]:
        """Extract a monetary amount from a natural language prompt."""
        import re
        match = re.search(
            r"[₹$€£]?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:k|lakh|l|million|m)?",
            prompt,
            re.IGNORECASE,
        )
        if match:
            try:
                raw = match.group(1).replace(",", "")
                val = float(raw)
                p_lower = prompt.lower()
                if "k" in p_lower:
                    val *= 1000
                elif "lakh" in p_lower or " l" in p_lower:
                    val *= 100_000
                elif "m" in p_lower or "million" in p_lower:
                    val *= 1_000_000
                return val
            except (ValueError, ArithmeticError) as exc:
                logger.debug("Could not parse amount from prompt: %s", exc)
        return None

    def _log_agent_run(self, prompt: str, state: AgentState, duration_ms: int) -> None:
        try:
            run = AgentRun(
                company_id=self.company_id,
                user_id=self.user_id,
                agent_name="SupervisorAgent",
                input_prompt=prompt,
                tools_called=state["executed_tools"],
                evidence_summary=(
                    f"{len(state['evidence_cards'])} evidence cards generated. "
                    f"Agents: {', '.join(state['selected_agents'])}"
                ),
                output_summary=state["final_response"][:300],
                execution_time_ms=duration_ms,
                status="SUCCESS",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            self.db.add(run)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.warning("Could not log AgentRun: %s", exc)
