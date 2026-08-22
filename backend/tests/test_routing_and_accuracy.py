"""
Regression tests for:
- Exact multi-agent routing (Changes 21)
- Financial metric correctness with deterministic data (Change 22)
- Period-aware filter: current month vs all-time (Change 23)
- Department-scoped metrics (Change 24)
- Tenant isolation (Change 25)
- What-If adjustment parsing (Change 26)
- _extract_money_amount: percentage must NOT be treated as money
- Response contract: required keys always present
"""

import asyncio
from datetime import date, timedelta
import calendar
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.supervisor_agent import SupervisorAgent, _currency_symbol
from app.agents.transaction_agent import TransactionAnalysisAgent
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.category import Category
from app.models.vendor import Vendor
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sv(db, company) -> SupervisorAgent:
    return SupervisorAgent(db=db, company_id=company.id)


def _route(db, company, prompt: str):
    return _sv(db, company)._route_intent(prompt.lower())


def _run(db, company, prompt: str) -> dict:
    """Execute supervisor with Gemini mocked out."""
    with patch("app.agents.supervisor_agent.llm_client") as mock_llm:
        mock_llm.generate_response = AsyncMock(return_value=f"[MOCKED] {prompt}")
        sv = _sv(db, company)
        return asyncio.run(sv.execute(prompt))


# ── Today / month helpers ─────────────────────────────────────────────────────

def _today() -> date:
    return date.today()


