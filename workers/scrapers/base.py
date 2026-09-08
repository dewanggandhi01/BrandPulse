from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hashlib
import time
import random

USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

@dataclass
class ScrapedResult:
    url: str
    status_code: int
    html: str
    headers: Dict[str, str] = field(default_factory=dict)
    content_hash: str = ""
    is_modified: bool = True
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash and self.html:
            self.content_hash = hashlib.sha256(self.html.encode("utf-8")).hexdigest()

class BaseScraper(ABC):
    """
    Abstract Base Scraper enforcing:
    1. Provenance tracking (source URL, timestamp, elapsed ms, hash)
    2. Exponential backoff and retry safety
    3. Proper HTTP header spoofing / identification
    4. Explicit error handling and timeout guarantees
    """
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 BrandPulse/1.0"
    )

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        proxy_url: Optional[str] = None,
        proxy_pool: Optional[list[str]] = None
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.proxy_url = proxy_url
        self.proxy_pool = proxy_pool

    def rotate_user_agent(self) -> str:
        return random.choice(USER_AGENT_POOL)

    def get_proxy(self) -> str | None:
        if self.proxy_pool:
            return random.choice(self.proxy_pool)
        return self.proxy_url

    def get_default_headers(self) -> Dict[str, str]:
        ua = self.user_agent or self.rotate_user_agent()
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    @abstractmethod
    async def scrape(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        **kwargs: Any
    ) -> ScrapedResult:
        """Execute extraction and return standardized ScrapedResult."""
        pass
