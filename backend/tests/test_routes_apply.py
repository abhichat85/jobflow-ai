from unittest.mock import AsyncMock, patch

from app.models.job import Job
from app.models.profile import UserProfile


def test_preview_returns_form_data(client):
    # Seed
    from app.database import get_db
    db = next(client.app.dependency_overrides[get_db]())
    db.add(UserProfile(name="Abhi", email="a@x.com", phone="+1-555-0000",
                       linkedin_url="https://lk"))
    db.add(Job(
        id=1,
        job_url="https://x/j/1",
        apply_url="https://boards.greenhouse.io/co/jobs/1",
        ats_type="greenhouse",
        role_title="AI PM",
        company_name="Anthropic",
        application_status="pending_review",
    ))
    db.commit()

    with patch("app.workflows.apply._generate_cover_letter", AsyncMock(return_value="Dear...")):
        resp = client.get("/api/apply/1/preview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["form_data"]["name"] == "Abhi"
    assert body["cover_letter_text"] == "Dear..."


def test_submit_enqueues_and_marks_approved(client):
    from app.database import get_db
    db = next(client.app.dependency_overrides[get_db]())
    db.add(Job(
        id=2,
        job_url="https://x/j/2",
        apply_url="https://boards.greenhouse.io/co/jobs/2",
        ats_type="greenhouse",
        application_status="pending_review",
    ))
    db.commit()

    fake_task = type("T", (), {"id": "task-xyz"})()
    with patch("app.tasks.submit_application.delay", return_value=fake_task):
        resp = client.post("/api/apply/2", json={
            "name": "A", "email": "a@x.com", "phone": "+1",
            "linkedin_url": "https://lk", "resume_pdf_path": "/tmp/r.pdf",
            "cover_letter_text": "Hi", "custom_answers": {},
        })

    assert resp.status_code == 200
    assert resp.json()["task_id"] == "task-xyz"

    db.expire_all()
    job = db.query(Job).get(2)
    assert job.application_status == "approved"


def test_skip_marks_skipped(client):
    from app.database import get_db
    db = next(client.app.dependency_overrides[get_db]())
    db.add(Job(
        id=3,
        job_url="https://x/j/3",
        apply_url="https://x/apply",
        ats_type="unknown",
        application_status="pending_review",
    ))
    db.commit()

    resp = client.post("/api/apply/3/skip")
    assert resp.status_code == 200
    db.expire_all()
    job = db.query(Job).get(3)
    assert job.application_status == "skipped"
