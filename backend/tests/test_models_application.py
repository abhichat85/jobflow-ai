import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.application import ApplicationAttempt
from app.models.job import Job


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


def test_application_attempt_creation(db):
    job = Job(job_url="https://x/j/1", role_title="PM")
    db.add(job)
    db.commit()

    attempt = ApplicationAttempt(
        job_id=job.id,
        status="success",
        resume_variant="ai_pm",
        cover_letter_text="Dear hiring manager...",
        form_data={"first_name": "Abhishek", "email": "a@example.com"},
        confirmation_text="Thanks for applying!",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    assert attempt.id is not None
    assert attempt.status == "success"
    assert attempt.form_data["first_name"] == "Abhishek"
    assert isinstance(attempt.attempted_at, datetime)
