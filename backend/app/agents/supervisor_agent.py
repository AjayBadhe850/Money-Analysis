import logging
import re
import ast
import operator
import time
from typing import Dict, Any, List, Optional, TypedDict, Tuple
from datetime import datetime, timezone, date, timedelta
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
from app.services.rag_service import FinanceRAGService
from app.core.llm import llm_client
from app.models.future_ai import AgentRun
from app.models.company import Company
from app.models.department import Department

logger = logging.getLogger(__name__)


SAFE_MATH_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _try_safe_math_eval(prompt: str) -> Optional[str]:
    """Safely evaluate arithmetic calculations like '10+2', '500 * 12', etc."""
    cleaned = prompt.strip().rstrip("?=").strip()
    cleaned = re.sub(
        r"^(?:what is|calculate|compute|solve|how much is)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE
    ).strip()
    if not re.match(r"^[\d\s\+\-\*\/\%\(\)\.\,\^]+$", cleaned) or not re.search(r"[\+\-\*\/\%\^]", cleaned):
        return None
    expr = cleaned.replace("^", "**").replace(",", "")
    try:
        tree = ast.parse(expr, mode='eval')

        def _eval_node(node):
            if isinstance(node, ast.Expression):
                return _eval_node(node.body)
            elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                op_type = type(node.op)
                if op_type in SAFE_MATH_OPERATORS:
                    return SAFE_MATH_OPERATORS[op_type](left, right)
                raise ValueError("Unsupported op")
            elif isinstance(node, ast.UnaryOp):
                operand = _eval_node(node.operand)
                op_type = type(node.op)
                if op_type in SAFE_MATH_OPERATORS:
                    return SAFE_MATH_OPERATORS[op_type](operand)
                raise ValueError("Unsupported op")
            else:
                raise ValueError("Unsupported AST node")

        val = _eval_node(tree)
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return f"{cleaned} = **{val:,}**" if isinstance(val, int) else f"{cleaned} = **{val:,.4f}**".rstrip("0").rstrip(".")
    except Exception:
        return None


class AgentState(TypedDict, total=False):
    """
    Typed structured state passed across LangGraph nodes in the multi-agent workflow.
    """
    user_prompt: str
    company_id: int
    user_id: Optional[int]
    currency: str
    period_label: str
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
    return {
        "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£",
        "JPY": "¥", "AUD": "A$", "CAD": "C$",
    }.get(code.upper(), code)


