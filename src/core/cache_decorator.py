"""
Cache decorator for API endpoints
Provides simple Redis-based caching with automatic serialization.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from src.core.cache import get_redis_client

logger = logging.getLogger(__name__)


def cache_response(
    ttl: int = 300,  # 5 minutes default
    key_prefix: str = "api",
    exclude_keys: Optional[list] = None,
):
    """
    Decorator to cache API endpoint responses in Redis.
    
    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        key_prefix: Prefix for cache keys
        exclude_keys: Parameter names to exclude from cache key generation
        
    Example:
        @cache_response(ttl=600, key_prefix="recommendations")
        async def get_recommendations(params):
            # ... expensive operation ...
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            redis = await get_redis_client()
            
            # If Redis is not available, skip caching
            if redis is None:
                logger.warning("Redis not available, skipping cache")
                return await func(*args, **kwargs)
            
            # Generate cache key from function args
            cache_key = _generate_cache_key(
                func.__name__,
                args,
                kwargs,
                key_prefix,
                exclude_keys or []
            )
            
            try:
                # Try to get from cache
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"Cache HIT: {cache_key[:50]}...")
                    return json.loads(cached)
                
                # Cache miss - execute function
                logger.info(f"Cache MISS: {cache_key[:50]}...")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error: {e}, falling back to direct execution")
                # If cache fails, fall back to direct execution
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def _generate_cache_key(
    func_name: str,
    args: tuple,
    kwargs: dict,
    prefix: str,
    exclude_keys: list
) -> str:
    """
    Generate a consistent cache key from function arguments.
    
    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments
        prefix: Cache key prefix
        exclude_keys: Keys to exclude from cache key
        
    Returns:
        Cache key string
    """
    # Filter out excluded keys
    filtered_kwargs = {
        k: v for k, v in kwargs.items()
        if k not in exclude_keys
    }
    
    # Create a deterministic representation
    cache_data = {
        "func": func_name,
        "args": [_serialize_arg(arg) for arg in args],
        "kwargs": {k: _serialize_arg(v) for k, v in filtered_kwargs.items()},
    }
    
    # Generate hash
    cache_str = json.dumps(cache_data, sort_keys=True, default=str)
    cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()[:16]
    
    return f"{prefix}:{func_name}:{cache_hash}"


def _serialize_arg(arg: Any) -> Any:
    """
    Serialize an argument for cache key generation.
    Handles common types like objects with .dict() method (Pydantic models).
    """
    if hasattr(arg, "dict"):
        return arg.dict()
    elif hasattr(arg, "__dict__"):
        return {k: v for k, v in arg.__dict__.items() if not k.startswith("_")}
    return arg


async def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "recommendations:*")
        
    Returns:
        Number of keys deleted
    """
    redis = await get_redis_client()
    if redis is None:
        return 0
    
    try:
        keys = []
        async for key in redis.scan_iter(pattern):
            keys.append(key)
        
        if keys:
            deleted = await redis.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0
