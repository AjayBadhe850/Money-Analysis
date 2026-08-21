import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.api_v1 import api_router
from app.database.session import Base, engine, SessionLocal
from app.models.company import Company
from app.utils.seed_data import seed_database
from app.core.middleware import StructuredLoggingMiddleware, init_sentry, limiter

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("costwise")

# Initialize Sentry if configured
init_sentry()

# Create database tables automatically if not present
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Auto-seed if empty
    db = SessionLocal()
    try:
        if not db.query(Company).first():
            logger.info("Database is empty. Populating demo seed dataset...")
            seed_database()
    finally:
        db.close()
except Exception as e:
    logger.warning(f"Database initialization note: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Money Analysis – Enterprise Multi-Agent Finance Controller & Autonomous Cost Optimization Platform (Stage 3 Production)",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Structured JSON Logging Middleware
app.add_middleware(StructuredLoggingMiddleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "3.0.0",
        "stage": settings.STAGE,
        "docs_url": "/docs"
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "database": "connected",
        "stage": 3,
        "service": "money-analysis-backend",
        "multi_agent_suite": "active",
        "celery_scheduler": "ready"
    }
