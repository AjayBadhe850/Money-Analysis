"""
Regression tests for multi-agent intent routing and financial accuracy.

These tests verify:
1. _route_intent returns the correct agents for each intent category
2. Financial metric calculations are numerically exact (using deterministic fixtures)
3. Tenant isolation: Company A data cannot be accessed by Company B queries
4. AI response contract: response dict always contains required keys
5. LLM/Gemini calls are mocked – tests never hit a live API
"""

import asyncio
from decimal import Decimal
from datetime import date
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.supervisor_agent import SupervisorAgent, _currency_symbol
from app.agents.transaction_agent import TransactionAnalysisAgent
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.subscription import Subscription, SubscriptionStatus
from app.auth.hashing import hash_password


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_supervisor(db_session, company) -> SupervisorAgent:
    return SupervisorAgent(db=db_session, company_id=company.id)


def _route(db_session, company, prompt: str):
    """Return the list of agents routed for a given prompt (lowercase)."""
    sv = _make_supervisor(db_session, company)
    return sv._route_intent(prompt.lower())


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ROUTING TESTS – FINANCIAL METRIC
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoutingFinancialMetric:

    def test_total_expenses_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "What are our total expenses?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents
        assert "CostOptimizationAgent" not in agents
        assert "BudgetAgent" not in agents
        assert "SubscriptionAgent" not in agents
        assert "VendorAgent" not in agents
        assert "ForecastingAgent" not in agents
        assert "AnomalyAgent" not in agents

    def test_total_revenue_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "What is our total revenue?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents
        assert "CostOptimizationAgent" not in agents

    def test_net_profit_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "What is our net profit?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_how_much_did_we_spend_routes_to_transaction(self, db_session, test_company):
        agents = _route(db_session, test_company, "How much did we spend this month?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_department_spending_routes_to_transaction(self, db_session, test_company):
        agents = _route(db_session, test_company, "How much did Marketing spend this month?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_total_expense_singular_routes_to_transaction(self, db_session, test_company):
        agents = _route(db_session, test_company, "What is our total expense?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_how_much_have_we_spent_routes_to_transaction(self, db_session, test_company):
        agents = _route(db_session, test_company, "How much have we spent?")
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ROUTING TESTS – COST OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoutingCostOptimization:

    def test_reduce_expenses_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "How can we reduce our expenses?")
        assert "SavingsAgent" in agents
        assert "CostOptimizationAgent" in agents

    def test_find_savings_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "Find cost-saving opportunities.")
        assert "SavingsAgent" in agents
        assert "CostOptimizationAgent" in agents

    def test_save_money_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "How can we save money?")
        assert "SavingsAgent" in agents

    def test_optimize_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "Optimize our monthly costs.")
        assert "CostOptimizationAgent" in agents

    def test_cut_costs_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "Which expenses should we cut?")
        assert "SavingsAgent" in agents


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ROUTING TESTS – OTHER INTENTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoutingOtherIntents:

    def test_anomaly_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "Find suspicious transactions.")
        assert "AnomalyAgent" in agents
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_forecast_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "Predict next month's expenses.")
        assert "ForecastingAgent" in agents
        assert "SavingsAgent" not in agents

    def test_forecast_next_quarter(self, db_session, test_company):
        agents = _route(db_session, test_company, "Forecast next quarter spending.")
        assert "ForecastingAgent" in agents

    def test_budget_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "Are we exceeding our budget?")
        assert "BudgetAgent" in agents
        assert "SavingsAgent" not in agents

    def test_subscription_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "Which subscriptions are unused?")
        assert "SubscriptionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_vendor_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "Which vendor costs us the most?")
        assert "VendorAgent" in agents
        assert "SavingsAgent" not in agents

    def test_what_if_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "What if we reduce Marketing spending by 15%?")
        assert "WhatIfAgent" in agents

    def test_default_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "Give me a finance overview.")
        assert "TransactionAgent" in agents
        # Default must NOT drag in optimisation agents
        assert "SavingsAgent" not in agents
        assert "CostOptimizationAgent" not in agents

    def test_supervisor_always_present(self, db_session, test_company):
        for prompt in [
            "total expenses",
            "reduce costs",
            "forecast spending",
            "budget status",
        ]:
            agents = _route(db_session, test_company, prompt)
            assert "SupervisorAgent" in agents, f"SupervisorAgent missing for '{prompt}'"

    def test_no_duplicate_agents_in_route(self, db_session, test_company):
        agents = _route(db_session, test_company, "reduce costs and save money")
        assert len(agents) == len(set(agents)), "Duplicate agents detected in routing result"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FINANCIAL ACCURACY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancialAccuracy:
    """
    These tests use a controlled fixture (separate from conftest) with
    exact, known transaction amounts to verify calculation correctness.
    """

    @pytest.fixture
    def precise_db(self, db_session, test_company):
        """Add transactions with exact known amounts for deterministic assertion."""
        dept = db_session.query(Department).filter(Department.company_id == test_company.id).first()
        cat = db_session.query(Category).filter(Category.company_id == test_company.id).first()

        # Add known revenue: 100,000
        db_session.add(Transaction(
            company_id=test_company.id,
            department_id=dept.id,
            category_id=cat.id,
            transaction_date=date(2026, 7, 1),
            description="Product Sales",
            amount=100000.0,
            transaction_type=TransactionType.REVENUE,
            payment_method="Bank Transfer",
            reference_number="REV-TEST-001"
        ))
        # Add expense 1: 30,000
        db_session.add(Transaction(
            company_id=test_company.id,
            department_id=dept.id,
            category_id=cat.id,
            transaction_date=date(2026, 7, 5),
            description="Office Rent",
            amount=30000.0,
            transaction_type=TransactionType.EXPENSE,
            payment_method="Bank Transfer",
            reference_number="EXP-TEST-001"
        ))
        # Add expense 2: 20,000
        db_session.add(Transaction(
            company_id=test_company.id,
            department_id=dept.id,
            category_id=cat.id,
            transaction_date=date(2026, 7, 10),
            description="Software Licenses",
            amount=20000.0,
            transaction_type=TransactionType.EXPENSE,
            payment_method="Credit Card",
            reference_number="EXP-TEST-002"
        ))
        db_session.commit()
        return db_session

    def test_total_expenses_exact(self, precise_db, test_company):
        """Total expenses must be exactly the sum of EXPENSE transactions only."""
        agent = TransactionAnalysisAgent(db=precise_db, company_id=test_company.id)
        result = agent.analyze()
        # conftest added 10 × (1200 + i*100) = 12000+13000+...+21000 = 165000
        # + our additions = 30000 + 20000 = 50000 → total expenses = 165000 + 50000 = 215000
        expected_additions = 30000.0 + 20000.0
        conftest_expenses = sum(1200.0 + i * 100 for i in range(10))
        expected_total = conftest_expenses + expected_additions
        assert abs(result["total_expenses"] - expected_total) < 0.01, (
            f"Expected total_expenses={expected_total}, got {result['total_expenses']}"
        )

    def test_total_revenue_exact(self, precise_db, test_company):
        """Total revenue must equal only REVENUE transactions."""
        agent = TransactionAnalysisAgent(db=precise_db, company_id=test_company.id)
        result = agent.analyze()
        # conftest has no revenue. We added 100,000.
        assert abs(result["total_revenue"] - 100000.0) < 0.01, (
            f"Expected total_revenue=100000.0, got {result['total_revenue']}"
        )

    def test_net_profit_exact(self, precise_db, test_company):
        """net_profit must equal total_revenue - total_expenses."""
        agent = TransactionAnalysisAgent(db=precise_db, company_id=test_company.id)
        result = agent.analyze()
        assert abs(result["net_profit"] - (result["total_revenue"] - result["total_expenses"])) < 0.01

    def test_revenue_not_counted_as_expense(self, precise_db, test_company):
        """Revenue transactions must NOT be included in total_expenses."""
        agent = TransactionAnalysisAgent(db=precise_db, company_id=test_company.id)
        result = agent.analyze()
        # If revenue was accidentally included in expenses the total would be > 215000
        conftest_expenses = sum(1200.0 + i * 100 for i in range(10))
        assert result["total_expenses"] <= (conftest_expenses + 50000.0 + 0.01)

    def test_expense_not_counted_as_revenue(self, precise_db, test_company):
        """Expense transactions must NOT be included in total_revenue."""
        agent = TransactionAnalysisAgent(db=precise_db, company_id=test_company.id)
        result = agent.analyze()
        # Revenue should be exactly 100,000 (only REV-TEST-001)
        assert result["total_revenue"] <= 100000.01


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TENANT ISOLATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTenantIsolation:

    @pytest.fixture
    def company_b(self, db_session):
        """Create a second isolated company with its own transactions."""
        comp_b = Company(name="Company B", industry="Finance", currency="USD")
        db_session.add(comp_b)
        db_session.commit()
        db_session.refresh(comp_b)

        dept_b = Department(company_id=comp_b.id, name="Sales")
        cat_b = Category(company_id=comp_b.id, name="Marketing", color_code="#FF0000")
        db_session.add_all([dept_b, cat_b])
        db_session.commit()

        # Company B has a large distinctive expense: 999,999
        tx_b = Transaction(
            company_id=comp_b.id,
            department_id=dept_b.id,
            category_id=cat_b.id,
            transaction_date=date(2026, 8, 1),
            description="Competitor Data Purchase",
            amount=999999.0,
            transaction_type=TransactionType.EXPENSE,
            payment_method="Wire Transfer",
            reference_number="COMP_B_TX_001"
        )
        db_session.add(tx_b)
        db_session.commit()
        return comp_b

    def test_company_a_cannot_see_company_b_transactions(self, db_session, test_company, company_b):
        """TransactionAgent for Company A must never return Company B's transaction data."""
        agent_a = TransactionAnalysisAgent(db=db_session, company_id=test_company.id)
        result_a = agent_a.analyze()
        # Company B has 999,999 expense – if it leaks, total_expenses will far exceed Company A's
        assert result_a["total_expenses"] < 999999.0, (
            "Company A's total expenses should not include Company B's transactions."
        )

    def test_company_b_cannot_see_company_a_transactions(self, db_session, test_company, company_b):
        """TransactionAgent for Company B must not return Company A's data."""
        agent_b = TransactionAnalysisAgent(db=db_session, company_id=company_b.id)
        result_b = agent_b.analyze()
        # Company A has 10 conftest transactions (total ~16500). B should only have 999999.
        assert abs(result_b["total_expenses"] - 999999.0) < 0.01, (
            f"Expected Company B total_expenses=999999.0, got {result_b['total_expenses']}"
        )

    def test_supervisor_uses_correct_company_id(self, db_session, test_company, company_b):
        """SupervisorAgent must be scoped to the company_id it was constructed with."""
        sv_a = _make_supervisor(db_session, test_company)
        sv_b = _make_supervisor(db_session, company_b)
        assert sv_a.company_id == test_company.id
        assert sv_b.company_id == company_b.id
        assert sv_a.company_id != sv_b.company_id