class SupervisorAgent:
    """
    LangGraph-compatible Supervisor Orchestrator.

    Routing priorities (first match wins):
    1. Math calculation / General greeting / Help
    2. What-If  – before optimization ("what if we reduce…" contains "reduce")
    3. Cost Optimization
    4. Direct Financial Metrics  – after optimization ("how can we reduce total expenses?" must not hit metric)
    5. Anomaly Detection
    6. Forecasting
    7. Subscription Analysis
    8. Vendor Analysis
    9. Budget Analysis
    10. Document RAG
    11. Safe default → TransactionAgent

    Guarantees:
    - Financial metric queries never invoke Gemini for the authoritative number.
    - No hardcoded savings figures.
    - No hardcoded what-if department adjustments.
    - Citations, evidence cards, and suggested actions are built only from
      agents that were actually executed.
    - Every DB query is scoped to self.company_id.
    """

    # ── Intent keyword sets ───────────────────────────────────────────────────

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

    _GREETING_PHRASES = frozenset([
        "hi", "hello", "hey", "help", "who are you", "what can you do",
        "capabilities", "good morning", "good afternoon", "good evening",
        "how does this work", "how do you work", "commands"
    ])

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self, db: Session, company_id: int, user_id: Optional[int] = None):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id
        company = db.query(Company).filter(Company.id == company_id).first()
        self.currency_code: str = (company.currency or "USD") if company else "USD"
        self.currency_sym: str = _currency_symbol(self.currency_code)

    async def execute(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Orchestrate multi-agent execution pipeline."""
        start_time = time.time()
        p_lower = prompt.lower().strip()

        # ── 0. Handle Direct Math Calculations (e.g. 10+2) ───────────────────
        math_result = _try_safe_math_eval(prompt)
        if math_result is not None:
            state: AgentState = {
                "user_prompt": prompt,
                "company_id": self.company_id,
                "user_id": self.user_id,
                "currency": self.currency_code,
                "period_label": "all_time",
                "selected_agents": ["SupervisorAgent"],
                "executed_tools": ["compute_arithmetic_expression"],
                "evidence_cards": [],
                "suggested_actions": [],
                "citations": [{
                    "source": "Calculator Engine",
                    "detail": "Deterministic precision arithmetic computation."
                }],
                "final_response": math_result,
            }
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_agent_run(prompt, state, duration_ms)
            return {
                "message": state["final_response"],
                "agents_involved": state["selected_agents"],
                "tools_executed": state["executed_tools"],
                "evidence_cards": [],
                "suggested_actions": [],
                "citations": state["citations"],
            }

        # ── 0b. Handle Direct Greetings & Help Inquiries ───────────────────────
        if p_lower in self._GREETING_PHRASES or p_lower.strip("!?.").lower() in self._GREETING_PHRASES:
            greeting_msg = (
                "### 👋 Money Analysis AI Financial Controller\n\n"
                "I am your automated AI finance controller. Here is what I can do:\n\n"
                "- 📊 **Financial Metrics**: *\"What are our total expenses?\"*, *\"What is our net profit?\"*\n"
                "- 💡 **Cost Optimization**: *\"How can we reduce SaaS and cloud spending?\"*\n"
                "- 🔮 **What-If Simulations**: *\"What if Marketing spending decreases by 20%?\"*\n"
                "- 🛡️ **Anomaly Detection**: *\"Find suspicious transactions\"*\n"
                "- 📈 **Forecasting**: *\"Predict spending for the next 90 days\"*\n"
                "- 📄 **Document AI**: *\"What is our procurement policy?\"*\n"
                "- 🧮 **Calculations**: Direct math like *\"10+2\"* or *\"5000 * 12\"*."
            )
            state = {
                "user_prompt": prompt,
                "company_id": self.company_id,
                "user_id": self.user_id,
                "currency": self.currency_code,
                "period_label": "all_time",
                "selected_agents": ["SupervisorAgent"],
                "executed_tools": [],
                "evidence_cards": [],
                "suggested_actions": [],
                "citations": [{
                    "source": "Assistant System",
                    "detail": "Money Analysis Multi-Agent Finance Controller AI."
                }],
                "final_response": greeting_msg,
            }
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_agent_run(prompt, state, duration_ms)
            return {
                "message": state["final_response"],
                "agents_involved": state["selected_agents"],
                "tools_executed": state["executed_tools"],
                "evidence_cards": [],
                "suggested_actions": [],
                "citations": state["citations"],
            }

        # Resolve time period from prompt
        start_date, end_date, period_label = self._resolve_period(p_lower)

        state = {
            "user_prompt": prompt,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "currency": self.currency_code,
            "period_label": period_label,
            "selected_agents": [],
            "executed_tools": [],
            "evidence_cards": [],
            "suggested_actions": [],
            "citations": [],
            "final_response": "",
        }

        # ── 1. Intent Classification & Selective Routing ──────────────────────
        selected_agents = self._route_intent(p_lower)
        state["selected_agents"] = selected_agents
        is_metric_query = self._is_financial_metric_query(p_lower)
        is_optimization_query = self._is_optimization_query(p_lower)

        # ── 2. Execute Selected Specialised Agents ────────────────────────────

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
                    unused_seats = sum(
                        s.get("unused_licenses", 0)
                        for s in state["subscription_data"].get("subscriptions", [])
                    )
                    state["suggested_actions"].append({
                        "action": "REVIEW_UNUSED_SEATS",
                        "label": f"Review {unused_seats} Unused SaaS Seats",
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
                    target = self._extract_money_amount(prompt)
                    # Do NOT use a silent fallback target.
                    # generate_plan() handles None target gracefully.
                    if target is not None:
                        state["optimization_plan"] = opt_agent.generate_plan(
                            target_savings_amount=target
                        )
                    else:
                        state["optimization_plan"] = opt_agent.generate_plan()
                    state["executed_tools"].append("synthesize_optimization_plan")
                    state["citations"].append({
                        "source": "Cost Optimisation Planner",
                        "detail": "Risk-stratified action plan derived from multi-agent analysis.",
                    })
                except Exception as exc:
                    logger.warning("CostOptimizationAgent failed: %s", exc)

        if "WhatIfAgent" in selected_agents:
            try:
                adjustments = self._build_what_if_adjustments(prompt)
                if not adjustments:
                    state["what_if_results"] = {
                        "status": "INSUFFICIENT_INPUT",
                        "message": (
                            "Please specify a department and a percentage to simulate, for example: "
                            "'What if Marketing spending decreases by 20%?'"
                        ),
                    }
                else:
                    wi_agent = WhatIfSimulationAgent(self.db, self.company_id)
                    state["what_if_results"] = wi_agent.simulate(
                        department_spend_adjustments=adjustments
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

        # TransactionAgent – run when in selected list, with optional date filter
        if "TransactionAgent" in selected_agents:
            try:
                tx_agent = TransactionAnalysisAgent(self.db, self.company_id)
                state["transaction_data"] = tx_agent.analyze(
                    start_date=start_date,
                    end_date=end_date,
                    department_name=self._extract_department(prompt),
                )
                state["executed_tools"].append("fetch_transaction_trends")
                state["citations"].append({
                    "source": "Financial Ledgers",
                    "detail": "Live PostgreSQL company transaction records (company-isolated).",
                })
                td = state["transaction_data"]
                sym = self.currency_sym
                period_str = period_label.replace("_", " ")
                state["evidence_cards"].append({
                    "title": f"Transaction Summary ({period_str})",
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

        # ── 3. Guard: metric query with failed TransactionAgent ───────────────
        if is_metric_query and not state.get("transaction_data"):
            final_text = (
                "I couldn't retrieve the financial ledger required to calculate "
                "this metric. Please try again after the transaction service is available."
            )
            state["final_response"] = final_text
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_agent_run(prompt, state, duration_ms)
            return {
                "message": state["final_response"],
                "agents_involved": state["selected_agents"],
                "tools_executed": state["executed_tools"],
                "evidence_cards": state["evidence_cards"],
                "suggested_actions": [],
                "citations": state["citations"],
            }

        # ── 4. Generate Response ──────────────────────────────────────────────
        if is_metric_query and state.get("transaction_data"):
            # Financial metrics are deterministic – never call Gemini for the authoritative number.
            final_text = self._build_direct_response(state, p_lower, period_label)
        else:
            system_instruction = self._build_system_instruction(
                is_metric_query=is_metric_query,
                is_optimization_query=is_optimization_query,
                state=state,
            )
            context_summary = self._build_context_summary(state)
            try:
                final_text = await llm_client.generate_response(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    context_data=context_summary,
                )
            except Exception as exc:
                logger.error("LLM response generation failed: %s", exc)
                final_text = self._build_direct_response(state, p_lower, period_label)

        state["final_response"] = final_text

        # ── 5. Log Execution ──────────────────────────────────────────────────
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

    # ── Routing ───────────────────────────────────────────────────────────────

    def _route_intent(self, prompt: str) -> List[str]:
        """
        Route user requests to the minimum required specialised agents.

        Priority order (first match wins):
        1. What-If   – must come before optimization: "what if we reduce…" contains "reduce"
        2. Optimization – must come before metric: "how can we reduce total expenses?" contains "total expenses"
        3. Direct financial metrics
        4. Anomaly detection
        5. Forecasting
        6. Subscription analysis
        7. Vendor analysis
        8. Budget analysis
        9. Finance document / RAG
        10. Safe default → TransactionAgent
        """
        agents = ["SupervisorAgent"]

        # 1. What-if (before optimization – "reduce" is in both keyword sets)
        if any(w in prompt for w in self._WHATIF_KEYWORDS):
            agents.append("WhatIfAgent")
            return list(dict.fromkeys(agents))

        # 2. Cost optimization (before metric – "total expenses" can appear in optimization prompts)
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

        # 3. Direct financial metrics
        if self._is_financial_metric_query(prompt):
            agents.append("TransactionAgent")
            return list(dict.fromkeys(agents))

        # 4. Anomaly detection
        if any(w in prompt for w in self._ANOMALY_KEYWORDS):
            agents.extend(["AnomalyAgent", "TransactionAgent"])
            return list(dict.fromkeys(agents))

        # 5. Forecasting
        if any(w in prompt for w in self._FORECAST_KEYWORDS):
            agents.append("ForecastingAgent")
            return list(dict.fromkeys(agents))

        # 6. Subscription analysis
        if any(w in prompt for w in self._SUBSCRIPTION_KEYWORDS):
            agents.append("SubscriptionAgent")
            return list(dict.fromkeys(agents))

        # 7. Vendor analysis
        if any(w in prompt for w in self._VENDOR_KEYWORDS):
            agents.append("VendorAgent")
            return list(dict.fromkeys(agents))

        # 8. Budget analysis
        if any(w in prompt for w in self._BUDGET_KEYWORDS):
            agents.extend(["BudgetAgent", "TransactionAgent"])
            return list(dict.fromkeys(agents))

        # 9. Finance document / RAG
        if any(w in prompt for w in self._RAG_KEYWORDS):
            agents.append("RAGAgent")
            return list(dict.fromkeys(agents))

        # 10. General / Safe default
        financial_general_keywords = [
            "overview", "summary", "transaction", "ledger", "balance",
            "spend", "expense", "revenue", "income", "finance", "money",
            "financial", "status", "dashboard", "report", "burn"
        ]
        if any(w in prompt for w in financial_general_keywords):
            agents.append("TransactionAgent")
        return list(dict.fromkeys(agents))

    def _is_financial_metric_query(self, prompt_lower: str) -> bool:
        return any(phrase in prompt_lower for phrase in self._FINANCIAL_METRIC_PHRASES)

    def _is_optimization_query(self, prompt_lower: str) -> bool:
        return any(kw in prompt_lower for kw in self._OPTIMIZATION_KEYWORDS)

    # ── Parsers ───────────────────────────────────────────────────────────────

    def _extract_money_amount(self, prompt: str) -> Optional[float]:
        """
        Extract a monetary target from the prompt.
        Supports ₹, $, €, £, k, lakh, million.

        Percentages (e.g. 15%) are explicitly NOT treated as monetary values.
        Numbers that are part of a percentage expression (NUMBER%) return None.
        """
        cleaned = re.sub(r"[0-9]+(?:\.[0-9]+)?\s*%", " ", prompt)

        pattern = re.compile(
            r"[₹$€£]\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(k|lakh|l|million|m)?|"
            r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(k|lakh|l|million|m)",
            re.IGNORECASE,
        )
        match = pattern.search(cleaned)
        if not match:
            return None

        try:
            if match.group(1) is not None:
                raw = match.group(1).replace(",", "")
                multiplier = (match.group(2) or "").lower()
            else:
                raw = match.group(3).replace(",", "")
                multiplier = (match.group(4) or "").lower()

            value = float(raw)
            if multiplier == "k":
                value *= 1_000
            elif multiplier in {"lakh", "l"}:
                value *= 100_000
            elif multiplier in {"million", "m"}:
                value *= 1_000_000
            return value
        except (ValueError, ArithmeticError) as exc:
            logger.debug("Could not parse money amount: %s", exc)
            return None

    def _extract_percentage(self, prompt: str) -> Optional[float]:
        """
        Extract a percentage and return as decimal (e.g. 15% → 0.15).
        Returns None if the value is outside 0–100.
        """
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", prompt, re.IGNORECASE)
        if not match:
            return None
        try:
            value = float(match.group(1))
            if value < 0 or value > 100:
                return None
            return value / 100.0
        except (ValueError, ArithmeticError):
            return None

    def _extract_department(self, prompt: str) -> Optional[str]:
        """
        Resolve a department mentioned in the prompt against departments
        belonging to the current company (tenant-safe).
        """
        departments = (
            self.db.query(Department)
            .filter(Department.company_id == self.company_id)
            .all()
        )
        p_lower = prompt.lower()
        for dept in departments:
            if dept.name.lower() in p_lower:
                return dept.name
        return None

    def _build_what_if_adjustments(self, prompt: str) -> Dict[str, float]:
        """
        Build department_spend_adjustments dict from the user's natural-language prompt.
        Returns {} when department or percentage cannot be resolved.
        """
        department = self._extract_department(prompt)
        percentage = self._extract_percentage(prompt)

        if not department or percentage is None:
            return {}

        p_lower = prompt.lower()
        increase_words = ["increase", "raise", "grow", "higher"]
        decrease_words = ["decrease", "reduce", "cut", "lower", "drop"]

        if any(word in p_lower for word in increase_words):
            return {department: percentage}
        if any(word in p_lower for word in decrease_words):
            return {department: -percentage}
        return {}

    def _resolve_period(
        self, prompt_lower: str
    ) -> Tuple[Optional[date], Optional[date], str]:
        """
        Detect time-period references in the prompt.
        Returns (start_date, end_date, label).
        """
        today = date.today()

        if "this month" in prompt_lower:
            return today.replace(day=1), today, "this_month"
        if "today" in prompt_lower:
            return today, today, "today"
        if "this year" in prompt_lower:
            return date(today.year, 1, 1), today, "this_year"
        if "last 30 days" in prompt_lower:
            return today - timedelta(days=30), today, "last_30_days"
        if "last month" in prompt_lower:
            first_of_this = today.replace(day=1)
            last_month_end = first_of_this - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start, last_month_end, "last_month"

        return None, None, "all_time"

    # ── Response builders ─────────────────────────────────────────────────────

    def _build_system_instruction(
        self,
        is_metric_query: bool,
        is_optimization_query: bool,
        state: AgentState,
    ) -> str:
        sym = self.currency_sym
        base = (
            "You are the Money Analysis Finance Controller AI. "
            "When answering questions about company financial metrics or records, "
            "you must strictly use figures explicitly provided in the context data. "
            "For general financial, accounting, business, technology, or conceptual questions, "
            "provide a clear, informative, and professional answer. "
            f"Use {self.currency_code} ({sym}) as the default currency symbol when discussing monetary values.\n\n"
        )
        if is_optimization_query:
            return (
                base
                + "The user is asking for cost optimisation advice. "
                + "Provide actionable recommendations based only on the data provided in context. "
                + "Do not fabricate savings figures not present in the context."
            )
        return base + "Answer the user's question accurately, concisely, and helpfully."

    def _build_context_summary(self, state: AgentState) -> Dict[str, Any]:
        """Build the context dict passed to the LLM – safe, no DB objects or secrets."""
        ctx: Dict[str, Any] = {
            "selected_agents": state["selected_agents"],
            "currency_code": self.currency_code,
            "currency_symbol": self.currency_sym,
            "period": state.get("period_label", "all_time"),
        }
        if state.get("transaction_data"):
            td = state["transaction_data"]
            ctx["transaction_summary"] = {
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
            ctx["budget_summary"] = {
                "total_allocated": bd.get("total_allocated"),
                "total_spent": bd.get("total_spent"),
                "overall_usage_pct": bd.get("overall_usage_pct"),
                "critical_count": bd.get("critical_count"),
                "at_risk_departments": bd.get("at_risk_departments", [])[:5],
            }
        if state.get("anomaly_data"):
            ctx["anomaly_count"] = len(state["anomaly_data"])
            ctx["top_anomalies"] = state["anomaly_data"][:3]
        if state.get("vendor_data"):
            vd = state["vendor_data"]
            ctx["vendor_summary"] = {
                "vendor_count": vd.get("vendor_count"),
                "top_vendors_by_spend": vd.get("vendors", [])[:5],
                "negotiation_targets": vd.get("negotiation_targets", [])[:3],
            }
        if state.get("subscription_data"):
            sd = state["subscription_data"]
            ctx["subscription_summary"] = {
                "total_monthly_spend": sd.get("total_monthly_spend"),
                "potential_monthly_savings": sd.get("potential_monthly_savings"),
                "wasted_subscriptions_count": sd.get("wasted_subscriptions_count"),
                "subscriptions_count": sd.get("subscriptions_count"),
                "upcoming_renewals": sd.get("upcoming_renewals", [])[:3],
            }
        if state.get("forecast_data"):
            ctx["forecast_data"] = state["forecast_data"]
        if state.get("savings_data"):
            sv = state["savings_data"]
            ctx["savings_summary"] = {
                "total_potential_monthly": sv.get("total_potential_monthly"),
                "total_potential_annual": sv.get("total_potential_annual"),
                "opportunities_count": sv.get("opportunities_count"),
                "top_opportunities": sv.get("opportunities", [])[:4],
            }
        if state.get("optimization_plan"):
            ctx["optimization_plan"] = state["optimization_plan"]
        if state.get("what_if_results"):
            ctx["what_if_results"] = state["what_if_results"]
        if state.get("rag_results"):
            ctx["rag_results"] = state["rag_results"]
        return ctx

    def _build_direct_response(
        self, state: AgentState, prompt_lower: str, period_label: str = "all_time"
    ) -> str:
        """
        Build a deterministic response from verified agent data.
        Used for financial metric queries and as LLM fallback.
        Never fabricates financial figures.
        """
        sym = self.currency_sym
        period_str = period_label.replace("_", " ")
        suffix = f" ({period_str})" if period_label != "all_time" else ""
        dept = self._extract_department(state.get("user_prompt", ""))
        dept_prefix = f"{dept} spending" if dept else "your expenses"

        td = state.get("transaction_data")
        if td is not None:
            total_exp = td.get("total_expenses", 0)
            total_rev = td.get("total_revenue", 0)
            net = td.get("net_profit", 0)
            count = td.get("total_transactions", 0)

            if any(ph in prompt_lower for ph in [
                "total expense", "total spending", "how much did we spend",
                "how much have we spent", "how much did we pay", "overall expenses",
                "total cost",
            ]):
                if dept:
                    return (
                        f"{dept} total expenses{suffix} are **{sym}{total_exp:,.2f}**"
                        f" across {count} transactions."
                    )
                return (
                    f"Your total expenses{suffix} are **{sym}{total_exp:,.2f}**"
                    f" across {count} transactions.\n\n"
                    f"- Total Revenue: {sym}{total_rev:,.2f}\n"
                    f"- Net Profit: {sym}{net:,.2f}"
                )

            if "total revenue" in prompt_lower or "total income" in prompt_lower:
                return (
                    f"Your total revenue{suffix} is **{sym}{total_rev:,.2f}**.\n\n"
                    f"- Total Expenses: {sym}{total_exp:,.2f}\n"
                    f"- Net Profit: {sym}{net:,.2f}"
                )

            if "net profit" in prompt_lower or "net loss" in prompt_lower or "gross profit" in prompt_lower:
                direction = "profit" if net >= 0 else "loss"
                return (
                    f"Your net {direction}{suffix} is **{sym}{abs(net):,.2f}**.\n\n"
                    f"- Total Revenue: {sym}{total_rev:,.2f}\n"
                    f"- Total Expenses: {sym}{total_exp:,.2f}"
                )

            # Generic financial summary
            return (
                f"### Financial Summary{suffix}\n\n"
                f"- **Total Expenses**: {sym}{total_exp:,.2f}\n"
                f"- **Total Revenue**: {sym}{total_rev:,.2f}\n"
                f"- **Net Profit**: {sym}{net:,.2f}\n"
                f"- **Total Transactions**: {count}\n"
                f"- **Monthly Burn Rate**: {sym}{td.get('monthly_burn_rate', 0):,.2f}"
            )

        if state.get("savings_data"):
            sv = state["savings_data"]
            m = sv.get("total_potential_monthly", 0)
            if m and m > 0:
                return (
                    f"Potential monthly savings: {sym}{m:,.2f} "
                    f"({sym}{sv.get('total_potential_annual', 0):,.2f} annually)."
                )

        return (
            "I couldn't calculate that value from the available financial records. "
            "Please check the dashboard for real-time metrics."
        )

    # ── Logging ───────────────────────────────────────────────────────────────

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
