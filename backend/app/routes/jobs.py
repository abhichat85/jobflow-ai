from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job, JobRequirement, JobScore
from app.schemas.job import (
    JobCreate,
    JobDetailResponse,
    JobResponse,
    JobScoreResponse,
    JobUpdate,
)
from app.schemas.asset import AssetResponse
from app.services.claude import ClaudeService
from app.agents.job_parser import JobParserAgent, JobParseInput, JobParseOutput
from app.agents.job_scorer import JobScorerAgent, JobScoreInput, JobScoreOutput
from app.agents.resume_tailor import ResumeTailorAgent, ResumeTailorInput, ResumeTailorOutput
from app.agents.cover_letter import CoverLetterAgent, CoverLetterInput, CoverLetterOutput
from app.models.profile import UserProfile, Experience, Skill
from app.models.resume import ResumeVariant
from app.models.asset import ApplicationAsset

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    job = Job(**data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobResponse])
def list_jobs(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    if source:
        query = query.filter(Job.source == source)
    if score_min is not None:
        query = query.filter(Job.fit_score >= score_min)
    return query.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, data: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"ok": True}


@router.post("/{job_id}/score", response_model=JobScoreResponse)
async def score_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not set up")

    skills = db.query(Skill).filter(Skill.user_profile_id == profile.id).all()

    # Parse job if requirements don't exist yet
    if not job.requirements:
        claude = ClaudeService()
        parser = JobParserAgent(claude)
        parsed = await parser.run(
            JobParseInput(raw_text=job.job_description or "", source_url=job.job_url),
            JobParseOutput,
        )
        req = JobRequirement(
            job_id=job.id,
            must_have_skills=parsed.must_have_skills,
            nice_to_have_skills=parsed.nice_to_have_skills,
            years_experience_required=parsed.years_experience_required,
            education_requirements=parsed.education_requirements,
            key_responsibilities=parsed.key_responsibilities,
            culture_signals=parsed.culture_signals,
            red_flags=parsed.red_flags,
        )
        db.add(req)
        if parsed.company_name and not job.company_name:
            job.company_name = parsed.company_name
        if parsed.role_title and not job.role_title:
            job.role_title = parsed.role_title
        if parsed.location:
            job.location = parsed.location
        if parsed.remote_type:
            job.remote_type = parsed.remote_type
        if parsed.company_stage:
            job.company_stage = parsed.company_stage
        db.commit()
        db.refresh(job)

    reqs = job.requirements[0] if job.requirements else None

    claude = ClaudeService()
    scorer = JobScorerAgent(claude)
    score_result = await scorer.run(
        JobScoreInput(
            job_description=job.job_description or "",
            role_title=job.role_title,
            company_name=job.company_name,
            location=job.location,
            remote_type=job.remote_type,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            company_stage=job.company_stage,
            must_have_skills=reqs.must_have_skills if reqs else [],
            nice_to_have_skills=reqs.nice_to_have_skills if reqs else [],
            key_responsibilities=reqs.key_responsibilities if reqs else [],
            candidate_summary=profile.positioning_statement or "",
            candidate_skills=[s.name for s in skills],
            candidate_target_roles=profile.target_roles or [],
            candidate_work_preference=profile.work_preference or "",
            candidate_target_locations=profile.target_locations or [],
            candidate_salary_min=profile.salary_expectation_min,
            candidate_salary_max=profile.salary_expectation_max,
        ),
        JobScoreOutput,
    )

    db_score = JobScore(
        job_id=job.id,
        role_match=score_result.role_match,
        skill_match=score_result.skill_match,
        startup_fit=score_result.startup_fit,
        ai_relevance=score_result.ai_relevance,
        location_fit=score_result.location_fit,
        speed_of_hiring=score_result.speed_of_hiring,
        compensation_fit=score_result.compensation_fit,
        total_score=score_result.total_score,
        decision=score_result.decision,
        reasoning=score_result.reasoning,
        resume_angle=score_result.resume_angle,
        outreach_angle=score_result.outreach_angle,
    )
    db.add(db_score)
    job.fit_score = score_result.total_score
    job.status = "scored"
    db.commit()
    db.refresh(db_score)
    return db_score


@router.post("/{job_id}/generate-assets", response_model=AssetResponse)
async def generate_assets(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(UserProfile).first()
    score = db.query(JobScore).filter(JobScore.job_id == job_id).first()
    if not score:
        raise HTTPException(status_code=400, detail="Job not scored yet")

    variant_name = score.resume_angle or "ai_pm"
    variant = (
        db.query(ResumeVariant)
        .filter(
            ResumeVariant.user_profile_id == profile.id,
            ResumeVariant.variant_name == variant_name,
        )
        .first()
    )

    experiences = (
        db.query(Experience)
        .filter(Experience.user_profile_id == profile.id)
        .all()
    )
    skills = db.query(Skill).filter(Skill.user_profile_id == profile.id).all()
    reqs = job.requirements[0] if job.requirements else None

    claude = ClaudeService()

    # Generate tailored resume
    tailor = ResumeTailorAgent(claude)
    tailored = await tailor.run(
        ResumeTailorInput(
            candidate_bio=profile.bio or "",
            candidate_positioning=profile.positioning_statement or "",
            experiences=[
                {
                    "id": e.id,
                    "company_name": e.company_name,
                    "role_title": e.role_title,
                    "bullet_points": e.bullet_points or [],
                }
                for e in experiences
            ],
            projects=[],
            skills=[s.name for s in skills],
            variant_positioning=variant.positioning_statement or "" if variant else "",
            variant_experience_ordering=variant.experience_ordering or [] if variant else [],
            job_description=job.job_description or "",
            must_have_skills=reqs.must_have_skills if reqs else [],
            nice_to_have_skills=reqs.nice_to_have_skills if reqs else [],
            key_responsibilities=reqs.key_responsibilities if reqs else [],
        ),
        ResumeTailorOutput,
    )

    # Generate cover letter and messages
    cover = CoverLetterAgent(claude)
    cover_result = await cover.run(
        CoverLetterInput(
            candidate_name=profile.name,
            candidate_positioning=profile.positioning_statement or "",
            candidate_experience_summary=tailored.summary,
            job_description=job.job_description or "",
            company_name=job.company_name or "",
            role_title=job.role_title or "",
            resume_angle=variant_name,
        ),
        CoverLetterOutput,
    )

    asset = ApplicationAsset(
        job_id=job.id,
        resume_variant_id=variant.id if variant else None,
        tailored_summary=tailored.summary,
        tailored_bullets=tailored.experience_bullets,
        cover_letter=cover_result.cover_letter,
        linkedin_message=cover_result.linkedin_message,
        email_message=cover_result.email_message,
        application_answers=cover_result.application_answers,
        status="draft",
    )
    db.add(asset)
    job.status = "ready"
    db.commit()
    db.refresh(asset)
    return asset
