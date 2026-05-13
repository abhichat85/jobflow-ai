import pytest

from app.services.browser import BrowserService


@pytest.mark.asyncio
async def test_browser_service_smoke():
    """Smoke test: actually launch Chromium and visit example.com.

    Skipped automatically if Playwright not installed.
    """
    pytest.importorskip("playwright")

    svc = BrowserService()
    await svc.start()
    try:
        page = await svc.new_page()
        await page.goto("https://example.com", timeout=15000)
        title = await page.title()
        assert "Example" in title
        await page.close()
    finally:
        await svc.shutdown()


@pytest.mark.asyncio
async def test_browser_service_new_page_with_cookie():
    pytest.importorskip("playwright")

    svc = BrowserService()
    await svc.start()
    try:
        page = await svc.new_page(cookies=[{
            "name": "li_at",
            "value": "test-value",
            "domain": ".linkedin.com",
            "path": "/",
        }])
        # Cookie is set on the browser context
        cookies = await page.context.cookies("https://www.linkedin.com")
        assert any(c["name"] == "li_at" and c["value"] == "test-value" for c in cookies)
        await page.close()
    finally:
        await svc.shutdown()
