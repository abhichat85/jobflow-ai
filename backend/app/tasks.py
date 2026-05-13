import asyncio
import logging
from datetime import datetime

from celery_worker import celery_app
from app.database import SessionLocal
from app.models.outreach import Outreach

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.check_pending_followups")
def check_pending_followups():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        pending = (
            db.query(Outreach)
            .filter(
                Outreach.scheduled_followup_at <= now,
                Outreach.status == "sent",
            )
            .all()
        )
        return {"pending_followups": len(pending)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.discover_jobs")
def discover_jobs():
    """Background task: run all enabled scrapers, insert new jobs."""
    from app.workflows.discovery import run_discovery

    db = SessionLocal()
    try:
        count = asyncio.run(run_discovery(db))
        return {"new_jobs": count}
    finally:
        db.close()


@celery_app.task(name="app.tasks.parse_and_score_job")
def parse_and_score_job(job_id: int):
    """Background task: parse + score a single job (Task 11 implements this)."""
    from app.workflows.parse_and_score import run_parse_and_score

    db = SessionLocal()
    try:
        asyncio.run(run_parse_and_score(db, job_id))
        return {"job_id": job_id}
    finally:
        db.close()


@celery_app.task(name="app.tasks.submit_application")
def submit_application(job_id: int, form_data: dict):
    """Background task: submit application via Playwright (Task 21 implements this)."""
    from app.workflows.apply import run_submit_application

    db = SessionLocal()
    try:
        result = asyncio.run(run_submit_application(db, job_id, form_data))
        return result
    finally:
        db.close()
