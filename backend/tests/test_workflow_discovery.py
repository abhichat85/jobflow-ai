import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.job import Job
from app.models.settings import UserSettings
from app.scrapers.base import RawJob
from app.workflows.discovery import run_discovery


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.mark.asyncio
async def test_run_discovery_inserts_new_jobs_and_skips_dupes(db, monkeypatch):
    # Seed: settings + one pre-existing job
    settings = UserSettings(discovery_enabled=True)
    db.add(settings)
    db.add(Job(job_url="https://example.com/job/1", role_title="Existing", application_status="discovered"))
    db.commit()

    # Mock scrapers: one returns a duplicate + a new job
    fake_scraper = MagicMock()
    fake_scraper.source_name = "yc"
    fake_scraper.scrape = AsyncMock(return_value=[
        RawJob(url="https://example.com/job/1", title="Dup", company="X", raw_text="", source="yc"),
        RawJob(url="https://example.com/job/2", title="New PM", company="Acme", raw_text="...", source="yc"),
    ])

    # Patch the scraper factory
    enqueued = []
    monkeypatch.setattr(
        "app.workflows.discovery._get_enabled_scrapers",
        lambda settings, browser: [fake_scraper],
    )
    monkeypatch.setattr(
        "app.workflows.discovery._enqueue_parse_and_score",
        lambda job_id: enqueued.append(job_id),
    )

    count = await run_discovery(db)

    assert count == 1
    assert db.query(Job).count() == 2
    new_job = db.query(Job).filter(Job.job_url == "https://example.com/job/2").one()
    assert new_job.application_status == "discovered"
    assert len(enqueued) == 1
    assert enqueued[0] == new_job.id

    # Settings should be updated
    db.refresh(settings)
    assert settings.discovery_last_count == 1
    assert settings.discovery_last_run_at is not None


@pytest.mark.asyncio
async def test_run_discovery_creates_settings_if_missing(db, monkeypatch):
    monkeypatch.setattr(
        "app.workflows.discovery._get_enabled_scrapers",
        lambda settings, browser: [],
    )
    count = await run_discovery(db)
    assert count == 0
    assert db.query(UserSettings).count() == 1
