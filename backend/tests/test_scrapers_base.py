import pytest
from app.scrapers.base import BaseJobScraper, RawJob


def test_raw_job_dataclass():
    job = RawJob(
        url="https://example.com/job/1",
        title="Senior PM",
        company="TestCo",
        raw_text="We are hiring...",
        source="yc",
    )
    assert job.url == "https://example.com/job/1"
    assert job.source == "yc"


def test_base_scraper_is_abstract():
    with pytest.raises(TypeError):
        BaseJobScraper()  # Cannot instantiate abstract class


def test_base_scraper_subclass_must_implement_scrape():
    class Incomplete(BaseJobScraper):
        async def is_healthy(self) -> bool:
            return True

    with pytest.raises(TypeError):
        Incomplete()


def test_base_scraper_full_subclass_can_instantiate():
    class Concrete(BaseJobScraper):
        source_name = "test"

        async def scrape(self, params):
            return []

        async def is_healthy(self):
            return True

    s = Concrete()
    assert s.source_name == "test"
