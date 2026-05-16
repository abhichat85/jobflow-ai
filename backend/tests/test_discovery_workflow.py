import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import UserSettings
from app.scrapers.linkedin import SessionExpiredError
from app.workflows.discovery import run_discovery


@pytest.fixture()
def db_with_settings():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    s = UserSettings()
    s.linkedin_cookie_encrypted = "fake-encrypted"
    s.linkedin_search_urls = json.dumps([
        "https://www.linkedin.com/jobs/search/?keywords=PM",
        "https://www.linkedin.com/jobs/search/?keywords=Senior+PM",
    ])
    s.discovery_enabled = True
    db.add(s)
    db.commit()
    db.close()
    return Session


@pytest.mark.asyncio
async def test_session_expired_sets_auth_status(db_with_settings):
    db = db_with_settings()

    with patch("app.workflows.discovery.YCScraper") as MockYC, \
         patch("app.workflows.discovery.LinkedInScraper") as MockLI, \
         patch("app.workflows.discovery.decrypt", return_value="fake-cookie"), \
         patch("app.workflows.discovery.get_browser_service", return_value=MagicMock()):
        mock_li_instance = AsyncMock()
        mock_li_instance.source_name = "linkedin"
        mock_li_instance.scrape = AsyncMock(side_effect=SessionExpiredError("expired"))
        MockLI.return_value = mock_li_instance

        mock_yc_instance = AsyncMock()
        mock_yc_instance.source_name = "yc"
        mock_yc_instance.scrape = AsyncMock(return_value=[])
        MockYC.return_value = mock_yc_instance

        await run_discovery(db)

    s = db.query(UserSettings).first()
    assert s.linkedin_auth_status == "expired"
    db.close()
