"""
EDQMP Database Connection
Supabase client and SQLAlchemy engine setup
"""

from typing import Optional, Generator
from functools import lru_cache
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class DatabaseManager:
    """Manages database connections for EDQMP"""
    
    _supabase_client: Optional[Client] = None
    _engine = None
    _session_local = None
    
    @classmethod
    def get_supabase_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._supabase_client is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Set SUPABASE_URL and SUPABASE_KEY environment variables."
                )
            cls._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Supabase client initialized")
        return cls._supabase_client
    
    @classmethod
    def get_supabase_admin_client(cls) -> Client:
        """Get Supabase client with service role key for admin operations"""
        if not settings.supabase_service_key:
            logger.warning("Service key not set, using regular client")
            return cls.get_supabase_client()
        return create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    @classmethod
    def get_engine(cls):
        """Get or create SQLAlchemy engine for direct DB access"""
        if cls._engine is None:
            if settings.database_url:
                cls._engine = create_engine(
                    settings.database_url,
                    pool_size=settings.db_pool_size,
                    max_overflow=settings.db_max_overflow,
                    pool_pre_ping=True,
                    echo=settings.debug
                )
                logger.info("SQLAlchemy engine initialized")
            else:
                logger.warning("DATABASE_URL not set, SQLAlchemy unavailable")
        return cls._engine
    
    @classmethod
    def get_session_local(cls):
        """Get session factory"""
        if cls._session_local is None and cls.get_engine():
            cls._session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls.get_engine()
            )
        return cls._session_local


def get_supabase() -> Client:
    """Dependency for getting Supabase client"""
    return DatabaseManager.get_supabase_client()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    session_local = DatabaseManager.get_session_local()
    if session_local is None:
        raise RuntimeError("Database not configured")
    
    db = session_local()
    try:
        yield db
    finally:
        db.close()


# Initialize on import (optional, for eager loading)
@lru_cache()
def init_database():
    """Initialize database connections"""
    try:
        supabase = DatabaseManager.get_supabase_client()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
