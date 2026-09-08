from __future__ import annotations
import asyncio
from urllib.parse import urlparse
from typing import Dict
import time
import logging

logger = logging.getLogger(__name__)

class DomainRateLimiter:
    """
    Per-domain asynchronous token-bucket rate limiter.
    Ensures scraping jobs do not overwhelm external target servers or trigger 429 bans.
    """
    def __init__(self, default_rate: float = 2.0, default_burst: int = 5):
        """
        :param default_rate: requests per second allowed per domain
        :param default_burst: maximum burst capacity
        """
        self.default_rate = default_rate
        self.default_burst = default_burst
        self._buckets: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    async def acquire(self, url: str, custom_delay: float | None = None) -> float:
        """
        Wait until allowed to fetch URL.
        Returns the duration waited in seconds.
        """
        domain = self._get_domain(url)
        async with self._lock:
            now = time.monotonic()
            rate = (1.0 / custom_delay) if custom_delay and custom_delay > 0 else self.default_rate
            burst = 1 if custom_delay else self.default_burst

            if domain not in self._buckets:
                self._buckets[domain] = {
                    "tokens": burst,
                    "last_updated": now,
                    "rate": rate,
                    "burst": burst
                }

            bucket = self._buckets[domain]
            # Refill tokens
            elapsed = now - bucket["last_updated"]
            bucket["tokens"] = min(bucket["burst"], bucket["tokens"] + elapsed * bucket["rate"])
            bucket["last_updated"] = now

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return 0.0

            # Calculate necessary sleep
            needed = 1.0 - bucket["tokens"]
            wait_time = needed / bucket["rate"]

        if wait_time > 0:
            logger.debug("Rate-limiting %s: sleeping for %.2fs", domain, wait_time)
            await asyncio.sleep(wait_time)
            async with self._lock:
                now = time.monotonic()
                bucket = self._buckets[domain]
                bucket["tokens"] = 0.0
                bucket["last_updated"] = now
            return wait_time

        return 0.0
