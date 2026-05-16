"""Tests for open_login_window() — mocks Playwright to avoid real browser."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import UserSettings
from app.services.browser import open_login_window, _auth_sessions


@pytest.fixture()
def mem_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(UserSettings())
    db.commit()
    db.close()
    return Session


def _make_mock_playwright(li_at_value: str):
    """Build a mock playwright stack that returns li_at on second cookie poll."""
    mock_cookie = {"name": "li_at", "value": li_at_value}
    call_count = {"n": 0}

    async def fake_cookies():
        call_count["n"] += 1
        if call_count["n"] >= 2:
            return [mock_cookie]
        return []

    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.cookies = fake_cookies
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright_instance = AsyncMock()
    mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

    return mock_playwright_instance, mock_browser


@pytest.mark.asyncio
async def test_open_login_window_captures_cookie(mem_db):
    mock_pw, mock_browser = _make_mock_playwright("fake-li-at-token")
    session_id = "test-session-abc"

    with patch("app.services.browser.async_playwright") as mock_ap, \
         patch("app.services.browser.SessionLocal", mem_db):
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_pw)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_ap.return_value = cm

        await open_login_window(session_id)

    assert _auth_sessions[session_id]["status"] == "connected"
    db = mem_db()
    s = db.query(UserSettings).first()
    assert s.linkedin_cookie_encrypted is not None
    assert s.linkedin_auth_status == "connected"
    db.close()
