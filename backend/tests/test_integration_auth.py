"""Integration test for authentication endpoints."""
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_github_redirect():
    """Test GitHub OAuth redirect endpoint."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/auth/github")
        assert response.status_code == 307  # Temporary redirect
        # Should redirect to GitHub OAuth
        assert "github.com" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_auth_callback_missing_code():
    """Test OAuth callback without code."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/callback")
        # Should fail without code or handle gracefully
        assert response.status_code in [400, 422]  # Bad request or validation error


@pytest.mark.asyncio
async def test_me_endpoint_unauthorized():
    """Test /api/me endpoint without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/me")
        assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_me_endpoint_with_invalid_token():
    """Test /api/me endpoint with invalid token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401  # Unauthorized

