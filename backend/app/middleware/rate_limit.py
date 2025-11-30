"""Rate limiting middleware."""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import get_logger

logger = get_logger(__name__)

# Simple in-memory rate limiter
# In production, use Redis-based rate limiting
_rate_limit_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware.
    
    Limits requests per IP address.
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get rate limit key
        key = f"rate_limit:{client_ip}"
        
        # Check current rate
        count, window_start = _rate_limit_store[key]
        current_time = time.time()
        
        # Reset window if expired
        if current_time - window_start >= self.window_seconds:
            count = 0
            window_start = current_time
        
        # Check if limit exceeded
        if count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute."
            )
        
        # Increment counter
        count += 1
        _rate_limit_store[key] = (count, window_start)
        
        # Clean up old entries (simple cleanup every 100 requests)
        if count == 1 and len(_rate_limit_store) > 1000:
            self._cleanup_old_entries(current_time)
        
        # Process request
        response = await call_next(request)
        return response
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than window."""
        keys_to_remove = [
            key for key, (count, window_start) in _rate_limit_store.items()
            if current_time - window_start >= self.window_seconds
        ]
        for key in keys_to_remove:
            del _rate_limit_store[key]

