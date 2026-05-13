import pytest
from unittest.mock import AsyncMock, MagicMock

from app.scrapers.linkedin import LinkedInScraper, SessionExpiredError


@pytest.mark.asyncio
async def test_linkedin_scrape_extracts_jobs_from_dom():
    mock_browser = MagicMock()
    mock_page = AsyncMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)

    # Mock the page.evaluate call that extracts job cards
    mock_page.evaluate = AsyncMock(return_value=[
        {
            "url": "https://www.linkedin.com/jobs/view/111",
            "title": "Senior AI PM",
            "company": "Anthropic",
            "raw_text": "Build the future of AI products.",
        },
        {
            "url": "https://www.linkedin.com/jobs/view/222",
            "title": "Product Manager",
            "company": "OpenAI",
            "raw_text": "Lead product for our flagship.",
        },
    ])
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.close = AsyncMock()
    mock_page.url = "https://www.linkedin.com/jobs/search/?keywords=AI+PM"

    scraper = LinkedInScraper(browser=mock_browser, cookie="AQEDtest")
    jobs = await scraper.scrape({"search_url": "https://www.linkedin.com/jobs/search/?keywords=AI+PM"})

    assert len(jobs) == 2
    assert jobs[0].title == "Senior AI PM"
    assert jobs[0].source == "linkedin"
    assert jobs[1].company == "OpenAI"


@pytest.mark.asyncio
async def test_linkedin_session_expired_raises():
    mock_browser = MagicMock()
    mock_page = AsyncMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.url = "https://www.linkedin.com/login"  # Redirected to login
    mock_page.close = AsyncMock()

    scraper = LinkedInScraper(browser=mock_browser, cookie="expired")
    with pytest.raises(SessionExpiredError):
        await scraper.scrape({"search_url": "https://www.linkedin.com/jobs/search/"})


@pytest.mark.asyncio
async def test_linkedin_empty_cookie_returns_empty():
    mock_browser = MagicMock()
    scraper = LinkedInScraper(browser=mock_browser, cookie="")
    jobs = await scraper.scrape({"search_url": "https://www.linkedin.com/jobs/search/"})
    assert jobs == []
