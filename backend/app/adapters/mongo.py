from typing import Optional
from app.config import get_settings

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore
except Exception:
    AsyncIOMotorClient = None  # type: ignore
    AsyncIOMotorDatabase = None  # type: ignore

try:
    from pymongo.uri_parser import parse_uri
except Exception:
    parse_uri = None

settings = get_settings()
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_mongo() -> None:
    global _client, _db
    uri = settings.MONGODB_URI
    if not uri:
        return
    if AsyncIOMotorClient is None:
        return
    _client = AsyncIOMotorClient(uri)

    # Determine DB name from URI if present, otherwise default
    dbname = None
    try:
        if parse_uri:
            parsed = parse_uri(uri)
            dbname = parsed.get("database")
    except Exception:
        dbname = None

    if not dbname:
        dbname = "quantumreview"

    _db = _client[dbname]


async def close_mongo() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_mongo_db() -> Optional[AsyncIOMotorDatabase]:
    return _db


def get_collection(name: str):
    if _db is None:
        raise RuntimeError("MongoDB not initialized")
    return _db[name]
