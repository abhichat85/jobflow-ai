import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.settings import UserSettings
from app.scrapers.base import BaseJobScraper
from app.scrapers.linkedin import LinkedInScraper, SessionExpiredError
from app.scrapers.yc import YCScraper
from app.services.browser import get_browser_service
from app.services.crypto import decrypt

logger = logging.getLogger(__name__)


def _get_or_create_settings(db: Session) -> UserSettings:
    s = db.query(UserSettings).first()
    if not s:
        s = UserSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _get_enabled_scrapers(settings: UserSettings, browser) -> list[BaseJobScraper]:
    scrapers: list[BaseJobScraper] = [YCScraper()]
    cookie = decrypt(settings.linkedin_cookie_encrypted)
    search_urls = json.loads(settings.linkedin_search_urls or "[]")
    # Fall back to legacy single URL if new list is empty
    if not search_urls and settings.linkedin_search_url:
        search_urls = [settings.linkedin_search_url]
    if cookie and search_urls:
        scrapers.append(LinkedInScraper(browser=browser, cookie=cookie))
    return scrapers


def _enqueue_parse_and_score(job_id: int) -> None:
    """Side-effect: enqueue background processing. Stubbed for tests."""
    from app.tasks import parse_and_score_job
    parse_and_score_job.delay(job_id)


async def run_discovery(db: Session) -> int:
    """Run all enabled scrapers, dedup jobs by URL, insert new ones, enqueue parse+score.

    Returns the number of new jobs inserted.
    """
    settings = _get_or_create_settings(db)
    if not settings.discovery_enabled:
        logger.info("Discovery is disabled")
        return 0

    browser = get_browser_service()
    scrapers = _get_enabled_scrapers(settings, browser)
    new_count = 0

    # Build the list of (scraper, params) pairs.
    # LinkedIn runs once per URL; other scrapers run once with their own params.
    scraper_runs: list[tuple] = []
    search_urls = json.loads(settings.linkedin_search_urls or "[]")
    if not search_urls and settings.linkedin_search_url:
        search_urls = [settings.linkedin_search_url]

    for scraper in scrapers:
        if scraper.source_name == "linkedin" and search_urls:
            for url in search_urls:
                scraper_runs.append((scraper, {"search_url": url}))
        else:
            scraper_runs.append((scraper, _build_params_for(scraper, settings)))

    for scraper, params in scraper_runs:
        try:
            raw_jobs = await scraper.scrape(params)
        except SessionExpiredError as e:
            logger.warning("LinkedIn session expired: %s", e)
            settings.linkedin_auth_status = "expired"
            db.commit()
            continue
        except Exception as e:
            logger.exception("Scraper %s failed: %s", scraper.source_name, e)
            continue

        for raw in raw_jobs:
            existing = db.query(Job).filter(Job.job_url == raw.url).first()
            if existing:
                continue
            job = Job(
                job_url=raw.url,
                role_title=raw.title,
                company_name=raw.company,
                job_description=raw.raw_text,
                source=raw.source,
                application_status="discovered",
                discovered_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            _enqueue_parse_and_score(job.id)
            new_count += 1

    settings.discovery_last_run_at = datetime.utcnow()
    settings.discovery_last_count = new_count
    db.commit()
    logger.info("Discovery complete: %d new jobs", new_count)
    return new_count


def _build_params_for(scraper: BaseJobScraper, settings: UserSettings) -> dict:
    if scraper.source_name == "linkedin":
        return {"search_url": settings.linkedin_search_url}
    if scraper.source_name == "yc":
        return settings.yc_filters or {"roles": ["Product", "AI"], "remote": True}
    return {}
