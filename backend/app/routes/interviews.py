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
from app.services.claude import ClaudeService
from app.agents.interview_prep import InterviewPrepAgent, InterviewPrepInput, InterviewPrepOutput
from app.models.profile import UserProfile, Experience, Skill
from app.models.job import Job

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


@router.post("/{interview_id}/generate-prep", response_model=InterviewPrepResponse)
async def generate_prep(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).get(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    job = db.query(Job).get(interview.job_id)
    profile = db.query(UserProfile).first()
    experiences = db.query(Experience).filter(Experience.user_profile_id == profile.id).all()
    skills = db.query(Skill).filter(Skill.user_profile_id == profile.id).all()

    claude = ClaudeService()
    agent = InterviewPrepAgent(claude)
    result = await agent.run(
        InterviewPrepInput(
            candidate_bio=profile.bio or "",
            candidate_positioning=profile.positioning_statement or "",
            experiences=[
                {"role_title": e.role_title, "company_name": e.company_name}
                for e in experiences
            ],
            projects=[],
            skills=[s.name for s in skills],
            company_name=interview.company_name or job.company_name or "",
            company_url=job.company_url,
            job_description=job.job_description or "",
            role_title=job.role_title or "",
            interview_stage=interview.interview_stage or "screening",
        ),
        InterviewPrepOutput,
    )

    prep = InterviewPrep(
        interview_id=interview.id,
        job_id=job.id,
        company_brief=result.company_brief,
        product_analysis=result.product_analysis,
        role_analysis=result.role_analysis,
        likely_questions=result.likely_questions,
        suggested_answers=result.suggested_answers,
        talking_points=result.talking_points,
        questions_to_ask=result.questions_to_ask,
        thirty_sixty_ninety_plan=result.thirty_sixty_ninety_plan,
        salary_negotiation_notes=result.salary_negotiation_notes,
    )
    db.add(prep)
    db.commit()
    db.refresh(prep)
    return prep
