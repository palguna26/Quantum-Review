"""Utility functions for publishing SSE events."""
import json
import redis.asyncio as aioredis
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
_redis_client: aioredis.Redis = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client for pub/sub."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


async def publish_event(user_id: int, event_type: str, data: dict):
    """Publish an SSE event to a user's channel.
    
    Args:
        user_id: User ID to send event to
        event_type: Type of event (e.g., 'issue_updated', 'checklist_ready')
        data: Event payload
    """
    try:
        client = await get_redis_client()
        channel = f"user:{user_id}:events"
        event = {
            "type": event_type,
            "data": data,
            "timestamp": None  # Will be set by backend if needed
        }
        await client.publish(channel, json.dumps(event))
        logger.debug(f"Published event to {channel}: {event_type}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}", exc_info=True)


async def publish_repo_event(repo_id: int, event_type: str, data: dict):
    """Publish an event to all users with access to a repo.
    
    Note: This is a simplified version. In production, you'd want to:
    1. Query users with access to the repo
    2. Publish to each user's channel
    
    Args:
        repo_id: Repository ID
        event_type: Type of event
        data: Event payload
    """
    try:
        client = await get_redis_client()
        channel = "broadcast:events"
        event = {
            "type": event_type,
            "data": {**data, "repo_id": repo_id},
            "timestamp": None,
        }
        await client.publish(channel, json.dumps(event))
        logger.debug(f"Published broadcast repo event {event_type} for repo {repo_id}")
    except Exception as e:
        logger.error(f"Failed to publish repo event: {e}", exc_info=True)

