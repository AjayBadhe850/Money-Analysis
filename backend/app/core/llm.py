import logging
import json
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM provider abstraction supporting Gemini, OpenAI, and a deterministic offline mock.
    Ensures safe, production-grade fallback and never hallucinates financial numbers.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL

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
                return await self._call_gemini(prompt, system_instruction, temperature)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Falling back to internal financial intelligence engine.")

        # If OpenAI key provided and selected
        if (self.provider == "openai" or self.openai_key) and self.openai_key:
            try:
                return await self._call_openai(prompt, system_instruction, temperature)
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}. Falling back to internal financial intelligence engine.")

        # Deterministic financial intelligence fallback
        return self._generate_intelligent_fallback(prompt, system_instruction, context_data)

    async def _call_gemini(self, prompt: str, system_instruction: Optional[str], temperature: float) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        contents = []
        if system_instruction:
            contents.append({"role": "user", "parts": [{"text": f"System Context:\n{system_instruction}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will act strictly according to these instructions and financial facts."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={
                    "contents": contents,
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048}
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(self, prompt: str, system_instruction: Optional[str], temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

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
        p_lower = prompt.lower()
        sym = ""
        if context_data:
            code = context_data.get("currency_code", "USD")
            sym = context_data.get("currency_symbol") or {
                "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£"
            }.get(code.upper(), code)

        # ── Financial metric response (use verified numbers from TransactionAgent) ──
        if context_data and context_data.get("transaction_summary"):
            ts = context_data["transaction_summary"]
            total_exp = ts.get("total_expenses", 0)
            total_rev = ts.get("total_revenue", 0)
            net = ts.get("net_profit", 0)
            tx_count = ts.get("total_transactions", 0)

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
                f"- **Monthly Burn Rate**: {sym}{ts.get('monthly_burn_rate', 0):,.2f}"
            )

        # ── Savings / optimisation response (use verified savings summary) ──
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

        # ── Anomaly response ──
        if context_data and context_data.get("anomaly_count"):
            return (
                f"### Anomaly Detection Report\n\n"
                f"The Isolation Forest scan identified **{context_data['anomaly_count']}** "
                f"statistical anomalies in company transaction records. "
                f"Review flagged items in the Anomaly dashboard for details."
            )

        # ── Forecast response ──
        if context_data and context_data.get("forecast_data"):
            fd = context_data["forecast_data"]
            total_proj = fd.get("total_projected_spend", 0)
            horizon = fd.get("horizon_days", 90)
            return (
                f"### Financial Forecast\n\n"
                f"Projected spend over the next **{horizon} days**: **{sym}{total_proj:,.2f}**.\n"
                f"This forecast is based on historical expenditure trends."
            )

        # ── Generic fallback – no data available ──
        return (
            "### Money Analysis Financial Controller\n\n"
            f"I reviewed available financial data for your query: *\"{prompt}\"*. "
            "No verified financial figures are available for the selected time period. "
            "Please ensure transactions are recorded and try again, "
            "or use the Dashboard for real-time metrics."
        )


llm_client = LLMClient()
