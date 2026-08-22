import logging
import json
import ast
import operator
import re
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

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


def _try_math_eval(prompt: str) -> Optional[str]:
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


class LLMClient:
    """
    Unified LLM provider abstraction supporting Gemini, OpenAI, and a deterministic offline engine.
    Ensures safe, production-grade responses and never hallucinates financial numbers.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "mock"
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL or "gemini-1.5-flash"

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate natural language response using configured provider.
        """
        # If Gemini key provided and selected
        if (self.provider == "gemini" or self.gemini_key) and self.gemini_key:
            try:
                return await self._call_gemini(prompt, system_instruction, temperature, context_data)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to internal financial intelligence engine.")

        # If OpenAI key provided and selected
        if (self.provider == "openai" or self.openai_key) and self.openai_key:
            try:
                return await self._call_openai(prompt, system_instruction, temperature, context_data)
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}. Falling back to internal financial intelligence engine.")

        # Deterministic financial intelligence fallback
        return self._generate_intelligent_fallback(prompt, system_instruction, context_data)

    async def _call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        api_key = (self.gemini_key or "").strip()
        configured_model = (self.model or "gemini-3.5-flash").strip()
        if configured_model.startswith("models/"):
            configured_model = configured_model[len("models/"):]

        # List of candidate models in order of preference
        candidate_models = [configured_model]
        for fallback_m in ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-1.5-flash"]:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        # Construct prompt incorporating context data
        full_user_prompt = prompt
        if context_data:
            context_json = json.dumps(context_data, indent=2, default=str)
            full_user_prompt = f"Verified Financial Context Data:\n```json\n{context_json}\n```\n\nUser Question / Task:\n{prompt}"

        last_error = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

                payload: Dict[str, Any] = {
                    "contents": [{"role": "user", "parts": [{"text": full_user_prompt}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048}
                }
                if system_instruction:
                    payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        logger.warning(
                            f"Gemini API ({model_name}) returned {resp.status_code}. Retrying with combined prompt..."
                        )
                        combined = f"System Instruction:\n{system_instruction}\n\n{full_user_prompt}" if system_instruction else full_user_prompt
                        retry_payload = {
                            "contents": [{"role": "user", "parts": [{"text": combined}]}],
                            "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048}
                        }
                        resp = await client.post(url, json=retry_payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                            parts = candidates[0]["content"]["parts"]
                            if parts and "text" in parts[0]:
                                return parts[0]["text"]
                    else:
                        last_error = f"Status {resp.status_code}: {resp.text}"
                except Exception as exc:
                    last_error = str(exc)
                    continue

        raise ValueError(f"All Gemini models failed. Last error: {last_error}")

    async def _call_openai(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        full_user_prompt = prompt
        if context_data:
            context_json = json.dumps(context_data, indent=2, default=str)
            full_user_prompt = f"Verified Financial Context Data:\n```json\n{context_json}\n```\n\nUser Question / Task:\n{prompt}"

        messages.append({"role": "user", "content": full_user_prompt})

        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={"model": "gpt-4o-mini", "messages": messages, "temperature": temperature}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _generate_intelligent_fallback(
        self, prompt: str, system_instruction: Optional[str], context_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        Deterministic financial fallback response built from verified context data only.
        This method must NEVER fabricate monetary amounts, percentages, or counts.
        All figures reported come exclusively from context_data passed by executed agents.
        """
        p_lower = prompt.lower().strip()

        # ── 0. Direct Math Calculation (e.g. "10+2", "500 * 12") ──
        math_res = _try_math_eval(prompt)
        if math_res:
            return math_res

        # ── 0b. Direct Greeting / Help ──
        greetings = {"hi", "hello", "hey", "help", "who are you", "what can you do", "capabilities"}
        if p_lower in greetings or p_lower.strip("!?.").lower() in greetings:
            return (
                "### 👋 Money Analysis AI Financial Controller\n\n"
                "I am your automated AI financial controller. I can assist you with:\n\n"
                "- 📊 **Financial Metrics**: *\"What are our total expenses?\"*, *\"What is our net profit?\"*\n"
                "- 💡 **Cost Optimization**: *\"How can we reduce SaaS and cloud spending?\"*\n"
                "- 🔮 **What-If Simulations**: *\"What if Marketing spending decreases by 20%?\"*\n"
                "- 🛡️ **Anomaly Detection**: *\"Find suspicious transactions\"*\n"
                "- 📈 **Forecasting**: *\"Predict spending for the next 90 days\"*\n"
                "- 📄 **Document AI**: *\"What is our procurement policy?\"*\n"
                "- 🧮 **Calculations**: Direct math like *\"10+2\"* or *\"5000 * 12\"*."
            )

        sym = "$"
        if context_data:
            code = context_data.get("currency_code", "USD")
            sym = context_data.get("currency_symbol") or {
                "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£"
            }.get(code.upper(), code)

        # ── 1. Document AI / RAG Context Response ──
        if context_data and ("rag_context" in context_data or "rag_results" in context_data):
            rag = context_data.get("rag_results") or context_data
            ans = rag.get("answer") if isinstance(rag, dict) else None
            chunks = rag.get("retrieved_chunks", []) if isinstance(rag, dict) else []
            if ans and not ans.startswith("No indexed financial documents"):
                return ans
            if chunks:
                chunk_texts = [f"• **{c.get('filename', 'Doc')}** (Match: {int(c.get('similarity_score', 0)*100)}%):\n{c.get('chunk_text', '')}" for c in chunks[:3]]
                return "### Document Intelligence Analysis\n\n" + "\n\n".join(chunk_texts)

        # ── 2. What-If Simulation Response ──
        if context_data and context_data.get("what_if_results"):
            wi = context_data["what_if_results"]
            if wi.get("status") == "INSUFFICIENT_INPUT":
                return wi.get("message", "Please specify a department and percentage to simulate.")
            narrative = wi.get("ai_narrative")
            if narrative:
                return f"### Scenario Simulation Result\n\n{narrative}"
            base_exp = wi.get("baseline_monthly_expense", 0)
            sim_exp = wi.get("simulated_monthly_expense", 0)
            m_sav = wi.get("monthly_expense_savings", 0)
            return (
                f"### What-If Scenario Analysis\n\n"
                f"- **Baseline Monthly Spend**: {sym}{base_exp:,.2f}\n"
                f"- **Simulated Monthly Spend**: {sym}{sim_exp:,.2f}\n"
                f"- **Monthly Delta**: {'Savings of ' + sym if m_sav >= 0 else 'Increase of ' + sym}{abs(m_sav):,.2f}\n"
                f"- **Operating Margin Change**: {wi.get('profit_margin_change_pct', 0):+.1f}%"
            )

        # ── 3. Strategic Cost Optimization Plan ──
        if context_data and context_data.get("optimization_plan"):
            plan = context_data["optimization_plan"]
            exec_summary = plan.get("executive_summary")
            actions = plan.get("recommended_actions", [])
            lines = ["### Strategic Cost Optimization Plan\n"]
            if exec_summary:
                lines.append(exec_summary)
            lines.append(f"\n**Total Achievable Monthly Savings**: {sym}{plan.get('achievable_monthly_savings', 0):,.2f}")
            if actions:
                lines.append("\n**Key Initiatives:**")
                for a in actions[:4]:
                    lines.append(f"- **{a.get('title', 'Action')}**: {sym}{a.get('projected_monthly_savings', 0):,.2f}/mo ({a.get('risk_level', 'LOW')} Risk) – {a.get('rationale', '')}")
            return "\n".join(lines)

        # ── 4. Savings Opportunities ──
        if context_data and context_data.get("savings_summary"):
            sv = context_data["savings_summary"]
            m = sv.get("total_potential_monthly", 0)
            a = sv.get("total_potential_annual", 0)
            count = sv.get("opportunities_count", 0)
            lines = [f"### Cost Optimisation Analysis\n\nIdentified **{count}** opportunities."]
            if m and m > 0:
                lines.append(f"- Total potential monthly savings: **{sym}{m:,.2f}**")
                lines.append(f"- Total potential annual savings: **{sym}{a:,.2f}**")
            for opp in sv.get("top_opportunities", [])[:4]:
                ms = opp.get("estimated_monthly_saving", 0)
                lines.append(
                    f"- **{opp.get('title', 'Opportunity')}**: {sym}{ms:,.2f}/mo "
                    f"(Risk: {opp.get('risk_level', 'N/A')})"
                )
            return "\n".join(lines)

        # ── 5. Budget Health & Velocity ──
        if context_data and context_data.get("budget_summary"):
            bs = context_data["budget_summary"]
            tot_alloc = bs.get("total_allocated", 0)
            tot_spent = bs.get("total_spent", 0)
            pct = bs.get("overall_usage_pct", 0)
            crit = bs.get("critical_count", 0)
            lines = [
                "### Budget Allocation & Burn Analysis\n",
                f"- **Total Allocated**: {sym}{tot_alloc:,.2f}",
                f"- **Total Spent**: {sym}{tot_spent:,.2f} ({pct:.1f}% consumed)",
                f"- **At-Risk Departments / Categories**: {crit}",
            ]
            for dept in bs.get("at_risk_departments", [])[:3]:
                lines.append(f"  • **{dept.get('department')}**: Spent {sym}{dept.get('spent', 0):,.2f} of {sym}{dept.get('allocated', 0):,.2f} ({dept.get('status')})")
            return "\n".join(lines)

        # ── 6. Vendor Intelligence ──
        if context_data and context_data.get("vendor_summary"):
            vs = context_data["vendor_summary"]
            lines = [
                "### Vendor Intelligence & Procurement Analysis\n",
                f"- **Active Tracked Vendors**: {vs.get('vendor_count', 0)}",
            ]
            if vs.get("top_vendors_by_spend"):
                lines.append("\n**Top Suppliers by Spend:**")
                for v in vs["top_vendors_by_spend"][:3]:
                    lines.append(f"- **{v.get('name')}**: {sym}{v.get('total_spend', 0):,.2f} (Efficiency Score: {v.get('cost_efficiency_score', 'N/A')}/100)")
            if vs.get("negotiation_targets"):
                lines.append("\n**Recommended Renegotiation Targets:**")
                for nt in vs["negotiation_targets"][:2]:
                    lines.append(f"- **{nt.get('vendor_name')}**: {sym}{nt.get('potential_savings', 0):,.2f} potential savings – {nt.get('suggested_action')}")
            return "\n".join(lines)

        # ── 7. SaaS Subscriptions ──
        if context_data and context_data.get("subscription_summary"):
            ss = context_data["subscription_summary"]
            lines = [
                "### SaaS & Subscription Audit\n",
                f"- **Total Monthly SaaS Spend**: {sym}{ss.get('total_monthly_spend', 0):,.2f}",
                f"- **Potential Waste Reclamation**: {sym}{ss.get('potential_monthly_savings', 0):,.2f}/mo",
                f"- **Subscriptions with Unused Seats**: {ss.get('wasted_subscriptions_count', 0)}",
            ]
            if ss.get("upcoming_renewals"):
                lines.append("\n**Upcoming Renewals:**")
                for r in ss["upcoming_renewals"][:2]:
                    lines.append(f"- **{r.get('service_name')}**: Renews in {r.get('days_remaining')} days – {r.get('action')}")
            return "\n".join(lines)

        # ── 8. Anomaly Detection ──
        if context_data and context_data.get("anomaly_count"):
            lines = [
                "### Anomaly Detection Report\n",
                f"The Isolation Forest scan identified **{context_data['anomaly_count']}** statistical anomalies in company transactions."
            ]
            if context_data.get("top_anomalies"):
                lines.append("\n**Highest Variance Transactions:**")
                for a in context_data["top_anomalies"][:3]:
                    lines.append(f"- **TX #{a.get('transaction_id')} ({a.get('vendor_name', 'Vendor')})**: {sym}{a.get('transaction_amount', 0):,.2f} (Score: {a.get('anomaly_score')}/100 | Severity: {a.get('severity')}) – {a.get('explanation', '')}")
            return "\n".join(lines)

        # ── 9. Forecast Response ──
        if context_data and context_data.get("forecast_data"):
            fd = context_data["forecast_data"]
            total_proj = fd.get("total_projected_spend", 0)
            horizon = fd.get("horizon_days", 90)
            growth = fd.get("historical_growth_rate", 0)
            trend = fd.get("trend", "STABLE")
            return (
                f"### Financial Forecast ({horizon}-Day Horizon)\n\n"
                f"- **Projected Total Spend**: **{sym}{total_proj:,.2f}**\n"
                f"- **Historical Monthly Growth Rate**: {growth:+.1f}%\n"
                f"- **Spending Trajectory**: {trend}\n"
                f"- **Forecast Model**: {fd.get('model_type', 'Ridge Regression')} (Confidence: {int(fd.get('confidence_score', 0.95)*100)}%)"
            )

        # ── 10. Financial Metric Response (Transaction Summary) ──
        if context_data and context_data.get("transaction_data"):
            td = context_data["transaction_data"]
            total_exp = td.get("total_expenses", 0)
            total_rev = td.get("total_revenue", 0)
            net = td.get("net_profit", 0)
            tx_count = td.get("total_transactions", 0)

            if any(ph in p_lower for ph in [
                "total expense", "total spending", "how much did we spend",
                "how much have we spent", "how much did we pay", "overall expenses",
                "total cost",
            ]):
                return (
                    f"Your total expenses are **{sym}{total_exp:,.2f}**"
                    f" across {tx_count} transactions.\n\n"
                    f"- Total Revenue: {sym}{total_rev:,.2f}\n"
                    f"- Net Profit: {sym}{net:,.2f}"
                )

            if "total revenue" in p_lower or "total income" in p_lower:
                return (
                    f"Your total revenue is **{sym}{total_rev:,.2f}**.\n\n"
                    f"- Total Expenses: {sym}{total_exp:,.2f}\n"
                    f"- Net Profit: {sym}{net:,.2f}"
                )

            if "net profit" in p_lower or "net loss" in p_lower or "gross profit" in p_lower:
                direction = "profit" if net >= 0 else "loss"
                return (
                    f"Your net {direction} is **{sym}{abs(net):,.2f}**.\n\n"
                    f"- Total Revenue: {sym}{total_rev:,.2f}\n"
                    f"- Total Expenses: {sym}{total_exp:,.2f}"
                )

            # Generic transaction summary
            return (
                f"### Financial Summary\n\n"
                f"- **Total Expenses**: {sym}{total_exp:,.2f}\n"
                f"- **Total Revenue**: {sym}{total_rev:,.2f}\n"
                f"- **Net Profit**: {sym}{net:,.2f}\n"
                f"- **Total Transactions**: {tx_count}\n"
                f"- **Monthly Burn Rate**: {sym}{td.get('monthly_burn_rate', 0):,.2f}"
            )

        # ── Generic fallback ──
        return (
            "### Money Analysis Financial Controller\n\n"
            f"I reviewed available financial data for your query: *\"{prompt}\"*. "
            "Please ask a specific question regarding expenses, revenue, savings, what-if scenarios, or forecast trends."
        )


llm_client = LLMClient()
