"""
Redis Cache Service
Provides caching functionality for API responses and price data.
"""

import json
from typing import Any, Optional
from datetime import timedelta

import redis.asyncio as redis

from src.core.config import settings


class CacheService:
    """Redis cache service with JSON serialization."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = settings.redis_cache_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value, default=str)
        return await self.redis.setex(key, ttl, serialized)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return await self.redis.delete(key) > 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using SCAN."""
        count = 0
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                count += await self.redis.delete(*keys)
            
            if cursor == 0:
                break
        
        return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self.redis.exists(key) > 0
    
    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or set using factory function."""
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory() if callable(factory) else factory
        await self.set(key, value, ttl)
        return value
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        return await self.redis.incrby(key, amount)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key."""
        return await self.redis.expire(key, ttl)


# Cache key generators
class CacheKeys:
    """Cache key templates."""
    
    @staticmethod
    def instance_pricing(instance_type: str, region: str) -> str:
        return f"pricing:{region}:{instance_type}"
    
    @staticmethod
    def spot_price(instance_type: str, region: str) -> str:
        return f"spot:{region}:{instance_type}"
    
    @staticmethod
    def all_instances() -> str:
        return "instances:all"
    
    @staticmethod
    def region_pricing(region: str) -> str:
        return f"pricing:{region}:all"
    
    @staticmethod
    def recommendations(workload_hash: str) -> str:
        return f"recommendations:{workload_hash}"
    
    @staticmethod
    def rate_limit(client_id: str) -> str:
        return f"ratelimit:{client_id}"


# Global redis client (initialized in main.py)
redis_client: Optional[redis.Redis] = None
cache_service: Optional[CacheService] = None


async def init_redis() -> redis.Redis:
    """Initialize Redis connection."""
    global redis_client, cache_service
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    cache_service = CacheService(redis_client)
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get the global Redis client instance.
    Returns None if Redis is not initialized or not available.
    """
    global redis_client
    if redis_client:
        try:
            # Test connection
            await redis_client.ping()
            return redis_client
        except Exception:
            return None
    return None

