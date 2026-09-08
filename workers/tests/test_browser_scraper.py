from __future__ import annotations
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys

from workers.scrapers.browser_scraper import BrowserScraper
from workers.scrapers.base import ScrapedResult

@pytest.mark.asyncio
async def test_browser_scraper_mocked_playwright():
    scraper = BrowserScraper()
    # Mute the robots check for unit testing
    scraper.robots = AsyncMock()
    scraper.robots.can_fetch.return_value = True
    scraper.robots.get_crawl_delay.return_value = None

    with patch("playwright.async_api.async_playwright") as mock_playwright:
        mock_pw_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value = mock_pw_context
        mock_pw_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = AsyncMock()
        mock_browser.new_context.return_value.new_page.return_value = mock_page
        mock_page.goto.return_value = mock_response
        mock_response.status = 200
        mock_page.content.return_value = "<html><body>Browser Data</body></html>"
        
        result = await scraper.scrape("https://example.com")
        assert result.status_code == 200
        assert "Browser Data" in result.html
        assert result.url == "https://example.com"
        mock_page.goto.assert_called_once()

@pytest.mark.asyncio
async def test_robots_txt_enforcement():
    scraper = BrowserScraper()
    scraper.robots = AsyncMock()
    scraper.robots.can_fetch.return_value = False
    
    result = await scraper.scrape("https://example.com/disallowed")
    assert result.status_code == 403
    assert result.error == "Disallowed by robots.txt"

@pytest.mark.asyncio
async def test_resource_blocking():
    scraper = BrowserScraper(block_heavy_resources=True)
    scraper.robots = AsyncMock()
    scraper.robots.can_fetch.return_value = True
    scraper.robots.get_crawl_delay.return_value = None
    
    with patch("playwright.async_api.async_playwright") as mock_playwright:
        mock_pw_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value = mock_pw_context
        mock_pw_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = AsyncMock()
        mock_browser.new_context.return_value.new_page.return_value = mock_page
        mock_page.goto.return_value = AsyncMock(status=200)
        mock_page.content.return_value = "<html>Data</html>"
        
        await scraper.scrape("https://example.com")
        mock_page.route.assert_called()

@pytest.mark.asyncio
async def test_browser_scraper_retry_loop():
    scraper = BrowserScraper(max_retries=2)
    scraper.robots = AsyncMock()
    scraper.robots.can_fetch.return_value = True
    scraper.robots.get_crawl_delay.return_value = None
    
    with patch("playwright.async_api.async_playwright") as mock_playwright:
        mock_pw_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value = mock_pw_context
        mock_pw_context.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = AsyncMock()
        mock_browser.new_context.return_value.new_page.return_value = mock_page
        
        # Simulate a failure on the first goto, success on second
        mock_page.goto.side_effect = [Exception("Timeout"), AsyncMock(status=200)]
        mock_page.content.return_value = "<html>Retry Success</html>"
        
        # Mock asyncio.sleep so we don't actually wait during test
        with patch("asyncio.sleep", return_value=None):
            result = await scraper.scrape("https://example.com")
            
        assert result.status_code == 200
        assert "Retry Success" in result.html
        assert mock_page.goto.call_count == 2
