import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.form_fillers.base import ApplyResult
from app.models.application import ApplicationAttempt
from app.models.job import Job
from app.models.profile import UserProfile
from app.workflows.apply import prepare_application, run_submit_application


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.mark.asyncio
async def test_prepare_application_builds_preview(db):
    db.add(UserProfile(
        name="Abhishek",
        email="a@x.com",
        phone="+1-555",
        linkedin_url="https://linkedin.com/in/abhi",
    ))
    job = Job(
        job_url="https://x/j/1",
        apply_url="https://boards.greenhouse.io/co/jobs/1",
        ats_type="greenhouse",
        role_title="AI PM",
        company_name="Anthropic",
        application_status="pending_review",
    )
    db.add(job)
    db.commit()

    with patch("app.workflows.apply._generate_cover_letter", AsyncMock(return_value="Dear hiring manager...")):
        preview = await prepare_application(db, job.id)

    assert preview["form_data"]["name"] == "Abhishek"
    assert preview["form_data"]["email"] == "a@x.com"
    assert preview["cover_letter_text"] == "Dear hiring manager..."
    assert preview["ats_type"] == "greenhouse"


@pytest.mark.asyncio
async def test_run_submit_application_success(db):
    job = Job(
        job_url="https://x/j/1",
        apply_url="https://boards.greenhouse.io/co/jobs/1",
        ats_type="greenhouse",
        application_status="approved",
    )
    db.add(job)
    db.commit()

    fake_filler = MagicMock()
    fake_filler.fill = AsyncMock(return_value=ApplyResult(
        success=True,
        confirmation_text="Thanks!",
        screenshot_path="/tmp/x.png",
    ))

    with patch("app.workflows.apply.get_form_filler", return_value=fake_filler), \
         patch("app.workflows.apply.get_browser_service"):
        result = await run_submit_application(db, job.id, {
            "name": "A", "email": "a@x.com", "phone": "+1",
            "linkedin_url": "https://lk", "resume_pdf_path": "/tmp/r.pdf",
            "cover_letter_text": "...", "custom_answers": {},
        })

    db.refresh(job)
    assert job.application_status == "applied"
    assert result["success"] is True
    attempt = db.query(ApplicationAttempt).filter_by(job_id=job.id).one()
    assert attempt.status == "success"


@pytest.mark.asyncio
async def test_run_submit_application_failure_marks_failed(db):
    job = Job(
        job_url="https://x/j/2",
        apply_url="https://boards.greenhouse.io/co/jobs/2",
        ats_type="greenhouse",
        application_status="approved",
    )
    db.add(job)
    db.commit()

    fake_filler = MagicMock()
    fake_filler.fill = AsyncMock(return_value=ApplyResult(success=False, error_message="captcha"))

    with patch("app.workflows.apply.get_form_filler", return_value=fake_filler), \
         patch("app.workflows.apply.get_browser_service"):
        result = await run_submit_application(db, job.id, {
            "name": "A", "email": "a@x.com", "phone": "+1",
            "linkedin_url": "https://lk", "resume_pdf_path": "/tmp/r.pdf",
            "cover_letter_text": "...", "custom_answers": {},
        })

    db.refresh(job)
    assert job.application_status == "failed"
    assert result["success"] is False
