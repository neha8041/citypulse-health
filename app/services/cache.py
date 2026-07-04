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
                logger.info(f"Cache hit for key: {key}")
                return entry["value"]
            logger.info(f"Cache expired for key: {key}")
        else:
            logger.info(f"Cache miss for key: {key}")

        value = await func(*args, **kwargs)

        self._cache[key] = {
            "value": value,
            "timestamp": now
        }
        return value

# Singleton instance for the application (5-minute TTL)
briefing_cache = AsyncTTLCache(ttl_seconds=300)