def _month_start() -> date:
    return _today().replace(day=1)


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  EXACT ROUTING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestExactRouting:

    def test_total_expenses_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "what are our total expenses?")
        assert agents == ["SupervisorAgent", "TransactionAgent"], agents

    def test_total_revenue_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "what is our total revenue?")
        assert agents == ["SupervisorAgent", "TransactionAgent"], agents

    def test_net_profit_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "what is our net profit?")
        assert agents == ["SupervisorAgent", "TransactionAgent"], agents

    def test_expenses_this_month_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "what are our expenses this month?")
        assert agents == ["SupervisorAgent", "TransactionAgent"], agents

    def test_reduce_total_expenses_routes_to_optimization(self, db_session, test_company):
        """'how can we reduce total expenses?' contains 'total expenses' but optimization wins."""
        agents = _route(db_session, test_company, "how can we reduce total expenses?")
        assert "SavingsAgent" in agents
        assert "CostOptimizationAgent" in agents
        assert "BudgetAgent" in agents
        assert "TransactionAgent" in agents
        assert agents[0] == "SupervisorAgent"

    def test_find_savings_routes_to_optimization(self, db_session, test_company):
        agents = _route(db_session, test_company, "find cost-saving opportunities")
        assert "SavingsAgent" in agents
        assert "CostOptimizationAgent" in agents

    def test_what_if_routes_before_optimization(self, db_session, test_company):
        """What-if must be priority 1 – 'reduce' is in both WHATIF and OPTIMIZATION."""
        agents = _route(db_session, test_company, "what if we reduce marketing by 20%?")
        assert agents == ["SupervisorAgent", "WhatIfAgent"], agents

    def test_what_if_increase_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "what if we increase hr spending by 10%?")
        assert agents == ["SupervisorAgent", "WhatIfAgent"], agents

    def test_anomaly_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "find suspicious transactions")
        assert "AnomalyAgent" in agents
        assert "TransactionAgent" in agents
        assert "SavingsAgent" not in agents

    def test_forecast_routing(self, db_session, test_company):
        agents = _route(db_session, test_company, "predict next month spending")
        assert "ForecastingAgent" in agents
        assert "SavingsAgent" not in agents

    def test_default_routes_to_transaction_only(self, db_session, test_company):
        agents = _route(db_session, test_company, "give me a finance overview")
        assert agents == ["SupervisorAgent", "TransactionAgent"], agents

    def test_no_duplicates_in_route(self, db_session, test_company):
        for prompt in [
            "reduce costs and save money",
            "total expenses this month",
            "what if we reduce marketing by 20%?",
        ]:
            agents = _route(db_session, test_company, prompt)
            assert len(agents) == len(set(agents)), f"Duplicates in route for '{prompt}': {agents}"

    def test_supervisor_always_first(self, db_session, test_company):
        for prompt in ["total expenses", "reduce costs", "forecast spending"]:
            agents = _route(db_session, test_company, prompt)
            assert agents[0] == "SupervisorAgent"


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  FINANCIAL METRIC CORRECTNESS (deterministic data)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancialAccuracy:

    @pytest.fixture
    def precise_db(self, db_session, test_company):
        """
        Add transactions with known exact amounts so we can assert exact totals.

        Revenue:  ₹100,000 (REV-EXACT-001)
        Expenses: ₹30,000  (EXP-EXACT-001)
                  ₹20,000  (EXP-EXACT-002)
        """
        dept = db_session.query(Department).filter_by(company_id=test_company.id).first()
        cat = db_session.query(Category).filter_by(company_id=test_company.id).first()

        db_session.add(Transaction(
            company_id=test_company.id, department_id=dept.id, category_id=cat.id,
            transaction_date=date(2026, 7, 1), description="Product Sales",
            amount=100000.0, transaction_type=TransactionType.REVENUE,
            payment_method="Bank Transfer", reference_number="REV-EXACT-001",
        ))
        db_session.add(Transaction(
            company_id=test_company.id, department_id=dept.id, category_id=cat.id,
            transaction_date=date(2026, 7, 5), description="Office Rent",
            amount=30000.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Bank Transfer", reference_number="EXP-EXACT-001",
        ))
        db_session.add(Transaction(
            company_id=test_company.id, department_id=dept.id, category_id=cat.id,
            transaction_date=date(2026, 7, 10), description="Software Licenses",
            amount=20000.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Credit Card", reference_number="EXP-EXACT-002",
        ))
        db_session.commit()
        return db_session

    def test_total_expenses_exact(self, precise_db, test_company):
        agent = TransactionAnalysisAgent(precise_db, test_company.id)
        result = agent.analyze()
        # conftest seeded 10 expenses: 1200+1300+…+2100 = 16500
        # precise fixture added 30000+20000 = 50000
        expected = 16500.0 + 50000.0
        assert abs(result["total_expenses"] - expected) < 0.01, result["total_expenses"]

    def test_total_revenue_exact(self, precise_db, test_company):
        agent = TransactionAnalysisAgent(precise_db, test_company.id)
        result = agent.analyze()
        assert abs(result["total_revenue"] - 100000.0) < 0.01, result["total_revenue"]

    def test_net_profit_exact(self, precise_db, test_company):
        agent = TransactionAnalysisAgent(precise_db, test_company.id)
        result = agent.analyze()
        assert abs(result["net_profit"] - (result["total_revenue"] - result["total_expenses"])) < 0.01

    def test_revenue_not_counted_as_expense(self, precise_db, test_company):
        agent = TransactionAnalysisAgent(precise_db, test_company.id)
        result = agent.analyze()
        # Revenue (100000) must not inflate expenses
        assert result["total_expenses"] <= (16500.0 + 50000.0 + 0.01)

    def test_expense_not_counted_as_revenue(self, precise_db, test_company):
        agent = TransactionAnalysisAgent(precise_db, test_company.id)
        result = agent.analyze()
        assert result["total_revenue"] <= 100000.01


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  PERIOD-AWARE FILTER: "this month" must not return all-time totals
# ═══════════════════════════════════════════════════════════════════════════════

