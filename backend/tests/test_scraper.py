import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.scraper import ScraperService


@pytest.mark.asyncio
async def test_scrape_url_returns_text():
    service = ScraperService()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><h1>AI PM</h1><p>We need a product manager.</p></body></html>"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        result = await service.scrape_url("https://example.com/job")
        assert "product manager" in result.lower()
