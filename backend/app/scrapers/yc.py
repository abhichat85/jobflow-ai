import logging
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseJobScraper, RawJob

logger = logging.getLogger(__name__)

YC_BASE = "https://www.workatastartup.com"
YC_JOBS_PATH = "/jobs"


class YCScraper(BaseJobScraper):
    """Scrapes workatastartup.com — no auth required."""

    source_name = "yc"

    async def scrape(self, params: dict[str, Any]) -> list[RawJob]:
        """params: { "roles": [...], "remote": bool }."""
        query = self._build_query(params)
        url = f"{YC_BASE}{YC_JOBS_PATH}"
        if query:
            url = f"{url}?{query}"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code >= 400:
                logger.warning("YC scrape returned %s for %s", resp.status_code, url)
                return []

        return self._parse(resp.text)

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{YC_BASE}{YC_JOBS_PATH}")
                return resp.status_code < 400
        except Exception as e:
            logger.warning("YC health check failed: %s", e)
            return False

    @staticmethod
    def _build_query(params: dict[str, Any]) -> str:
        q = {}
        roles = params.get("roles") or []
        if roles:
            q["role"] = ",".join(roles)
        if params.get("remote"):
            q["remote"] = "true"
        return urlencode(q)

    @staticmethod
    def _parse(html: str) -> list[RawJob]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[RawJob] = []
        for listing in soup.select(".job-listing"):
            link = listing.select_one(".job-link")
            title_el = listing.select_one(".job-title")
            company_el = listing.select_one(".company-name")
            desc_el = listing.select_one(".job-description")

            if not link or not title_el:
                continue

            href = link.get("href") or ""
            url = urljoin(YC_BASE, href)

            jobs.append(RawJob(
                url=url,
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                raw_text=desc_el.get_text(strip=True) if desc_el else "",
                source="yc",
            ))
        return jobs
