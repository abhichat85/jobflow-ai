import pytest
from unittest.mock import AsyncMock, MagicMock

from app.form_fillers.base import ApplicationData
from app.form_fillers.lever import LeverFormFiller


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
async def test_lever_fill_happy_path():
    browser = MagicMock()
    page = AsyncMock()
    browser.new_page = AsyncMock(return_value=page)
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.locator = MagicMock()
    page.locator.return_value.set_input_files = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.inner_text = AsyncMock(return_value="Application Submitted")
    page.screenshot = AsyncMock()
    page.close = AsyncMock()

    filler = LeverFormFiller(browser=browser)
    result = await filler.fill("https://jobs.lever.co/openai/abc-123", _data())

    assert result.success is True
    page.fill.assert_any_call('input[name="name"]', "Abhishek")
    page.fill.assert_any_call('input[name="email"]', "a@x.com")
