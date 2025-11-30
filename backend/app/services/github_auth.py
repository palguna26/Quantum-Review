"""GitHub App authentication and token management."""
import time
import jwt
from datetime import datetime, timedelta
from typing import Optional
import httpx
import redis.asyncio as aioredis
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global Redis client (will be initialized)
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
        logger.info("Redis client initialized")


async def close_redis() -> None:
    """Close Redis client."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis client closed")


def generate_app_jwt() -> str:
    """Generate JWT for GitHub App authentication.
    
    Returns:
        JWT token string
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued at time (1 minute ago to account for clock skew)
        "exp": now + (settings.GITHUB_APP_JWT_EXPIRATION_MINUTES * 60),
        "iss": settings.GITHUB_APP_ID,
    }
    
    token = jwt.encode(
        payload,
        settings.github_private_key_bytes,
        algorithm="RS256"
    )
    
    return token


async def get_installation_token(installation_id: int) -> Optional[str]:
    """Get installation access token, using cache if available.
    
    Args:
        installation_id: GitHub App installation ID
    
    Returns:
        Installation access token or None if failed
    """
    await init_redis()
    
    cache_key = f"gh:install:{installation_id}:token"
    cache_expiry_key = f"gh:install:{installation_id}:expires_at"
    
    # Check cache
    if redis_client:
        try:
            cached_token = await redis_client.get(cache_key)
            expires_at_str = await redis_client.get(cache_expiry_key)
            
            if cached_token and expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                # Refresh if expires within 5 minutes
                if expires_at > datetime.utcnow() + timedelta(minutes=5):
                    logger.debug(f"Using cached installation token for {installation_id}")
                    return cached_token
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
    
    # Generate new token
    app_jwt = generate_app_jwt()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            token = data["token"]
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            
            # Cache the token
            if redis_client:
                try:
                    ttl = int((expires_at - datetime.utcnow()).total_seconds())
                    if ttl > 0:
                        await redis_client.setex(cache_key, ttl, token)
                        await redis_client.setex(cache_expiry_key, ttl, expires_at.isoformat())
                except Exception as e:
                    logger.warning(f"Error caching token: {e}")
            
            logger.info(f"Generated new installation token for {installation_id}")
            return token
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get installation token: {e}")
            return None


def get_github_api_client(installation_id: Optional[int] = None) -> httpx.AsyncClient:
    """Get authenticated GitHub API client (synchronous factory).
    
    Note: For async usage, call get_installation_token first, then create client.
    
    Args:
        installation_id: Optional installation ID. If provided, uses installation token.
                         Otherwise, uses app JWT.
    
    Returns:
        Authenticated httpx client
    """
    if installation_id:
        # Note: This is a sync function, token should be fetched separately
        # For async usage, use get_installation_token_async pattern
        app_jwt = generate_app_jwt()
        auth_header = f"Bearer {app_jwt}"
    else:
        app_jwt = generate_app_jwt()
        auth_header = f"Bearer {app_jwt}"
    
    return httpx.AsyncClient(
        base_url=settings.GITHUB_API_BASE,
        headers={
            "Authorization": auth_header,
            "Accept": "application/vnd.github+json",
        },
        timeout=30.0,
    )


async def get_github_api_client_async(installation_id: Optional[int] = None) -> httpx.AsyncClient:
    """Get authenticated GitHub API client (async version).
    
    Args:
        installation_id: Optional installation ID. If provided, uses installation token.
                         Otherwise, uses app JWT.
    
    Returns:
        Authenticated httpx client
    """
    if installation_id:
        token = await get_installation_token(installation_id)
        if not token:
            raise ValueError(f"Failed to get installation token for {installation_id}")
        auth_header = f"token {token}"
    else:
        app_jwt = generate_app_jwt()
        auth_header = f"Bearer {app_jwt}"
    
    return httpx.AsyncClient(
        base_url=settings.GITHUB_API_BASE,
        headers={
            "Authorization": auth_header,
            "Accept": "application/vnd.github+json",
        },
        timeout=30.0,
    )

