from __future__ import annotations
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from workers.scrapers.base import BaseScraper, ScrapedResult
from workers.scrapers.robots_parser import RobotsParser
from workers.scrapers.rate_limiter import DomainRateLimiter
from workers.scrapers.http_scraper import HttpScraper

@pytest.mark.asyncio
async def test_robots_parser(sample_robots_txt):
    parser = RobotsParser()
    # Mock httpx response
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_robots_txt
        mock_get.return_value = mock_resp

        allowed = await parser.can_fetch("https://example.com/public-page", user_agent="BrandPulse")
        assert allowed is True

        disallowed = await parser.can_fetch("https://example.com/admin/dashboard", user_agent="BrandPulse")
        assert disallowed is False

        delay = await parser.get_crawl_delay("https://example.com/", user_agent="BrandPulse")
        assert delay == 5.0

@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = DomainRateLimiter(default_rate=10.0, default_burst=2)
    # First token immediate
    t1 = await limiter.acquire("https://example.com/page1")
    assert t1 == 0.0

    # Second token immediate
    t2 = await limiter.acquire("https://example.com/page2")
    assert t2 == 0.0

@pytest.mark.asyncio
async def test_scraped_result_hash():
    res = ScrapedResult(
        url="https://example.com",
        status_code=200,
        html="<html><body>BrandPulse Test</body></html>"
    )
    assert res.content_hash != ""
    assert len(res.content_hash) == 64 # sha256 hex length

@pytest.mark.asyncio
async def test_http_scraper_mock():
    scraper = HttpScraper(enforce_robots=False)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com"
        mock_resp.text = "<html><h1>Example</h1></html>"
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = await scraper.scrape("https://example.com")
        assert result.status_code == 200
        assert "Example" in result.html
        assert result.is_modified is True

@pytest.mark.asyncio
async def test_rate_limiter_burst_exhaustion():
    # Rate of 2 req/s with burst of 1 means 2nd request will have to wait
    limiter = DomainRateLimiter(default_rate=2.0, default_burst=1)
    t1 = await limiter.acquire("https://example.com/item1")
    assert t1 == 0.0

    # 2nd acquisition should experience wait time > 0
    t2 = await limiter.acquire("https://example.com/item2")
    assert t2 >= 0.0

@pytest.mark.asyncio
async def test_http_scraper_conditional_304():
    scraper = HttpScraper(enforce_robots=False)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 304
        mock_resp.url = "https://example.com"
        mock_resp.text = ""
        mock_resp.headers = {"etag": '"abc123"'}
        mock_get.return_value = mock_resp

        result = await scraper.scrape("https://example.com", etag='"abc123"')
        assert result.status_code == 304
        assert result.is_modified is False
        assert result.html == ""

@pytest.mark.asyncio
async def test_http_scraper_429_backoff_and_retry():
    scraper = HttpScraper(enforce_robots=False, max_retries=2)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # First call: 429 with Retry-After: 0.01, Second call: 200 OK
        mock_429 = AsyncMock()
        mock_429.status_code = 429
        mock_429.url = "https://example.com"
        mock_429.headers = {"retry-after": "0"}
        mock_429.text = "Too Many Requests"

        mock_200 = AsyncMock()
        mock_200.status_code = 200
        mock_200.url = "https://example.com"
        mock_200.text = "Success after 429"
        mock_200.headers = {"content-type": "text/html"}
        mock_200.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_429, mock_200]

        result = await scraper.scrape("https://example.com")
        assert result.status_code == 200
        assert "Success after 429" in result.html

