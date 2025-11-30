r"""Create the configured database if it doesn't exist.

Usage:
    # Ensure DATABASE_URL is set in the shell or backend/.env contains the right value
    python backend\scripts\create_database.py

This script uses the repo's settings to determine the target DB name,
connects to the maintenance 'postgres' database, checks if the target
database exists, and creates it if missing.
"""
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine
from pathlib import Path
import sys
import os

# Make repo importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings

settings = get_settings()

# Prefer environment override
env_db = os.environ.get("DATABASE_URL")
db_url = env_db or settings.database_url_sync

if not db_url:
    print("No DATABASE_URL found in environment or settings. Aborting.")
    raise SystemExit(1)

url = make_url(db_url)
target_db = url.database

if not target_db:
    print("Could not determine target database from DATABASE_URL. Aborting.")
    raise SystemExit(1)

print(f"Target database: {target_db}")

# Build maintenance URL (connect to 'postgres' database)
maint_url = url.set(database="postgres")

try:
    # Convert URL to string; avoid exposing credentials in logs by showing
    # only host:port/database portion.
    maint_str = str(maint_url)
    host_part = maint_str.split('@')[-1]
    print(f"Connecting to server at: {host_part}")
except Exception:
    print("Connecting to server (host information unavailable)")

engine = create_engine(maint_url)

with engine.connect() as conn:
    # Check if database exists
    exists = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :d"), {"d": target_db}
    ).scalar()

    if exists:
        print(f"Database '{target_db}' already exists. No action taken.")
    else:
        print(f"Creating database '{target_db}'...")
        # Note: CREATE DATABASE cannot run inside a transaction block
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            text(f"CREATE DATABASE \"{target_db}\"")
        )
        print("Database created.")

print("Done.")
