import time
import json
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

logger = logging.getLogger("costwise.access")

# Initialize SlowAPI rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


def init_sentry():
    """Initializes Sentry error tracking if SENTRY_DSN is provided."""
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=0.2,
                profiles_sample_rate=0.2,
            )
            logger.info("Sentry observability initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Sentry: {e}")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Structured JSON Logging Middleware tracking latency, user context, and status codes."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Inject Request ID header
        response.headers["X-Request-ID"] = request_id

        # Skip high-frequency health check spam in structured logs
        if request.url.path not in ["/api/health", "/docs", "/openapi.json"]:
            log_record = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            }
            logger.info(json.dumps(log_record))

        return response
