"""Application configuration from environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # GitHub App Configuration (Required for webhook processing)
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None  # PEM format, may contain \n
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # GitHub OAuth Configuration (Required for user authentication)
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None
    
    # Database Configuration (Required)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/quantumreview"
    
    # Redis Configuration (Required for background jobs)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Configuration (Required - should be set in production)
    JWT_SECRET: str = "dev-secret-key-change-in-production-min-32-chars"
    
    # LLM Configuration (optional)
    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    
    # Deployment Configuration
    RENDER: bool = False
    
    # Application Configuration
    APP_NAME: str = "QuantumReview"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS / Origins Configuration
    # For local development we expect the frontend to run on port 8080.
    CORS_ORIGINS: list[str] = ["http://localhost:8080"]
    FRONTEND_ORIGIN: str = "http://localhost:8080"
    BACKEND_ORIGIN: str = "http://localhost:8000"
    
    # Session Configuration
    SESSION_COOKIE_NAME: str = "quantum_session"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False  # Allow http://127.0.0.1
    SESSION_COOKIE_SAMESITE: str = "Lax"  # Allow redirects
    JWT_EXPIRATION_DAYS: int = 7
    JWT_REFRESH_THRESHOLD_HOURS: int = 24
    
    # GitHub API Configuration
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_APP_JWT_EXPIRATION_MINUTES: int = 10
    
    # Redis Cache Configuration
    INSTALLATION_TOKEN_CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    WEBHOOK_DELIVERY_CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Optional MongoDB (for flexible document storage / Atlas)
    MONGODB_URI: Optional[str] = None
    
    @property
    def github_private_key_bytes(self) -> bytes:
        """Return the GitHub private key as bytes, handling newlines."""
        return self.GITHUB_PRIVATE_KEY.encode('utf-8').replace(b'\\n', b'\n')
    
    @property
    def database_url_sync(self) -> str:
        """Return synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

