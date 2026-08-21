from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    dashboard,
    transactions,
    budgets,
    vendors,
    subscriptions,
    invoices,
    departments,
    alerts,
    audit,
    ai,
    reports,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(transactions.router)
api_router.include_router(budgets.router)
api_router.include_router(vendors.router)
api_router.include_router(subscriptions.router)
api_router.include_router(invoices.router)
api_router.include_router(departments.router)
api_router.include_router(alerts.router)
api_router.include_router(audit.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router, prefix="/ai", tags=["AI Multi-Agent System"])