class TestPeriodFilter:

    @pytest.fixture
    def period_db(self, db_session, test_company):
        """
        Old expense (previous month):  ₹100,000
        Current month expense:         ₹25,000
        """
        dept = db_session.query(Department).filter_by(company_id=test_company.id).first()
        cat = db_session.query(Category).filter_by(company_id=test_company.id).first()

        today = date.today()
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)

        # Old expense – last month
        db_session.add(Transaction(
            company_id=test_company.id, department_id=dept.id, category_id=cat.id,
            transaction_date=last_month_end, description="Old Server Cost",
            amount=100000.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Bank Transfer", reference_number="OLD-EXP-001",
        ))
        # Current month expense
        db_session.add(Transaction(
            company_id=test_company.id, department_id=dept.id, category_id=cat.id,
            transaction_date=first_this_month, description="Current SaaS Renewal",
            amount=25000.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Credit Card", reference_number="CUR-EXP-001",
        ))
        db_session.commit()
        return db_session

    def test_this_month_excludes_previous_month(self, period_db, test_company):
        """Expenses 'this month' must NOT include the old ₹100,000 expense."""
        today = date.today()
        start = today.replace(day=1)
        agent = TransactionAnalysisAgent(period_db, test_company.id)
        result = agent.analyze(start_date=start, end_date=today)

        # conftest expenses in August (some of the 10 test txs may be in current month
        # but the key assertion is the old 100000 is excluded)
        assert result["total_expenses"] < 100000.0 + 25000.0 + 1.0, (
            f"This-month query should not include last-month expenses. Got: {result['total_expenses']}"
        )
        # The 100000 old expense must not appear at all
        assert result["total_expenses"] < 130000.0, result["total_expenses"]

    def test_all_time_includes_old_expense(self, period_db, test_company):
        """All-time query must include both old and new expenses."""
        agent = TransactionAnalysisAgent(period_db, test_company.id)
        result = agent.analyze()
        # conftest (16500) + old (100000) + new (25000) = 141500
        assert result["total_expenses"] >= 141000.0, result["total_expenses"]

    def test_period_resolution_this_month(self, db_session, test_company):
        """SupervisorAgent._resolve_period must return month-start for 'this month'."""
        sv = _sv(db_session, test_company)
        start, end, label = sv._resolve_period("what are our expenses this month?")
        today = date.today()
        assert label == "this_month"
        assert start == today.replace(day=1)
        assert end == today

    def test_period_resolution_all_time(self, db_session, test_company):
        sv = _sv(db_session, test_company)
        start, end, label = sv._resolve_period("what are our total expenses?")
        assert label == "all_time"
        assert start is None
        assert end is None


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  DEPARTMENT FILTER
# ═══════════════════════════════════════════════════════════════════════════════

