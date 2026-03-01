"""Database configuration and session management."""

import os
import logging
from pathlib import Path
from typing import Generator, Optional
from sqlalchemy import create_engine, inspect, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from .models import Base

logger = logging.getLogger(__name__)

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker[Session]] = None
_db_initialized: bool = False


def get_database_url() -> str:
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def is_database_available() -> bool:
    global engine

    if engine is None:
        return False

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.debug(f"Database not available: {e}")
        return False


def run_migrations() -> None:
    """Run Alembic migrations to bring the database schema up to date.

    Auto-detects pre-Alembic databases (app tables exist but no alembic_version
    table) and stamps them with the current head revision so that future
    migrations apply cleanly.
    """
    from alembic.config import Config
    from alembic import command

    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))

    # Stamp pre-Alembic databases so migrations don't try to recreate tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    has_app_tables = "conversations" in existing_tables
    has_alembic = "alembic_version" in existing_tables

    if has_app_tables and not has_alembic:
        logger.info("Pre-Alembic database detected — stamping with current head.")
        command.stamp(alembic_cfg, "head")
    else:
        command.upgrade(alembic_cfg, "head")


def init_database() -> bool:
    global engine, SessionLocal, _db_initialized

    if _db_initialized and engine is not None and is_database_available():
        return True

    try:
        if engine is None:
            engine = create_engine(
                get_database_url(),
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,
                connect_args={"connect_timeout": 5},
            )

        if SessionLocal is None:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        if not is_database_available():
            logger.warning("Database is not available. Will retry on next access.")
            return False

        try:
            run_migrations()
        except Exception as e:
            logger.warning(f"Alembic migration failed: {e}")
            logger.warning("Falling back to create_all for table creation.")
            Base.metadata.create_all(bind=engine)

        _db_initialized = True
        return True

    except OperationalError as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Chatbot will run without database persistence.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def get_db() -> Generator[Session, None, None]:
    if not _db_initialized:
        init_database()

    if SessionLocal is None:
        raise RuntimeError(
            "Database session factory not initialized. Is PostgreSQL running?"
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
