"""Singleton Playwright browser manager.

Launches a single headless Chromium instance and hands out fresh pages.
Used by both scrapers (LinkedIn) and form fillers (Greenhouse/Lever/Ashby).
"""
import asyncio
import logging
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)


class BrowserService:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._browser is not None:
                return
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            logger.info("BrowserService launched (headless=%s)", self.headless)

    async def shutdown(self) -> None:
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

    async def new_page(
        self,
        cookies: Optional[list[dict[str, Any]]] = None,
        user_agent: Optional[str] = None,
    ) -> Page:
        """Create a fresh page in a new context. Caller closes it."""
        if self._browser is None:
            await self.start()
        assert self._browser is not None

        context: BrowserContext = await self._browser.new_context(
            user_agent=user_agent or (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        if cookies:
            await context.add_cookies(cookies)
        return await context.new_page()


# Module-level singleton, instantiated lazily
_instance: Optional[BrowserService] = None


def get_browser_service() -> BrowserService:
    global _instance
    if _instance is None:
        _instance = BrowserService()
    return _instance
