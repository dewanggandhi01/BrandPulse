from __future__ import annotations
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from workers.scrapers.api_scraper import ApiScraper

@pytest.mark.asyncio
async def test_api_scraper_get_request():
    scraper = ApiScraper()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data": "test"}'
        mock_resp.url = "https://api.example.com/v1/data"
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"data": "test"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = await scraper.scrape("https://api.example.com/v1/data")
        assert result.status_code == 200
        assert '{"data": "test"}' in result.html
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_api_scraper_post_request():
    scraper = ApiScraper()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.text = '{"created": true}'
        mock_resp.url = "https://api.example.com/v1/data"
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"created": True}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        payload = {"name": "test"}
        result = await scraper.scrape("https://api.example.com/v1/data", method="POST", payload=payload)
        
        assert result.status_code == 201
        assert '{"created": true}' in result.html
        mock_post.assert_called_once()
        kwargs = mock_post.call_args.kwargs
        assert kwargs.get("json") == payload

@pytest.mark.asyncio
async def test_api_scraper_bearer_token():
    scraper = ApiScraper(auth_token="secret-token-123")
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"auth": "success"}'
        mock_resp.url = "https://api.example.com/secure"
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"auth": "success"}
        mock_get.return_value = mock_resp

        await scraper.scrape("https://api.example.com/secure")
        
        kwargs = mock_get.call_args.kwargs
        headers = kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer secret-token-123"

@pytest.mark.asyncio
async def test_api_scraper_304_not_modified():
    scraper = ApiScraper()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 304
        mock_resp.text = ""
        mock_resp.url = "https://api.example.com/data"
        mock_resp.headers = {"etag": '"xyz789"'}
        mock_get.return_value = mock_resp

        result = await scraper.scrape("https://api.example.com/data", etag='"xyz789"')
        assert result.status_code == 304
        assert result.is_modified is False
        assert result.html == ""

@pytest.mark.asyncio
async def test_api_scraper_retry_on_429():
    scraper = ApiScraper(max_retries=2)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"retry-after": "0"}
        mock_429.text = "Rate Limited"

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.text = '{"success": true}'
        mock_200.url = "https://api.example.com/data"
        mock_200.headers = {}
        mock_200.json.return_value = {"success": True}
        mock_200.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_429, mock_200]

        with patch("asyncio.sleep", return_value=None):
            result = await scraper.scrape("https://api.example.com/data")
            
        assert result.status_code == 200
        assert '{"success": true}' in result.html
        assert mock_get.call_count == 2
