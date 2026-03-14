import json
from functools import lru_cache
from typing import Any

# In-memory cache as fallback (no Redis dependency required)
_cache: dict[str, Any] = {}
_redis_client = None


async def get_redis():
    """Get Redis client, falling back to in-memory cache."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as aioredis
        from app.config import get_settings
        settings = get_settings()
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await _redis_client.ping()
        return _redis_client
    except Exception:
        return None


async def cache_get(key: str) -> Any | None:
    """Get value from cache."""
    client = await get_redis()
    if client:
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception:
            pass
    return _cache.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL (seconds)."""
    client = await get_redis()
    if client:
        try:
            await client.set(key, json.dumps(value, default=str), ex=ttl)
            return
        except Exception:
            pass
    _cache[key] = value


async def cache_invalidate(pattern: str) -> None:
    """Invalidate cache entries matching pattern."""
    client = await get_redis()
    if client:
        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
            return
        except Exception:
            pass
    # In-memory fallback
    to_delete = [k for k in _cache if pattern.replace("*", "") in k]
    for k in to_delete:
        del _cache[k]