# ═══════════════════════════════════════════════════════════════════════════════
# 6. AI RESPONSE CONTRACT TESTS (LLM mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAIResponseContract:
    """
    Tests verify the structure of the Supervisor response dict.
    Gemini API calls are mocked so tests pass without a live API key.
    """

    REQUIRED_KEYS = {"message", "agents_involved", "tools_executed", "evidence_cards", "suggested_actions", "citations"}

    def _run_supervisor(self, db_session, company, prompt: str) -> dict:
        with patch("app.agents.supervisor_agent.llm_client") as mock_llm:
            mock_llm.generate_response = AsyncMock(return_value=f"[MOCKED RESPONSE] {prompt}")
            sv = _make_supervisor(db_session, company)
            return asyncio.run(sv.execute(prompt))

    def test_response_has_required_keys_for_metric_query(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "What are our total expenses?")
        assert self.REQUIRED_KEYS.issubset(set(result.keys())), (
            f"Missing keys: {self.REQUIRED_KEYS - set(result.keys())}"
        )

    def test_response_has_required_keys_for_optimization_query(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "How can we reduce our expenses?")
        assert self.REQUIRED_KEYS.issubset(set(result.keys()))

    def test_metric_query_only_invokes_transaction_agent(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "What are our total expenses?")
        assert "TransactionAgent" in result["agents_involved"]
        assert "SavingsAgent" not in result["agents_involved"]
        assert "CostOptimizationAgent" not in result["agents_involved"]

    def test_optimization_query_invokes_savings_agents(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "How can we reduce our expenses?")
        assert "SavingsAgent" in result["agents_involved"]
        assert "CostOptimizationAgent" in result["agents_involved"]

    def test_forecast_query_does_not_invoke_savings_agent(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "Predict next month's expenses.")
        assert "ForecastingAgent" in result["agents_involved"]
        assert "SavingsAgent" not in result["agents_involved"]

    def test_citations_only_from_executed_agents(self, db_session, test_company):
        """For a simple metric query, citations must not include SaaS License Auditor."""
        result = self._run_supervisor(db_session, test_company, "What are our total expenses?")
        citation_sources = [c["source"] for c in result.get("citations", [])]
        assert "Financial Ledgers" in citation_sources
        assert "SaaS License Auditor" not in citation_sources

    def test_suggested_actions_empty_for_metric_query(self, db_session, test_company):
        """A simple metric query must not generate 'Cancel SaaS Seats' or similar actions."""
        result = self._run_supervisor(db_session, test_company, "What are our total expenses?")
        action_labels = [a.get("action", "") for a in result.get("suggested_actions", [])]
        assert "CANCEL_UNUSED_SEATS" not in action_labels

    def test_agents_involved_is_list(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "What are our total expenses?")
        assert isinstance(result["agents_involved"], list)

    def test_message_is_string(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "What is our total revenue?")
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_evidence_cards_is_list(self, db_session, test_company):
        result = self._run_supervisor(db_session, test_company, "What is our net profit?")
        assert isinstance(result["evidence_cards"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CURRENCY SYMBOL UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

class TestCurrencySymbol:

    def test_inr_symbol(self):
        assert _currency_symbol("INR") == "₹"

    def test_usd_symbol(self):
        assert _currency_symbol("USD") == "$"

    def test_eur_symbol(self):
        assert _currency_symbol("EUR") == "€"

    def test_gbp_symbol(self):
        assert _currency_symbol("GBP") == "£"

    def test_unknown_returns_code(self):
        assert _currency_symbol("XYZ") == "XYZ"

    def test_case_insensitive(self):
        assert _currency_symbol("inr") == "₹"
        assert _currency_symbol("usd") == "$"
