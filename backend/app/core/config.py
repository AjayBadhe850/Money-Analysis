import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Money Analysis – Multi-Agent Finance Controller"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "costwise_super_secret_jwt_key_stage3_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database (Supabase PostgreSQL / SQLite fallback)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/costwise_db"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # Redis & Celery Background Processing
    REDIS_URL: str = "redis://localhost:6379/0"

    # Stage Flag
    STAGE: int = 3
    ENABLE_AI_AGENTS: bool = True

    # AI & LLM Settings
    LLM_PROVIDER: str = "mock"  # "gemini", "openai", "mock"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"

    # Cloudinary / S3 File Storage
    STORAGE_PROVIDER: str = "local"  # "cloudinary", "s3", "local"
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Sentry Observability
    SENTRY_DSN: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:80",
        "http://localhost",
        "https://costwise-ai.vercel.app",
        "*"
    ]

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")


settings = Settings()
