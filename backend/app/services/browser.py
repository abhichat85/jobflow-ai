"""Singleton Playwright browser manager.

Launches a single headless Chromium instance and hands out fresh pages.
Used by both scrapers (LinkedIn) and form fillers (Greenhouse/Lever/Ashby).
"""
import asyncio
import logging
import uuid
from typing import Any, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.database import SessionLocal
from app.models.settings import UserSettings
from app.services.crypto import encrypt

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


# Module-level dict tracking in-progress LinkedIn auth sessions.
# Safe for single-process local deployment.
# Key: session_id (uuid4 string), Value: {"status": "waiting"|"connected"|"timeout"}
_auth_sessions: dict[str, dict] = {}


async def open_login_window(session_id: str) -> None:
    """Spawn a visible Chromium window for LinkedIn login.

    Polls for the li_at session cookie, saves it encrypted to DB, then closes.
    Updates _auth_sessions[session_id] to reflect outcome.
    """
    _auth_sessions[session_id] = {"status": "waiting"}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()
            await page.goto("https://www.linkedin.com/login")

            deadline = asyncio.get_event_loop().time() + 300  # 5-minute timeout
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(2)
                cookies = await context.cookies()
                li_at = next(
                    (c["value"] for c in cookies if c["name"] == "li_at"), None
                )
                if li_at:
                    db = SessionLocal()
                    try:
                        s = db.query(UserSettings).first()
                        if not s:
                            s = UserSettings()
                            db.add(s)
                        s.linkedin_cookie_encrypted = encrypt(li_at)
                        s.linkedin_auth_status = "connected"
                        db.commit()
                    finally:
                        db.close()
                    _auth_sessions[session_id] = {"status": "connected"}
                    logger.info("LinkedIn auth captured for session %s", session_id)
                    return

            _auth_sessions[session_id] = {"status": "timeout"}
            logger.warning("LinkedIn auth timed out for session %s", session_id)
        finally:
            await browser.close()


# Module-level singleton, instantiated lazily
_instance: Optional[BrowserService] = None


def get_browser_service() -> BrowserService:
    global _instance
    if _instance is None:
        _instance = BrowserService()
    return _instance
