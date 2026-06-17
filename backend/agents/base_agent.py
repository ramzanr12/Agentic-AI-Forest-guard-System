"""Base agent with async lifecycle, Redis pub/sub, caching."""
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from core.redis_client import publish, set_cache, get_cache
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._running = False
        self._tasks = []

    async def start(self):
        self._running = True
        self.logger.info(f"[{self.name}] started")
        await self.on_start()

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self.logger.info(f"[{self.name}] stopped")

    async def on_start(self):
        pass

    @abstractmethod
    async def run(self):
        pass

    async def emit(self, channel: str, message: Dict[str, Any]):
        message["_agent"] = self.name
        await publish(channel, message)

    async def cache_set(self, key: str, value: Any, expire: int = 300):
        await set_cache(f"{self.name}:{key}", value, expire)

    async def cache_get(self, key: str) -> Optional[Any]:
        return await get_cache(f"{self.name}:{key}")

    def spawn(self, coro):
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t
