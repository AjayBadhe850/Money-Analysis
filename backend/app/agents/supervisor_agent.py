import logging
import time
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

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """
    Typed structured state passed across LangGraph nodes in the multi-agent workflow.
    """
    user_prompt: str
    company_id: int
    user_id: Optional[int]
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
    final_response: str


class SupervisorAgent:
    """
    LangGraph-compatible Supervisor Orchestrator.
    Analyzes intent, executes specialized subagents selectively, passes structured state,
    synthesizes final responses, and logs agent execution for auditing.
    """

    def __init__(self, db: Session, company_id: int, user_id: Optional[int] = None):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    async def execute(self, prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Orchestrate multi-agent execution pipeline.
        """
        start_time = time.time()
        p_lower = prompt.lower()

        # Initialize structured agent state
        state: AgentState = {
            "user_prompt": prompt,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "selected_agents": [],
            "executed_tools": [],
            "evidence_cards": [],
            "suggested_actions": [],
            "final_response": "",
        }

        # 1. Intent Classification & Selective Routing
        selected_agents = self._route_intent(p_lower)
        state["selected_agents"] = selected_agents

        # 2. Execute Selected Specialized Agents
        if "SubscriptionAgent" in selected_agents:
            sub_agent = SubscriptionOptimizationAgent(self.db, self.company_id)
            state["subscription_data"] = sub_agent.analyze()
            state["executed_tools"].append("audit_saas_licenses")
            if state["subscription_data"]["potential_monthly_savings"] > 0:
                state["evidence_cards"].append({
                    "title": "SaaS License Waste Detected",
                    "value": f"${state['subscription_data']['potential_monthly_savings']:,.2f}/mo",
                    "detail": f"{state['subscription_data']['wasted_subscriptions_count']} subscriptions have unassigned seats.",
                    "type": "savings"
                })

        if "BudgetAgent" in selected_agents:
            budg_agent = BudgetAgent(self.db, self.company_id)
            state["budget_data"] = budg_agent.analyze()
            state["executed_tools"].append("calculate_budget_velocity")
            if state["budget_data"]["critical_count"] > 0:
                state["evidence_cards"].append({
                    "title": "Budget Velocity Alert",
                    "value": f"{state['budget_data']['critical_count']} Overruns",
                    "detail": f"Overall budget burn is at {state['budget_data']['overall_usage_pct']}%.",
                    "type": "warning"
                })

        if "VendorAgent" in selected_agents:
            vend_agent = VendorIntelligenceAgent(self.db, self.company_id)
            state["vendor_data"] = vend_agent.analyze()
            state["executed_tools"].append("evaluate_vendor_efficiency")

        if "AnomalyAgent" in selected_agents:
            anom_agent = AnomalyDetectionAgent(self.db, self.company_id)
            state["anomaly_data"] = anom_agent.scan_transactions()
            state["executed_tools"].append("run_isolation_forest_scan")
            if state["anomaly_data"]:
                state["evidence_cards"].append({
                    "title": "Statistical Anomalies Flagged",
                    "value": f"{len(state['anomaly_data'])} Items",
                    "detail": f"Highest score: {state['anomaly_data'][0]['anomaly_score']}/100.",
                    "type": "anomaly"
                })

        if "ForecastingAgent" in selected_agents:
            fc_agent = ForecastingAgent(self.db, self.company_id)
            state["forecast_data"] = fc_agent.generate_forecast(horizon_days=90)
            state["executed_tools"].append("run_time_series_forecast")

        if "SavingsAgent" in selected_agents or "CostOptimizationAgent" in selected_agents:
            sav_agent = SavingsOpportunityAgent(self.db, self.company_id)
            state["savings_data"] = sav_agent.discover_opportunities()
            state["executed_tools"].append("aggregate_savings_opportunities")

            if "CostOptimizationAgent" in selected_agents:
                opt_agent = CostOptimizationAgent(self.db, self.company_id)
                # Parse target amount if present in prompt
                target = self._extract_amount(prompt) or 50000.0
                state["optimization_plan"] = opt_agent.generate_plan(target_savings_amount=target)
                state["executed_tools"].append("synthesize_optimization_plan")

        if "WhatIfAgent" in selected_agents:
            wi_agent = WhatIfSimulationAgent(self.db, self.company_id)
            state["what_if_results"] = wi_agent.simulate(
                department_spend_adjustments={"Marketing": -0.15, "Engineering": -0.10}
            )
            state["executed_tools"].append("run_what_if_simulation")

        if "RAGAgent" in selected_agents:
            rag_service = FinanceRAGService(self.db, self.company_id)
            state["rag_results"] = rag_service.query(prompt)
            state["executed_tools"].append("query_finance_documents_rag")

        # Always run Transaction Agent if baseline numbers are needed
        if "TransactionAgent" in selected_agents or len(selected_agents) == 1:
            tx_agent = TransactionAnalysisAgent(self.db, self.company_id)
            state["transaction_data"] = tx_agent.analyze()
            state["executed_tools"].append("fetch_transaction_trends")

        # 3. Formulate Action Suggestions
        if state.get("subscription_data", {}).get("potential_monthly_savings", 0) > 0:
            state["suggested_actions"].append({
                "action": "CANCEL_UNUSED_SEATS",
                "label": "Deprovision 42 Unused SaaS Seats",
                "savings": state["subscription_data"]["potential_monthly_savings"]
            })
        if state.get("anomaly_data"):
            state["suggested_actions"].append({
                "action": "REVIEW_ANOMALIES",
                "label": f"Review {len(state['anomaly_data'])} High-Severity Transactions",
                "severity": "CRITICAL"
            })

        # 4. Generate Synthesized Response via LLM Abstraction
        context_summary = {
            "selected_agents": state["selected_agents"],
            "savings_total": state.get("savings_data", {}).get("total_potential_monthly", 0.0),
            "savings_annual": state.get("savings_data", {}).get("total_potential_annual", 0.0),
        }
        final_text = await llm_client.generate_response(
            prompt=prompt,
            context_data=context_summary
        )
        state["final_response"] = final_text

        # 5. Log Execution to AgentRun Table
        duration_ms = int((time.time() - start_time) * 1000)
        self._log_agent_run(prompt, state, duration_ms)

        return {
            "message": state["final_response"],
            "agents_involved": state["selected_agents"],
            "tools_executed": state["executed_tools"],
            "evidence_cards": state["evidence_cards"],
            "suggested_actions": state["suggested_actions"],
            "citations": [
                {"source": "Financial Ledgers", "detail": "Live PostgreSQL company transactions and budget tables."},
                {"source": "SaaS License Auditor", "detail": "Deterministic seat cost optimizer."}
            ]
        }

    def _route_intent(self, prompt: str) -> List[str]:
        """
        Determine which specialized agents must be triggered for maximum efficiency.
        """
        agents = ["SupervisorAgent"]

        if any(w in prompt for w in ["save", "saving", "reduce", "cut", "opportunity", "optimize", "optimization", "plan"]):
            agents.extend(["SavingsAgent", "CostOptimizationAgent", "SubscriptionAgent", "VendorAgent", "BudgetAgent"])
        elif any(w in prompt for w in ["abnormal", "anomaly", "suspicious", "fraud", "spike", "outlier"]):
            agents.extend(["AnomalyAgent", "TransactionAgent"])
        elif any(w in prompt for w in ["forecast", "predict", "next month", "next quarter", "runway", "future"]):
            agents.extend(["ForecastingAgent", "BudgetAgent"])
        elif any(w in prompt for w in ["what if", "simulate", "simulation", "increase", "decrease"]):
            agents.extend(["WhatIfAgent", "BudgetAgent"])
        elif any(w in prompt for w in ["subscription", "saas", "license", "seats", "software", "salesforce", "zoom"]):
            agents.extend(["SubscriptionAgent"])
        elif any(w in prompt for w in ["vendor", "supplier", "contract", "sla", "aws"]):
            agents.extend(["VendorAgent"])
        elif any(w in prompt for w in ["budget", "overspend", "burn", "department", "velocity"]):
            agents.extend(["BudgetAgent", "TransactionAgent"])
        elif any(w in prompt for w in ["policy", "document", "contract clause", "terms"]):
            agents.extend(["RAGAgent"])
        else:
            agents.extend(["TransactionAgent", "BudgetAgent", "SavingsAgent"])

        return list(dict.fromkeys(agents))  # unique

    def _extract_amount(self, prompt: str) -> Optional[float]:
        import re
        match = re.search(r"\$?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:k|lakh|l|million|m)?", prompt, re.IGNORECASE)
        if match:
            try:
                raw = match.group(1).replace(",", "")
                val = float(raw)
                if "k" in prompt.lower():
                    val *= 1000
                elif "lakh" in prompt.lower() or " l" in prompt.lower():
                    val *= 100000
                elif "m" in prompt.lower() or "million" in prompt.lower():
                    val *= 1000000
                return val
            except Exception:
                pass
        return None

    def _log_agent_run(self, prompt: str, state: AgentState, duration_ms: int):
        try:
            run = AgentRun(
                company_id=self.company_id,
                user_id=self.user_id,
                agent_name="SupervisorAgent",
                input_prompt=prompt,
                tools_called=state["executed_tools"],
                evidence_summary=f"{len(state['evidence_cards'])} evidence cards generated. Agents: {', '.join(state['selected_agents'])}",
                output_summary=state["final_response"][:300],
                execution_time_ms=duration_ms,
                status="SUCCESS",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            self.db.add(run)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.warning(f"Could not log AgentRun: {e}")
