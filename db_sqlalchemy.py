from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config import settings


# Create SQLAlchemy engine using DATABASE_URL from settings
DATABASE_URL = settings.DATABASE_URL

# Recommended pool size tuning for web + worker processes
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session():
    """Yield a SQLAlchemy session (use as context manager)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
