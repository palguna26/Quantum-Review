"""Database adapter with async SQLAlchemy."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.models.base import Base
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global engine and session factory
engine = None
async_session_maker = None


async def init_db() -> None:
    """Initialize database connection pool."""
    global engine, async_session_maker
    
    if engine is None:
        # Normalize DATABASE_URL: strip surrounding quotes if present (handles
        # values like '"postgresql+asyncpg://..."' from .env files).
        db_url = settings.DATABASE_URL
        if isinstance(db_url, str):
            db_url = db_url.strip('\"\'')

        engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            poolclass=NullPool if settings.DEBUG else None,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Database connection pool initialized")


async def close_db() -> None:
    """Close database connection pool."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection pool closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    if async_session_maker is None:
        from app.adapters.db import init_db
        await init_db()
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables (for testing or initial setup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

