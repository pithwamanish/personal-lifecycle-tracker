from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Environment variable for database connection
DEFAULT_DATABASE_URL = "sqlite:///./lifecycle.db"


def get_database_url() -> str:
    """
    Resolve the database connection URL from environment variables.
    Checks DATABASE_URL first, then DB_URL as fallback, defaulting to local SQLite.
    Normalizes legacy postgres:// scheme to postgresql:// for SQLAlchemy.
    """
    raw_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or DEFAULT_DATABASE_URL
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    return raw_url


def is_postgres_url(url: str) -> bool:
    """Check whether a URL targets a PostgreSQL database."""
    return url.startswith("postgresql") or url.startswith("postgres")


def create_engine_for_url(url: Optional[str] = None) -> Engine:
    """
    Factory function creating a database-agnostic SQLAlchemy Engine.
    Handles dialect-specific connection arguments (such as SQLite foreign keys and thread safety,
    or PostgreSQL connection pooling and pre-ping checks).
    """
    db_url = url or get_database_url()
    connect_args = {}

    pool_pre_ping_env = os.getenv("DB_POOL_PRE_PING")
    if pool_pre_ping_env is not None:
        pool_pre_ping = pool_pre_ping_env.lower() in ("true", "1", "yes")
    else:
        # Eliminate cross-region SELECT 1 ping roundtrips in AWS Lambda; keep True for container/local setups
        is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_EXECUTION_ENV"))
        pool_pre_ping = not is_lambda

    engine_kwargs = {
        "pool_pre_ping": pool_pre_ping,
    }

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Ensure parent directory exists for file-based SQLite databases
        if not db_url.startswith("sqlite:///:memory:"):
            # Strip prefix (e.g. 'sqlite:///' or 'sqlite://')
            cleaned_path = db_url.replace("sqlite:///", "", 1) if db_url.startswith("sqlite:///") else db_url.replace("sqlite://", "", 1)
            # Remove query parameters if any
            cleaned_path = cleaned_path.split("?")[0]
            db_dir = os.path.dirname(cleaned_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
    elif is_postgres_url(db_url):
        is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_EXECUTION_ENV"))
        default_pool_recycle = "300" if is_lambda else "1800"
        default_pool_size = "5" if is_lambda else "10"
        default_max_overflow = "10" if is_lambda else "20"
        # Connection pooling optimizations for PostgreSQL
        engine_kwargs.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", default_pool_size)),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", default_max_overflow)),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", default_pool_recycle)),
        })

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **engine_kwargs,
    )

    if db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if hasattr(dbapi_connection, "cursor"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return engine


Base = declarative_base()

# Global default engine and session factory
_default_engine: Optional[Engine] = None
_default_sessionmaker: Optional[sessionmaker] = None


def get_engine(url: Optional[str] = None) -> Engine:
    global _default_engine, _default_sessionmaker
    target_url = url or get_database_url()
    if _default_engine is None or (url is not None and str(_default_engine.url) != target_url):
        _default_engine = create_engine_for_url(target_url)
        _default_sessionmaker = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=_default_engine,
        )
    return _default_engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    global _default_sessionmaker
    if engine is not None:
        return sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
    if _default_sessionmaker is None:
        get_engine()
    return _default_sessionmaker


@contextmanager
def get_db_session(session_factory: Optional[sessionmaker] = None) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    factory = session_factory or get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_health(engine: Optional[Engine] = None) -> bool:
    """Executes a lightweight query to verify active database connectivity."""
    eng = engine or get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def wait_for_db(engine: Optional[Engine] = None, max_retries: int = 15, delay: float = 0.5) -> bool:
    """
    Waits for the database to become reachable.
    Useful during container orchestration startup when PostgreSQL is initializing.
    """
    eng = engine or get_engine()
    for _ in range(max_retries):
        if check_db_health(eng):
            return True
        time.sleep(delay)
    return False


def init_db(engine: Optional[Engine] = None) -> None:
    """Create all database tables defined on Base metadata."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
