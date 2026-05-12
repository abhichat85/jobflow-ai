from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse

router = APIRouter(prefix="/api/crm", tags=["crm"])

PIPELINE_STATUSES = [
    "discovered", "scored", "ready", "applied",
    "rejected", "paused",
]


@router.get("/pipeline")
def get_pipeline(db: Session = Depends(get_db)):
    counts = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )
    pipeline = {s: 0 for s in PIPELINE_STATUSES}
    for status, count in counts:
        pipeline[status] = count
    return pipeline


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Job.id)).scalar()
    applied = db.query(func.count(Job.id)).filter(Job.status == "applied").scalar()
    avg_score = db.query(func.avg(Job.fit_score)).filter(Job.fit_score.isnot(None)).scalar()
    return {
        "total_jobs": total,
        "applied": applied,
        "avg_score": round(avg_score, 1) if avg_score else 0,
    }


@router.put("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: int, status: str, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    job.status = status
    db.commit()
    db.refresh(job)
    return job
