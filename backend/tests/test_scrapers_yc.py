import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.scrapers.yc import YCScraper


YC_SAMPLE_HTML = """
<html><body>
<div class="job-listing">
  <a href="/jobs/123-ai-pm" class="job-link"><h3 class="job-title">AI Product Manager</h3></a>
  <div class="company-name">Acme AI</div>
  <p class="job-description">Building autonomous agents for the enterprise.</p>
</div>
<div class="job-listing">
  <a href="/jobs/124-eng" class="job-link"><h3 class="job-title">ML Engineer</h3></a>
  <div class="company-name">Bolt Labs</div>
  <p class="job-description">Training LLMs at scale.</p>
</div>
</body></html>
"""


@pytest.mark.asyncio
async def test_yc_scrape_returns_jobs():
    scraper = YCScraper()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = YC_SAMPLE_HTML

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        jobs = await scraper.scrape({"roles": ["Product"]})

    assert len(jobs) == 2
    assert jobs[0].title == "AI Product Manager"
    assert jobs[0].company == "Acme AI"
    assert "https://www.workatastartup.com/jobs/123-ai-pm" in jobs[0].url
    assert jobs[0].source == "yc"


@pytest.mark.asyncio
async def test_yc_is_healthy():
    scraper = YCScraper()
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        assert await scraper.is_healthy() is True


@pytest.mark.asyncio
async def test_yc_unhealthy_on_5xx():
    scraper = YCScraper()
    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        assert await scraper.is_healthy() is False
