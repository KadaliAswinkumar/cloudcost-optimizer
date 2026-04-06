"""
Rate Limiter Middleware
Implements token bucket rate limiting using Redis.
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.cache import redis_client, CacheKeys


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Limits requests per client based on IP address.
    """
    
    def __init__(
        self,
        app,
        requests_per_window: int = None,
        window_seconds: int = None,
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window or settings.rate_limit_requests
        self.window_seconds = window_seconds or settings.rate_limit_window
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and apply rate limiting."""
        
        # Skip rate limiting for health checks and API documentation
        path = request.url.path
        if path.startswith("/health") or path in (
            "/docs",
            "/redoc",
            "/openapi.json",
            "/swagger",
        ) or path.startswith("/docs/") or path.startswith("/redoc/"):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_id)
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": reset_time,
                    "limit": self.requests_per_window,
                    "window_seconds": self.window_seconds,
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get real IP from proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(
        self,
        client_id: str,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Returns:
            (is_allowed, remaining_requests, seconds_until_reset)
        """
        if not redis_client:
            # Redis not available, allow all requests
            return True, self.requests_per_window, 0
        
        key = CacheKeys.rate_limit(client_id)
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        try:
            # Use Redis sorted set for sliding window
            pipe = redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, self.window_seconds)
            
            results = await pipe.execute()
            request_count = results[1]
            
            if request_count >= self.requests_per_window:
                # Get oldest request timestamp to calculate reset time
                oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + self.window_seconds - current_time
                else:
                    reset_time = self.window_seconds
                
                return False, 0, max(1, reset_time)
            
            remaining = self.requests_per_window - request_count - 1
            return True, remaining, self.window_seconds
            
        except Exception:
            # On error, allow the request
            return True, self.requests_per_window, 0

