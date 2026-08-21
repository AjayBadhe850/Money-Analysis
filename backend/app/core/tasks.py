import logging
from datetime import datetime, date, timedelta, timezone
from app.core.celery_app import celery_app
from app.database.session import SessionLocal
from app.models.company import Company
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.future_ai import Anomaly
from app.models.alert import CostAlert, AlertSeverity
from app.agents.anomaly_agent import AnomalyDetectionAgent
from app.agents.savings_agent import SavingsOpportunityAgent
from app.agents.forecasting_agent import ForecastingAgent

logger = logging.getLogger("costwise.tasks")

# In-memory execution timestamps registry
TASK_EXECUTION_REGISTRY = {
    "daily_anomaly_scan": {"last_run": None, "status": "READY", "details": "Runs daily at 02:00 UTC"},
    "weekly_savings_optimization": {"last_run": None, "status": "READY", "details": "Runs Mondays at 03:00 UTC"},
    "monthly_cfo_report": {"last_run": None, "status": "READY", "details": "Runs 1st of month at 04:00 UTC"},
}


@celery_app.task(name="app.core.tasks.daily_anomaly_and_renewal_scan")
def daily_anomaly_and_renewal_scan():
    """Daily job: Runs Isolation Forest anomaly scans & checks upcoming subscription renewals."""
    logger.info("Executing daily_anomaly_and_renewal_scan...")
    db = SessionLocal()
    try:
        companies = db.query(Company).all()
        for comp in companies:
            # 1. Isolation Forest scan
            agent = AnomalyDetectionAgent(db=db, company_id=comp.id)
            res = agent.scan_all_transactions(contamination=0.08)
            logger.info(f"Company {comp.id}: Detected {res['anomalies_detected']} anomalies.")

            # 2. Check renewals in next 30 days
            today = date.today()
            in_30_days = today + timedelta(days=30)
            expiring_subs = db.query(Subscription).filter(
                Subscription.company_id == comp.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.renewal_date <= in_30_days,
                Subscription.renewal_date >= today
            ).all()

            for sub in expiring_subs:
                days_left = (sub.renewal_date - today).days
                # Create alert if not already exists
                existing = db.query(CostAlert).filter(
                    CostAlert.company_id == comp.id,
                    CostAlert.title.contains(sub.service_name),
                    CostAlert.status == "ACTIVE"
                ).first()
                if not existing:
                    alert = CostAlert(
                        company_id=comp.id,
                        department_id=sub.department_id,
                        severity=AlertSeverity.WARNING,
                        title=f"Upcoming Renewal: {sub.service_name}",
                        message=f"{sub.service_name} will renew in {days_left} days (${sub.monthly_cost:,.2f}/mo). Review license allocation.",
                        status="ACTIVE"
                    )
                    db.add(alert)
            db.commit()

        TASK_EXECUTION_REGISTRY["daily_anomaly_scan"]["last_run"] = datetime.now(timezone.utc).isoformat()
        TASK_EXECUTION_REGISTRY["daily_anomaly_scan"]["status"] = "SUCCESS"
        return {"status": "SUCCESS", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error in daily_anomaly_and_renewal_scan: {e}")
        TASK_EXECUTION_REGISTRY["daily_anomaly_scan"]["status"] = f"ERROR: {str(e)}"
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.core.tasks.weekly_savings_optimization_analysis")
def weekly_savings_optimization_analysis():
    """Weekly job: Re-aggregates company-wide savings opportunities."""
    logger.info("Executing weekly_savings_optimization_analysis...")
    db = SessionLocal()
    try:
        companies = db.query(Company).all()
        for comp in companies:
            agent = SavingsOpportunityAgent(db=db, company_id=comp.id)
            opps = agent.discover_opportunities()
            logger.info(f"Company {comp.id}: Identified {opps['opportunities_count']} savings opportunities totaling ${opps['total_potential_monthly']:,.2f}/mo.")

        TASK_EXECUTION_REGISTRY["weekly_savings_optimization"]["last_run"] = datetime.now(timezone.utc).isoformat()
        TASK_EXECUTION_REGISTRY["weekly_savings_optimization"]["status"] = "SUCCESS"
        return {"status": "SUCCESS", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error in weekly_savings_optimization_analysis: {e}")
        TASK_EXECUTION_REGISTRY["weekly_savings_optimization"]["status"] = f"ERROR: {str(e)}"
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.core.tasks.monthly_financial_report_generation")
def monthly_financial_report_generation():
    """Monthly job: Generates 90-day forecasts and financial controller reports."""
    logger.info("Executing monthly_financial_report_generation...")
    db = SessionLocal()
    try:
        companies = db.query(Company).all()
        for comp in companies:
            forecaster = ForecastingAgent(db=db, company_id=comp.id)
            fc = forecaster.generate_forecast(horizon_days=90)
            logger.info(f"Company {comp.id}: Projected 90-day spend = ${fc['total_projected_spend']:,.2f} ({fc['trend']}).")

        TASK_EXECUTION_REGISTRY["monthly_cfo_report"]["last_run"] = datetime.now(timezone.utc).isoformat()
        TASK_EXECUTION_REGISTRY["monthly_cfo_report"]["status"] = "SUCCESS"
        return {"status": "SUCCESS", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error in monthly_financial_report_generation: {e}")
        TASK_EXECUTION_REGISTRY["monthly_cfo_report"]["status"] = f"ERROR: {str(e)}"
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()
