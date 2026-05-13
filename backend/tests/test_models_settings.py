import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models.settings import UserSettings


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_user_settings_defaults(db: Session):
    s = UserSettings()
    db.add(s)
    db.commit()
    db.refresh(s)
    assert s.discovery_enabled is True
    assert s.discovery_interval_hours == 6
    assert s.auto_review_threshold == 65
    assert s.auto_apply_threshold == 80
    assert s.daily_apply_cap == 10
    assert s.cover_letter_tone == "professional"
