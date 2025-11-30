"""Authentication endpoints."""
import jwt
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.adapters.db import get_db
from app.models.user import User
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


def create_session_token(user_id: int) -> str:
    """Create JWT session token for user.
    
    Args:
        user_id: User ID
    
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_EXPIRATION_DAYS),
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def get_user_from_token(token: str) -> Optional[int]:
    """Extract user ID from session token.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from session cookie or Bearer token.
    
    Supports both cookie-based and Bearer token authentication.
    
    Args:
        request: FastAPI request
        db: Database session
    
    Returns:
        User object or None if not authenticated
    """
    token = None
    
    # Check for Bearer token in Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
    else:
        # Fall back to cookie
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if not token:
        return None
    
    user_id = get_user_from_token(token)
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@router.get("/github")
async def github_oauth_start(request: Request):
    """Start GitHub OAuth flow."""
    # GitHub redirects back to backend callback, then backend redirects to frontend
    # Use configured backend origin for the OAuth callback
    backend_url = getattr(settings, "BACKEND_ORIGIN", None) or "http://127.0.0.1:8000"
    redirect_uri = f"{backend_url.rstrip('/')}/auth/callback"
    
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=read:user user:email"
    )
    return RedirectResponse(url=github_oauth_url)


@router.get("/callback")
async def github_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback.

    This endpoint accepts an optional `code` query param from GitHub. If `code`
    is missing we return a 400 with a clear message. When a valid `code` is
    provided we exchange it for an access token, create/update the user,
    create a session JWT, set it as a cookie on the redirect response and
    redirect the browser to the frontend callback with `?token=`.
    """
    if code is None:
        raise HTTPException(status_code=400, detail="Missing `?code=` from GitHub OAuth callback")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10.0,
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
            timeout=10.0,
        )
        user_response.raise_for_status()
        github_user = user_response.json()

        # Get user email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"},
            timeout=10.0,
        )
        emails = email_response.json() if email_response.status_code == 200 else []
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)

    # Create or update user in database
    github_id = github_user["id"]
    username = github_user["login"]
    avatar_url = github_user.get("avatar_url")

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = username
        user.email = primary_email or user.email
        user.avatar_url = avatar_url or user.avatar_url
    else:
        # Create new user
        user = User(
            github_id=github_id,
            username=username,
            email=primary_email,
            avatar_url=avatar_url,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create session token
    session_token = create_session_token(user.id)

    # Build frontend callback from configured FRONTEND_ORIGIN
    frontend_origin = settings.FRONTEND_ORIGIN or (settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:8080")
    frontend_callback = f"{frontend_origin.rstrip('/')}/auth/callback?token={session_token}"

    # Attach cookie to redirect response so browser receives both cookie and
    # the frontend redirect URL in one response.
    redirect = RedirectResponse(url=frontend_callback, status_code=302)
    redirect.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=settings.JWT_EXPIRATION_DAYS * 24 * 60 * 60,
    )

    return redirect

