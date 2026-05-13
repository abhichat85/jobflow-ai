import pytest
from unittest.mock import AsyncMock, MagicMock

from app.form_fillers.base import ApplicationData
from app.form_fillers.ashby import AshbyFormFiller


def _data() -> ApplicationData:
    return ApplicationData(
        name="Abhishek",
        email="a@x.com",
        phone="+1-555-0000",
        linkedin_url="https://linkedin.com/in/abhi",
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Hi...",
        custom_answers={},
    )


@pytest.mark.asyncio
async def test_ashby_fill_happy_path():
    browser = MagicMock()
    page = AsyncMock()
    browser.new_page = AsyncMock(return_value=page)
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.locator = MagicMock()
    page.locator.return_value.set_input_files = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.inner_text = AsyncMock(return_value="Thank you")
    page.screenshot = AsyncMock()
    page.close = AsyncMock()

    filler = AshbyFormFiller(browser=browser)
    result = await filler.fill("https://jobs.ashbyhq.com/notion/abc", _data())
    assert result.success is True
