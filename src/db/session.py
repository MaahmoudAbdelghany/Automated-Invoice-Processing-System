"""
Database Session Management.

Creates the SQLAlchemy engine and provides a session dependency
for use with FastAPI's dependency injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings


# ---------------------------------------------------------------------------
# Synchronous engine & session (used for simple scripts, migrations, etc.)
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL statements when DEBUG=True
    pool_pre_ping=True,   # Verify connections before using them
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Session:
    """
    FastAPI dependency that yields a database session.

    Usage in a route::

        @router.get("/invoices")
        def list_invoices(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
