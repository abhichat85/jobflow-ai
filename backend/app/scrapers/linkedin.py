import asyncio
import logging
from typing import Any, Optional

from app.scrapers.base import BaseJobScraper, RawJob
from app.services.browser import BrowserService

logger = logging.getLogger(__name__)


class SessionExpiredError(Exception):
    """Raised when LinkedIn redirects us to login (cookie expired/invalid)."""


# JavaScript that runs inside the page to extract job cards from the jobs search UI.
# LinkedIn changes selectors frequently; we use multiple fallbacks.
EXTRACT_JOBS_JS = """
() => {
    const cards = Array.from(document.querySelectorAll(
        '.jobs-search-results__list-item, .scaffold-layout__list-item, [data-occludable-job-id]'
    ));
    return cards.map(card => {
        const linkEl = card.querySelector('a.job-card-list__title, a.job-card-container__link, a[href*="/jobs/view/"]');
        const titleEl = card.querySelector('.job-card-list__title, .job-card-container__primary-description');
        const companyEl = card.querySelector('.job-card-container__primary-description, .artdeco-entity-lockup__subtitle, .job-card-container__company-name');
        const snippetEl = card.querySelector('.job-card-container__metadata-item, .job-card-list__insight');
        const url = linkEl?.href || '';
        return {
            url: url.split('?')[0],
            title: (titleEl?.innerText || linkEl?.innerText || '').trim(),
            company: (companyEl?.innerText || '').trim(),
            raw_text: (snippetEl?.innerText || '').trim(),
        };
    }).filter(j => j.url && j.title);
}
"""


class LinkedInScraper(BaseJobScraper):
    source_name = "linkedin"

    def __init__(self, browser: BrowserService, cookie: str):
        self.browser = browser
        self.cookie = cookie

    async def scrape(self, params: dict[str, Any]) -> list[RawJob]:
        if not self.cookie:
            logger.info("LinkedIn cookie not set — skipping LinkedIn scrape")
            return []
        search_url = params.get("search_url")
        if not search_url:
            logger.warning("LinkedIn scrape called without search_url")
            return []

        page = await self.browser.new_page(cookies=self._cookie_jar())
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            # If we got redirected to login, the cookie is invalid
            if "/login" in page.url or "/uas/login" in page.url:
                raise SessionExpiredError("LinkedIn redirected to login — cookie invalid or expired")
            # Allow lazy-loaded cards to render
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2.0)  # extra settle time
            raw = await page.evaluate(EXTRACT_JOBS_JS)
        finally:
            await page.close()

        return [
            RawJob(
                url=item["url"],
                title=item["title"],
                company=item["company"],
                raw_text=item["raw_text"],
                source="linkedin",
            )
            for item in raw
        ]

    async def is_healthy(self) -> bool:
        if not self.cookie:
            return False
        page = await self.browser.new_page(cookies=self._cookie_jar())
        try:
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
            return "/login" not in page.url
        except Exception as e:
            logger.warning("LinkedIn health check failed: %s", e)
            return False
        finally:
            await page.close()

    def _cookie_jar(self) -> list[dict[str, Any]]:
        return [{
            "name": "li_at",
            "value": self.cookie,
            "domain": ".linkedin.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
        }]
