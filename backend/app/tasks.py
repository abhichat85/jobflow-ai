from datetime import datetime

from celery_worker import celery_app
from app.database import SessionLocal
from app.models.outreach import Outreach


@celery_app.task
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
