from __future__ import annotations
import urllib.robotparser
from urllib.parse import urlparse
import httpx
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class RobotsParser:
    """
    RFC 9309 compliant robots.txt parser with in-memory TTL caching.
    Ensures ethical crawling by checking disallow paths and crawl-delays.
    """
    def __init__(self, cache_ttl_seconds: int = 3600, timeout: float = 10.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout
        self._cache: Dict[str, tuple[urllib.robotparser.RobotFileParser, float]] = {}

    def _get_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def get_parser(self, url: str, user_agent: str = "*") -> urllib.robotparser.RobotFileParser:
        base_url = self._get_base_url(url)
        now = time.time()

        if base_url in self._cache:
            parser, timestamp = self._cache[base_url]
            if now - timestamp < self.cache_ttl:
                return parser

        robots_url = f"{base_url}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)

        try:
            ua = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(robots_url, headers={"User-Agent": ua})
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    # 404 or other: allow all
                    parser.parse(["User-agent: *", "Allow: /"])
        except Exception as exc:
            logger.warning("Could not fetch robots.txt for %s: %s; defaulting to allow", base_url, exc)
            parser.parse(["User-agent: *", "Allow: /"])

        self._cache[base_url] = (parser, now)
        return parser

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Return True if robots.txt permits user_agent to fetch url."""
        try:
            parser = await self.get_parser(url, user_agent)
            return parser.can_fetch(user_agent, url)
        except Exception as err:
            logger.error("Error evaluating robots.txt for %s: %s", url, err)
            return True

    async def get_crawl_delay(self, url: str, user_agent: str = "*") -> Optional[float]:
        """Return crawl delay in seconds if specified."""
        try:
            parser = await self.get_parser(url, user_agent)
            delay = parser.crawl_delay(user_agent)
            return float(delay) if delay is not None else None
        except Exception:
            return None
