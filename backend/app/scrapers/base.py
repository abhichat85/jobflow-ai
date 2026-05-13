from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RawJob:
    """Normalized output from any job board scraper."""
    url: str
    title: str
    company: str
    raw_text: str
    source: str  # "linkedin" | "yc" | future sources


class BaseJobScraper(ABC):
    """Abstract interface every job board scraper implements.

    Concrete scrapers set `source_name` and implement `scrape()` and `is_healthy()`.
    """

    source_name: str = "base"

    @abstractmethod
    async def scrape(self, params: dict[str, Any]) -> list[RawJob]:
        """Return discovered jobs as a list of RawJob.

        `params` is scraper-specific (e.g. {"search_url": "..."}, {"roles": [...]}).
        """

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Quick check: can the scraper reach its source?"""
