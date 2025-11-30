from typing import Any, Dict, Optional
import httpx

from app.services.github_auth import get_github_api_client_async, get_installation_token
from app.logging_config import get_logger

logger = get_logger(__name__)


async def list_installation_repositories(installation_id: int) -> Dict[str, Any]:
    client = await get_github_api_client_async(installation_id)
    try:
        resp = await client.get("/installation/repositories")
        resp.raise_for_status()
        return resp.json()
    finally:
        await client.aclose()


async def create_installation_access_token(installation_id: int) -> Optional[str]:
    try:
        token = await get_installation_token(installation_id)
        return token
    except Exception as e:
        logger.error(f"Failed to create installation access token: {e}", exc_info=True)
        return None


async def get_authenticated_user(oauth_token: str) -> Optional[Dict[str, Any]]:
    async with httpx.AsyncClient(base_url="https://api.github.com") as client:
        try:
            resp = await client.get("/user", headers={"Authorization": f"token {oauth_token}"})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch authenticated user: {e}")
            return None

