from app.services.finance_service import (
    calculate_net_profit, calculate_subscription_cost
)
from app.models.subscription import Subscription, SubscriptionStatus
from datetime import date


def test_financial_calculations():
    # Net Profit
    revenue = 250000.0
    expenses = 175000.0
    net_profit = calculate_net_profit(revenue, expenses)
    assert net_profit == 75000.0


def test_subscription_waste_calculation():
    # Example: 20 licenses, 8 active -> 12 unused
    # Monthly cost $2,000 -> $100 per license -> $1,200 monthly waste
    sub = Subscription(
        service_name="Salesforce CRM",
        monthly_cost=2000.0,
        total_licenses=20,
        active_licenses=8,
        renewal_date=date(2026, 12, 31),
        status=SubscriptionStatus.ACTIVE
    )
    metrics = calculate_subscription_cost(sub)
    assert metrics["annual_cost"] == 24000.0
    assert metrics["utilization_percentage"] == 40.0
    assert metrics["unused_licenses"] == 12
    assert metrics["estimated_monthly_waste"] == 1200.0
    assert metrics["estimated_annual_waste"] == 14400.0
    assert metrics["has_waste_flag"] is True
