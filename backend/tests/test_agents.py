import asyncio
import pytest
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
from app.agents.supervisor_agent import SupervisorAgent
from app.services.categorizer_service import ExpenseCategorizerService


def test_transaction_analysis_agent(db_session, test_company):
    agent = TransactionAnalysisAgent(db=db_session, company_id=test_company.id)
    res = agent.analyze()
    assert "total_expenses" in res
    assert "total_revenue" in res
    assert "monthly_burn_rate" in res
    assert "top_categories" in res


def test_budget_agent(db_session, test_company):
    agent = BudgetAgent(db=db_session, company_id=test_company.id)
    res = agent.analyze()
    assert "total_allocated" in res
    assert "overall_usage_pct" in res
    assert "budget_lines" in res


def test_anomaly_detection_agent(db_session, test_company):
    agent = AnomalyDetectionAgent(db=db_session, company_id=test_company.id)
    anomalies = agent.scan_transactions()
    assert isinstance(anomalies, list)


def test_vendor_intelligence_agent(db_session, test_company):
    agent = VendorIntelligenceAgent(db=db_session, company_id=test_company.id)
    res = agent.analyze()
    assert "vendor_count" in res
    assert "average_vendor_efficiency_score" in res
    assert 0 <= res["average_vendor_efficiency_score"] <= 100


def test_subscription_optimization_agent(db_session, test_company):
    agent = SubscriptionOptimizationAgent(db=db_session, company_id=test_company.id)
    res = agent.analyze()
    assert "potential_monthly_savings" in res
    assert "potential_annual_savings" in res
    assert res["potential_annual_savings"] == round(res["potential_monthly_savings"] * 12, 2)


def test_forecasting_agent(db_session, test_company):
    agent = ForecastingAgent(db=db_session, company_id=test_company.id)
    res = agent.generate_forecast(horizon_days=30)
    assert res["horizon_days"] == 30
    assert "total_projected_spend" in res
    assert "series" in res


def test_savings_and_cost_optimization_agents(db_session, test_company):
    sav_agent = SavingsOpportunityAgent(db=db_session, company_id=test_company.id)
    sav_res = sav_agent.discover_opportunities()
    assert "opportunities" in sav_res
    assert sav_res["total_potential_monthly"] >= 0

    opt_agent = CostOptimizationAgent(db=db_session, company_id=test_company.id)
    plan = opt_agent.generate_plan(target_savings_amount=20000.0, timeframe_months=3)
    assert plan["target_savings"] == 20000.0
    assert plan["timeframe_months"] == 3
    assert "recommended_actions" in plan


def test_what_if_simulation_agent(db_session, test_company):
    agent = WhatIfSimulationAgent(db=db_session, company_id=test_company.id)
    sim = agent.simulate(
        department_spend_adjustments={"Engineering": -0.15},
        revenue_growth_adjustment=0.10
    )
    assert "simulated_monthly_expense" in sim
    assert "simulated_net_profit" in sim
    assert "profit_margin_change_pct" in sim


def test_approval_agent_lifecycle(db_session, test_company):
    agent = ApprovalAgent(db=db_session, company_id=test_company.id)
    req = agent.create_request(
        request_type="CANCEL_SUBSCRIPTION",
        title="Test Revoke Licenses",
        details="Cancel 10 unused licenses",
        impact_savings_monthly=2500.0,
        risk_level="LOW"
    )
    assert req.status == "PENDING"

    processed = agent.process_action(request_id=req.id, action="APPROVE", notes="Approved by Finance")
    assert processed["status"] in ["APPROVED", "EXECUTED"]


def test_expense_categorizer_hybrid(db_session, test_company):
    categorizer = ExpenseCategorizerService(db=db_session, company_id=test_company.id)
    
    # Tier 1: Keyword rule
    res1 = categorizer.categorize("AWS EC2 On-Demand Compute Instances")
    assert res1["predicted_category"] == "Cloud Infrastructure"
    assert res1["prediction_method"] == "RULE"

    # Tier 2: User correction
    categorizer.record_user_correction("Specialized Widget", "Custom Hardware")
    res2 = categorizer.categorize("Purchase of Specialized Widget Model X")
    assert res2["predicted_category"] == "Custom Hardware"
    assert res2["prediction_method"] == "USER_CORRECTION"


def test_supervisor_agent_routing(db_session, test_company):
    supervisor = SupervisorAgent(db=db_session, company_id=test_company.id)
    res = asyncio.run(supervisor.execute("How can we save $50,000 next quarter?"))
    assert "message" in res
    assert len(res["agents_involved"]) >= 1
    assert "tools_executed" in res
