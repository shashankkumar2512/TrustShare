# server/src/database/core.py

# CRITICAL: Load .env BEFORE reading any environment variables
from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://trustshare:trustshare@localhost:5432/trustshare",
)

def is_postgresql_url(url: str) -> bool:
    return url.startswith(("postgresql://", "postgresql+psycopg2://", "postgresql+psycopg://"))

def validate_database_url(url: str, require_postgresql: bool = False) -> None:
    if require_postgresql and not is_postgresql_url(url):
        raise RuntimeError(
            "TrustShare requires PostgreSQL for integration and production. "
            "Set DATABASE_URL to a postgresql+psycopg2:// URL."
        )

validate_database_url(
    DATABASE_URL,
    os.getenv("REQUIRE_POSTGRESQL", "false").lower() in {"1", "true", "yes"},
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