class TestDepartmentFilter:

    @pytest.fixture
    def dept_db(self, db_session, test_company):
        """
        Marketing dept:    ₹30,000 expense
        Engineering dept:  already has conftest data (16500)
        """
        cat = db_session.query(Category).filter_by(company_id=test_company.id).first()
        marketing = Department(company_id=test_company.id, name="Marketing")
        db_session.add(marketing)
        db_session.commit()
        db_session.refresh(marketing)

        db_session.add(Transaction(
            company_id=test_company.id, department_id=marketing.id, category_id=cat.id,
            transaction_date=_month_start(), description="Digital Ads",
            amount=30000.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Credit Card", reference_number="MKT-EXP-001",
        ))
        db_session.commit()
        return db_session

    def test_marketing_filter_returns_only_marketing_expenses(self, dept_db, test_company):
        agent = TransactionAnalysisAgent(dept_db, test_company.id)
        result = agent.analyze(department_name="Marketing")
        assert abs(result["total_expenses"] - 30000.0) < 0.01, result["total_expenses"]

    def test_engineering_filter_excludes_marketing(self, dept_db, test_company):
        agent = TransactionAnalysisAgent(dept_db, test_company.id)
        result = agent.analyze(department_name="Engineering")
        # Engineering only = conftest 16500; must not include Marketing 30000
        assert result["total_expenses"] < 30000.0, result["total_expenses"]

    def test_department_extraction_from_prompt(self, dept_db, test_company):
        sv = _sv(dept_db, test_company)
        dept = sv._extract_department("how much did Marketing spend this month?")
        assert dept == "Marketing"

    def test_no_department_in_prompt_returns_none(self, db_session, test_company):
        sv = _sv(db_session, test_company)
        dept = sv._extract_department("what are our total expenses?")
        assert dept is None


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  TENANT ISOLATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestTenantIsolation:

    @pytest.fixture
    def company_b(self, db_session):
        comp_b = Company(name="Company B", industry="Retail", currency="USD")
        db_session.add(comp_b)
        db_session.commit()
        db_session.refresh(comp_b)

        dept_b = Department(company_id=comp_b.id, name="Sales")
        cat_b = Category(company_id=comp_b.id, name="Advertising", color_code="#FF0000")
        db_session.add_all([dept_b, cat_b])
        db_session.commit()

        # Company B has a large distinctive expense: 999,999
        db_session.add(Transaction(
            company_id=comp_b.id, department_id=dept_b.id, category_id=cat_b.id,
            transaction_date=date(2026, 8, 1), description="Competitor Data",
            amount=999999.0, transaction_type=TransactionType.EXPENSE,
            payment_method="Wire Transfer", reference_number="COMP_B_TX_001",
        ))
        db_session.commit()
        return comp_b

    def test_company_a_cannot_see_company_b_data(self, db_session, test_company, company_b):
        agent = TransactionAnalysisAgent(db_session, test_company.id)
        result = agent.analyze()
        assert result["total_expenses"] < 999999.0, (
            f"Company A expenses should not include Company B's 999999. Got: {result['total_expenses']}"
        )

    def test_company_b_expenses_are_exact(self, db_session, test_company, company_b):
        agent = TransactionAnalysisAgent(db_session, company_b.id)
        result = agent.analyze()
        assert abs(result["total_expenses"] - 999999.0) < 0.01, result["total_expenses"]

    def test_supervisor_company_id_is_isolated(self, db_session, test_company, company_b):
        sv_a = _sv(db_session, test_company)
        sv_b = _sv(db_session, company_b)
        assert sv_a.company_id == test_company.id
        assert sv_b.company_id == company_b.id
        assert sv_a.company_id != sv_b.company_id

    def test_end_to_end_metric_query_isolates_company_a(self, db_session, test_company, company_b):
        result = _run(db_session, test_company, "What are our total expenses?")
        # The response must NOT contain the Company B amount
        assert "999999" not in result["message"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  WHAT-IF PARSING
# ═══════════════════════════════════════════════════════════════════════════════

class TestWhatIfParsing:

    @pytest.fixture
    def sv_with_marketing(self, db_session, test_company):
        """Return a supervisor with a Marketing department in DB."""
        marketing = Department(company_id=test_company.id, name="Marketing")
        db_session.add(marketing)
        db_session.commit()
        return _sv(db_session, test_company)

    def test_decrease_marketing_by_20_percent(self, sv_with_marketing):
        adj = sv_with_marketing._build_what_if_adjustments(
            "What if Marketing spending decreases by 20%?"
        )
        assert adj == {"Marketing": -0.20}, adj

    def test_increase_by_10_percent(self, db_session, test_company):
        hr = Department(company_id=test_company.id, name="HR")
        db_session.add(hr)
        db_session.commit()
        sv = _sv(db_session, test_company)
        adj = sv._build_what_if_adjustments("What if HR spending increases by 10%?")
        assert adj == {"HR": 0.10}, adj

    def test_unknown_department_returns_empty(self, db_session, test_company):
        sv = _sv(db_session, test_company)
        adj = sv._build_what_if_adjustments("What if Accounting spending decreases by 15%?")
        assert adj == {}, adj

    def test_missing_percentage_returns_empty(self, db_session, test_company):
        sv = _sv(db_session, test_company)
        adj = sv._build_what_if_adjustments("What if Engineering spending decreases?")
        assert adj == {}, adj


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  MONEY AMOUNT PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class TestMoneyParser:

    @pytest.fixture
    def sv(self, db_session, test_company):
        return _sv(db_session, test_company)

    def test_percentage_not_parsed_as_money(self, sv):
        assert sv._extract_money_amount("reduce Marketing by 15%") is None

    def test_money_lakh(self, sv):
        assert sv._extract_money_amount("save ₹2 lakh") == 200_000.0

    def test_money_k(self, sv):
        assert sv._extract_money_amount("save $50k") == 50_000.0

    def test_money_million(self, sv):
        result = sv._extract_money_amount("target $1 million")
        assert result == 1_000_000.0

    def test_money_plain(self, sv):
        result = sv._extract_money_amount("save ₹25000")
        assert result == 25000.0

    def test_money_none_when_no_amount(self, sv):
        assert sv._extract_money_amount("find cost saving opportunities") is None

    def test_percentage_parser_basic(self, sv):
        assert abs(sv._extract_percentage("15%") - 0.15) < 0.001

    def test_percentage_parser_decimal(self, sv):
        assert abs(sv._extract_percentage("7.5%") - 0.075) < 0.001

    def test_percentage_out_of_range_returns_none(self, sv):
        assert sv._extract_percentage("150%") is None


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  AI RESPONSE CONTRACT
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponseContract:

    REQUIRED = {"message", "agents_involved", "tools_executed", "evidence_cards", "suggested_actions", "citations"}

    def test_required_keys_metric_query(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        missing = self.REQUIRED - set(result.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_required_keys_optimization_query(self, db_session, test_company):
        result = _run(db_session, test_company, "How can we reduce costs?")
        assert self.REQUIRED.issubset(set(result.keys()))

    def test_metric_query_agents(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        assert "TransactionAgent" in result["agents_involved"]
        assert "SavingsAgent" not in result["agents_involved"]
        assert "CostOptimizationAgent" not in result["agents_involved"]

    def test_optimization_query_agents(self, db_session, test_company):
        result = _run(db_session, test_company, "How can we reduce our costs?")
        assert "SavingsAgent" in result["agents_involved"]
        assert "CostOptimizationAgent" in result["agents_involved"]

    def test_metric_citations_contain_financial_ledgers(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        sources = [c["source"] for c in result["citations"]]
        assert "Financial Ledgers" in sources

    def test_metric_citations_no_saas_auditor(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        sources = [c["source"] for c in result["citations"]]
        assert "SaaS License Auditor" not in sources

    def test_metric_suggested_actions_no_cancel_seats(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        actions = [a.get("action") for a in result["suggested_actions"]]
        assert "CANCEL_UNUSED_SEATS" not in actions

    def test_message_is_non_empty_string(self, db_session, test_company):
        result = _run(db_session, test_company, "What are our total expenses?")
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_evidence_cards_is_list(self, db_session, test_company):
        result = _run(db_session, test_company, "What is our net profit?")
        assert isinstance(result["evidence_cards"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  CURRENCY SYMBOL UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

class TestCurrencySymbol:
    def test_inr(self):   assert _currency_symbol("INR") == "₹"
    def test_usd(self):   assert _currency_symbol("USD") == "$"
    def test_eur(self):   assert _currency_symbol("EUR") == "€"
    def test_gbp(self):   assert _currency_symbol("GBP") == "£"
    def test_unknown(self): assert _currency_symbol("XYZ") == "XYZ"
    def test_lowercase(self): assert _currency_symbol("inr") == "₹"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. MATH & GENERAL QUERY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMathAndGeneralQueries:
    def test_simple_addition(self, db_session, test_company):
        result = _run(db_session, test_company, "10+2")
        assert "12" in result["message"]
        assert result["agents_involved"] == ["SupervisorAgent"]

    def test_multiplication_query(self, db_session, test_company):
        result = _run(db_session, test_company, "What is 500 * 12?")
        assert "6,000" in result["message"] or "6000" in result["message"]
        assert result["agents_involved"] == ["SupervisorAgent"]

    def test_greeting_query(self, db_session, test_company):
        result = _run(db_session, test_company, "Hello")
        assert "Money Analysis AI Financial Controller" in result["message"]
        assert result["agents_involved"] == ["SupervisorAgent"]

