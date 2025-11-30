"""Migrate existing checklist data from Postgres to MongoDB.

Usage:
  # Ensure DATABASE_URL and MONGODB_URI are set in the shell (or backend/.env)
  python backend\scripts\migrate_checklists_to_mongo.py

This script is idempotent and will upsert checklist documents by issue id.
"""
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.logging_config import get_logger
from app.adapters.db import init_db, async_session_maker
from app.adapters.mongo import init_mongo, get_collection, close_mongo
from sqlalchemy import select
from app.models.issue import Issue

logger = get_logger(__name__)
settings = get_settings()

async def migrate():
    if not settings.MONGODB_URI:
        print("MONGODB_URI not configured; aborting migration.")
        return

    await init_db()
    await init_mongo()

    coll = get_collection("checklists")
    migrated = 0

    async with async_session_maker() as session:
        result = await session.execute(select(Issue))
        for issue in result.scalars():
            checklist = getattr(issue, "checklist_json", None)
            if not checklist:
                continue
            doc = {
                "issue_id": issue.id,
                "issue_number": issue.issue_number,
                "repo_id": issue.repo_id,
                "title": issue.title,
                "checklist": checklist,
            }
            await coll.update_one({"issue_id": issue.id}, {"$set": doc}, upsert=True)
            migrated += 1

    await close_mongo()
    print(f"Migrated {migrated} issue checklists to MongoDB")

if __name__ == "__main__":
    asyncio.run(migrate())
