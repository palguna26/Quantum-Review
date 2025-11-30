#!/usr/bin/env python
"""
Create all tables from SQLAlchemy models directly.
Use this when Alembic migrations have issues.
"""
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

async def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.config import get_settings
        from app.models.base import Base
        # Import all models to ensure they're registered
        import app.models  # noqa: F401
        
        settings = get_settings()
        
        # Create engine and normalize DATABASE_URL
        db_url = settings.DATABASE_URL
        if isinstance(db_url, str):
            db_url = db_url.strip('\"\'')
        
        print(f"Creating tables in database...")
        
        async_engine = create_async_engine(db_url, echo=False)
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await async_engine.dispose()
        
        print("✓ All tables created successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_all_tables())
    sys.exit(0 if success else 1)
