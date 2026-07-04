"""Async in-memory caching for CityPulse Health."""
import time
from typing import Any, Callable, Dict

from app.core.config import logger


class AsyncTTLCache:
    """Simple asynchronous TTL cache."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_or_set(self, key: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Get from cache if valid, otherwise compute and store."""
        now = time.time()

        if key in self._cache:
            entry = self._cache[key]
            if now - entry["timestamp"] < self.ttl:
                logger.info("Cache hit for key: %s", key)
                return entry["value"]
            logger.info("Cache expired for key: %s", key)
        else:
            logger.info("Cache miss for key: %s", key)

        value = await func(*args, **kwargs)

        self._cache[key] = {
            "value": value,
            "timestamp": now
        }
        return value

# Singleton instance for the application (5-minute TTL)
briefing_cache = AsyncTTLCache(ttl_seconds=300)
