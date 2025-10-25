"""
Database configuration and session management for JARVIS 3.0
Handles PostgreSQL connection with pgvector support
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging
import time

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    poolclass=StaticPool if "sqlite" in settings.database_url else None,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for table introspection
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """
    Initialize database and create tables.
    This function should be called on application startup.
    """
    try:
        # Import all models to ensure they are registered with SQLAlchemy
        from ..models import user, document, conversation
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Initialize pgvector extension
        with engine.connect() as conn:
            # Create vector extension if not exists
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gin;")
            conn.commit()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """
    Close database connections.
    This function should be called on application shutdown.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


class DatabaseManager:
    """Database manager for advanced operations"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_factory()
    
    def execute_raw_sql(self, query: str, params: dict = None):
        """Execute raw SQL query"""
        with self.engine.connect() as conn:
            result = conn.execute(query, params or {})
            conn.commit()
            return result
    
    def check_connection(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> dict:
        """Get information about a specific table"""
        try:
            metadata.reflect(bind=self.engine, only=[table_name])
            table = metadata.tables.get(table_name)
            if table is not None:
                return {
                    "columns": [col.name for col in table.columns],
                    "primary_keys": [col.name for col in table.primary_key],
                    "indexes": [idx.name for idx in table.indexes]
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return {}


# Global database manager instance
db_manager = DatabaseManager()


# Database health check function
def health_check() -> dict:
    """Perform database health check"""
    try:
        start_time = time.time()
        is_healthy = db_manager.check_connection()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time_ms": round(response_time * 1000, 2),
            "database_url": settings.database_url.split("@")[-1],  # Hide credentials
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": 0,
        }