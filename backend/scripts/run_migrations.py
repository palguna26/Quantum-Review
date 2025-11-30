#!/usr/bin/env python
"""
Run Alembic migrations programmatically.
Useful when alembic CLI is not directly available in the environment.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command

def run_migrations():
    """Run Alembic migrations."""
    try:
        # Construct the path to alembic.ini
        alembic_ini = backend_dir / "alembic.ini"
        
        if not alembic_ini.exists():
            print(f"ERROR: alembic.ini not found at {alembic_ini}")
            return False
        
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini))
        
        # Set the sqlalchemy.url from environment or config
        # This ensures migrations use the correct DATABASE_URL
        from app.config import settings
        
        # Get the database URL and normalize it
        db_url = settings.database_url_sync
        if not db_url:
            print("ERROR: DATABASE_URL not set in environment or config")
            return False
        
        # Update Alembic config with the database URL
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        print(f"Running migrations against: {db_url.split('@')[1] if '@' in db_url else 'unknown host'}")
        print()
        
        # Run the upgrade to the latest revision
        command.upgrade(alembic_cfg, "head")
        
        print("\nMigrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
