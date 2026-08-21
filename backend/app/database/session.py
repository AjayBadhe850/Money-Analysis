import logging
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}

# Ensure consistent database path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
fallback_db_path = BASE_DIR / "money_analysis.db" if not (BASE_DIR / "costwise.db").exists() else BASE_DIR / "costwise.db"
fallback_url = f"sqlite:///{fallback_db_path.as_posix()}"

try:
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info(f"Database connected successfully using {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.warning(
        f"Could not connect to configured DATABASE_URL ({db_url}): {e}. "
        f"Defaulting to local SQLite database ({fallback_db_path}) for development."
    )
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
