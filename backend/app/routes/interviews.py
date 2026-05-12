from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview, InterviewPrep
from app.schemas.interview import (
    InterviewCreate,
    InterviewPrepResponse,
    InterviewResponse,
    InterviewUpdate,
)

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("", response_model=list[InterviewResponse])
def list_interviews(db: Session = Depends(get_db)):
    return db.query(Interview).order_by(Interview.interview_date.desc()).all()


@router.post("", response_model=InterviewResponse)
def create_interview(data: InterviewCreate, db: Session = Depends(get_db)):
    interview = Interview(**data.model_dump())
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.put("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: int, data: InterviewUpdate, db: Session = Depends(get_db)
):
    interview = db.query(Interview).get(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(interview, key, value)
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/{interview_id}/prep", response_model=Optional[InterviewPrepResponse])
def get_interview_prep(interview_id: int, db: Session = Depends(get_db)):
    prep = (
        db.query(InterviewPrep)
        .filter(InterviewPrep.interview_id == interview_id)
        .first()
    )
    return prep
