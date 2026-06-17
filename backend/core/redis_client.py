"""Redis async client with in-memory fallback."""
import json
import asyncio
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from core.config import settings

logger = logging.getLogger(__name__)
_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        try:
            _client = aioredis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await _client.ping()
            logger.info(f"Redis connected at {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Using in-memory fallback.")
            _client = _InMemoryFallback()
    return _client


async def publish(channel: str, message: dict):
    client = await get_redis()
    try:
        await client.publish(channel, json.dumps(message))
    except Exception as e:
        logger.error(f"Publish error on {channel}: {e}")


async def set_cache(key: str, value: Any, expire: int = 300):
    client = await get_redis()
    try:
        await client.setex(key, expire, json.dumps(value, default=str))
    except Exception as e:
        logger.error(f"Cache set error [{key}]: {e}")


async def get_cache(key: str) -> Optional[Any]:
    client = await get_redis()
    try:
        val = await client.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def delete_cache(key: str):
    client = await get_redis()
    try:
        await client.delete(key)
    except Exception:
        pass


class _InMemoryFallback:
    """Minimal in-memory fallback when Redis is unavailable."""
    def __init__(self):
        self._store: dict = {}

    async def ping(self): return True
    async def setex(self, key, expire, value): self._store[key] = value
    async def get(self, key): return self._store.get(key)
    async def delete(self, key): self._store.pop(key, None)
    async def publish(self, channel, message): pass

    def pubsub(self):
        class _PS:
            async def subscribe(self, ch): pass
            async def listen(self):
                # Never yields — prevents infinite loops in fallback
                return
                yield  # make it an async generator
        return _PS()
