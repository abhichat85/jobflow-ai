import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import ApplicationAttempt
from app.models.job import Job
from app.schemas.apply import ApplyFormData, ApplyPreviewResponse, ApplySubmitResponse
from app.workflows.apply import prepare_application

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apply", tags=["apply"])


@router.get("/{job_id}/preview", response_model=ApplyPreviewResponse)
async def get_preview(job_id: int, db: Session = Depends(get_db)):
    try:
        preview = await prepare_application(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return preview


@router.post("/{job_id}", response_model=ApplySubmitResponse)
def submit(job_id: int, data: ApplyFormData, db: Session = Depends(get_db)):
    from app.tasks import submit_application
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.application_status = "approved"
    db.commit()

    task = submit_application.delay(job_id, data.model_dump())
    return ApplySubmitResponse(status="enqueued", task_id=task.id)


@router.get("/{job_id}/status")
def get_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    latest = (
        db.query(ApplicationAttempt)
        .filter(ApplicationAttempt.job_id == job_id)
        .order_by(ApplicationAttempt.attempted_at.desc())
        .first()
    )
    return {
        "application_status": job.application_status,
        "attempt": {
            "status": latest.status,
            "confirmation_text": latest.confirmation_text,
            "screenshot_path": latest.screenshot_path,
            "error_message": latest.error_message,
            "attempted_at": latest.attempted_at,
        } if latest else None,
    }


@router.post("/{job_id}/skip")
def skip(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.application_status = "skipped"
    db.commit()
    return {"ok": True}
