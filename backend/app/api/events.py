"""Server-Sent Events (SSE) endpoint for real-time updates."""
import asyncio
import json
from typing import AsyncIterator
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
from app.config import get_settings
from app.adapters.db import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.logging_config import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()

# Global Redis client for pub/sub
redis_pubsub: aioredis.Redis = None


async def init_redis_pubsub():
    """Initialize Redis pub/sub client."""
    global redis_pubsub
    if redis_pubsub is None:
        redis_pubsub = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )


async def event_stream(user_id: int) -> AsyncIterator[str]:
    """Generate SSE event stream for user."""
    await init_redis_pubsub()
    
    if not redis_pubsub:
        logger.error("Redis pub/sub not initialized")
        yield f"data: {json.dumps({'type': 'error', 'message': 'SSE unavailable'})}\n\n"
        return
    
    # Create a channel for user-specific events
    channel = f"user:{user_id}:events"
    pubsub = redis_pubsub.pubsub()
    await pubsub.subscribe(channel)
    
    # Send initial connection event
    yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"
    
    try:
        while True:
            # Check for messages with timeout
            message = await asyncio.wait_for(pubsub.get_message(timeout=1.0), timeout=30.0)
            
            if message and message["type"] == "message":
                try:
                    event_data = json.loads(message["data"])
                    yield f"data: {json.dumps(event_data)}\n\n"
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in SSE event: {message['data']}")
            else:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
                
    except asyncio.TimeoutError:
        # Timeout - send ping to check if client is still connected
        yield f": ping\n\n"
    except Exception as e:
        logger.error(f"Error in event stream: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.get("/stream")
async def stream_events(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """SSE endpoint for real-time updates.
    
    Streams events to authenticated users including:
    - Issue created/updated
    - Checklist generated/updated
    - PR opened/validated
    - Health score updated
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return StreamingResponse(
        event_stream(current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )

