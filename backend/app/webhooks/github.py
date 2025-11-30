"""GitHub webhook handler."""
import hmac
import hashlib
import json
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import Response
import redis.asyncio as aioredis
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()

# Global Redis client
redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature.
    
    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
    
    Returns:
        True if signature is valid
    """
    if not signature_header:
        return False
    
    # Extract signature (format: sha256=...)
    if not signature_header.startswith("sha256="):
        return False
    
    signature = signature_header[7:]  # Remove "sha256=" prefix
    
    # Compute expected signature
    expected_signature = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected_signature)


async def is_duplicate_delivery(delivery_id: str) -> bool:
    """Check if webhook delivery is duplicate.
    
    Args:
        delivery_id: X-GitHub-Delivery header value
    
    Returns:
        True if duplicate
    """
    await init_redis()
    
    if not redis_client:
        return False
    
    cache_key = f"webhook:delivery:{delivery_id}"
    
    # Check if exists
    exists = await redis_client.exists(cache_key)
    if exists:
        return True
    
    # Store with TTL
    await redis_client.setex(
        cache_key,
        settings.WEBHOOK_DELIVERY_CACHE_TTL_SECONDS,
        "1"
    )
    
    return False


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
):
    """Handle GitHub webhook events."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Get raw body
    body = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(body, x_hub_signature_256 or ""):
        logger.warning(f"Invalid webhook signature", extra={"request_id": request_id})
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Check for duplicate delivery
    if x_github_delivery and await is_duplicate_delivery(x_github_delivery):
        logger.info(
            f"Duplicate webhook delivery ignored",
            extra={"request_id": request_id, "delivery_id": x_github_delivery}
        )
        return Response(status_code=200, content="Duplicate delivery")
    
    # Parse payload
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON payload", extra={"request_id": request_id})
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = x_github_event or "unknown"
    
    logger.info(
        f"Received webhook event: {event_type}",
        extra={
            "request_id": request_id,
            "event_type": event_type,
            "delivery_id": x_github_delivery,
        }
    )
    
    # Enqueue background job based on event type
    from rq import Queue
    import redis
    
    redis_conn = redis.from_url(settings.REDIS_URL)
    queue = Queue("default", connection=redis_conn)
    
    # Route events to appropriate handlers
    if event_type == "installation":
        if payload.get("action") in ["created", "deleted"]:
            # Handle installation events
            queue.enqueue("app.workers.tasks.handle_installation", payload)
    
    elif event_type == "installation_repositories":
        if payload.get("action") in ["added", "removed"]:
            # Handle repository access changes
            queue.enqueue("app.workers.tasks.handle_installation_repositories", payload)
    
    elif event_type == "issues":
        if payload.get("action") in ["opened", "edited"]:
            # Generate checklist
            from app.workers.tasks import generate_checklist
            queue.enqueue(generate_checklist, payload)
            
            # Publish SSE event for real-time updates
            # TODO: Query users with access to this repo and publish events
            # For now, publish to all users (simplified)
            try:
                from app.utils.events import publish_repo_event
                repo = payload.get("repository", {})
                repo_id = repo.get("id")  # GitHub repo ID, not our DB ID
                await publish_repo_event(repo_id, "issue_updated", {
                    "action": payload.get("action"),
                    "issue_number": payload.get("issue", {}).get("number"),
                    "repo_full_name": repo.get("full_name"),
                })
            except Exception as e:
                logger.error(f"Failed to publish SSE event: {e}", exc_info=True)
    
    elif event_type == "pull_request":
        if payload.get("action") in ["opened", "synchronize"]:
            # Generate test manifest
            from app.workers.tasks import generate_test_manifest
            queue.enqueue(generate_test_manifest, payload)
        elif payload.get("action") == "closed":
            # Handle PR closure
            queue.enqueue("app.workers.tasks.handle_pr_closed", payload)
    
    elif event_type == "workflow_run":
        if payload.get("action") == "completed":
            # Process workflow run
            from app.workers.tasks import process_workflow_run
            queue.enqueue(process_workflow_run, payload)
    
    elif event_type in ["check_suite", "check_run"]:
        # Handle check events if needed
        logger.debug(f"Check event received: {event_type}", extra={"request_id": request_id})
    
    # Return 200 quickly
    return Response(status_code=200, content="OK")

