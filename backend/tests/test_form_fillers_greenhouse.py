import pytest
from unittest.mock import AsyncMock, MagicMock

from app.form_fillers.base import ApplicationData
from app.form_fillers.greenhouse import GreenhouseFormFiller


def _data() -> ApplicationData:
    return ApplicationData(
        name="Abhishek Chatterjee",
        email="abhi@example.com",
        phone="+1-555-0000",
        linkedin_url="https://linkedin.com/in/abhi",
        resume_pdf_path="/tmp/resume.pdf",
        cover_letter_text="Dear hiring manager...",
        custom_answers={},
    )


@pytest.mark.asyncio
async def test_greenhouse_fill_happy_path(tmp_path):
    browser = MagicMock()
    page = AsyncMock()
    browser.new_page = AsyncMock(return_value=page)

    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.locator = MagicMock()
    page.locator.return_value.set_input_files = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.inner_text = AsyncMock(return_value="Thanks! Your application has been received.")
    page.screenshot = AsyncMock()
    page.close = AsyncMock()

    filler = GreenhouseFormFiller(browser=browser)
    result = await filler.fill(
        "https://boards.greenhouse.io/anthropic/jobs/12345",
        _data(),
    )

    assert result.success is True
    assert "thanks" in (result.confirmation_text or "").lower()
    # Verify the standard fields were filled
    page.fill.assert_any_call("#first_name", "Abhishek")
    page.fill.assert_any_call("#last_name", "Chatterjee")
    page.fill.assert_any_call("#email", "abhi@example.com")


@pytest.mark.asyncio
async def test_greenhouse_fill_fails_returns_error(tmp_path):
    browser = MagicMock()
    page = AsyncMock()
    browser.new_page = AsyncMock(return_value=page)
    page.goto = AsyncMock(side_effect=Exception("Network timeout"))
    page.close = AsyncMock()

    filler = GreenhouseFormFiller(browser=browser)
    result = await filler.fill("https://boards.greenhouse.io/x/jobs/1", _data())

    assert result.success is False
    assert "network timeout" in (result.error_message or "").lower()
