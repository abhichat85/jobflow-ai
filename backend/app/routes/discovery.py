import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings import UserSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.post("/run")
def run_discovery_now():
    """Trigger a discovery run immediately. Returns Celery task ID."""
    from app.tasks import discover_jobs
    task = discover_jobs.delay()
    return {"status": "started", "task_id": task.id}


@router.get("/status")
def get_discovery_status(db: Session = Depends(get_db)):
    s = db.query(UserSettings).first()
    if not s:
        return {
            "enabled": True,
            "last_run_at": None,
            "last_count": None,
            "interval_hours": 6,
        }
    return {
        "enabled": s.discovery_enabled,
        "last_run_at": s.discovery_last_run_at,
        "last_count": s.discovery_last_count,
        "interval_hours": s.discovery_interval_hours,
    }
