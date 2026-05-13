import logging

from sqlalchemy.orm import Session

from app.agents.job_parser import JobParseInput, JobParseOutput, JobParserAgent
from app.agents.job_scorer import JobScoreInput, JobScoreOutput, JobScorerAgent
from app.models.job import Job, JobRequirement, JobScore
from app.models.profile import UserProfile
from app.models.settings import UserSettings
from app.services.ats_detect import detect_ats
from app.services.claude import ClaudeService

logger = logging.getLogger(__name__)


async def run_parse_and_score(db: Session, job_id: int) -> None:
    job = db.query(Job).get(job_id)
    if not job:
        logger.warning("parse_and_score: job %s not found", job_id)
        return
    if job.application_status not in ("discovered", "parsed"):
        logger.info(
            "parse_and_score: job %s already at %s — skipping",
            job_id,
            job.application_status,
        )
        return

    profile = db.query(UserProfile).first()
    settings = db.query(UserSettings).first() or UserSettings()
    if profile is None:
        logger.warning("parse_and_score: no UserProfile — scoring without profile")
        profile = UserProfile(name="", email="")

    claude = ClaudeService()

    # Step 1: Parse
    parser = JobParserAgent(claude)
    parsed: JobParseOutput = await parser.run(
        JobParseInput(raw_text=job.job_description or "", source_url=job.job_url),
        JobParseOutput,
    )
    # Save requirement record
    db.add(JobRequirement(
        job_id=job.id,
        must_have_skills=parsed.must_have_skills,
        nice_to_have_skills=parsed.nice_to_have_skills,
        years_experience_required=parsed.years_experience_required,
        education_requirements=parsed.education_requirements,
        key_responsibilities=parsed.key_responsibilities,
        culture_signals=parsed.culture_signals,
        red_flags=parsed.red_flags,
    ))
    # Update job
    if parsed.company_name:
        job.company_name = parsed.company_name
    if parsed.role_title:
        job.role_title = parsed.role_title
    job.location = parsed.location
    job.remote_type = parsed.remote_type
    job.salary_min = parsed.salary_min
    job.salary_max = parsed.salary_max
    job.salary_currency = parsed.salary_currency
    job.company_stage = parsed.company_stage
    job.company_size = parsed.company_size
    job.company_industry = parsed.company_industry
    job.apply_url = job.apply_url or job.job_url  # may be refined later
    job.ats_type = detect_ats(job.apply_url)
    job.application_status = "parsed"
    db.commit()

    # Step 2: Score
    scorer = JobScorerAgent(claude)
    score_input = JobScoreInput(
        job_description=job.job_description or "",
        role_title=job.role_title,
        company_name=job.company_name,
        location=job.location,
        remote_type=job.remote_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        company_stage=job.company_stage,
        must_have_skills=parsed.must_have_skills,
        nice_to_have_skills=parsed.nice_to_have_skills,
        key_responsibilities=parsed.key_responsibilities,
        candidate_summary=(
            getattr(profile, "positioning_statement", None)
            or getattr(profile, "bio", None)
            or ""
        ),
        candidate_skills=[],
        candidate_target_roles=getattr(profile, "target_roles", None) or [],
        candidate_work_preference=getattr(profile, "work_preference", None) or "",
        candidate_target_locations=getattr(profile, "target_locations", None) or [],
        candidate_salary_min=getattr(profile, "salary_expectation_min", None),
        candidate_salary_max=getattr(profile, "salary_expectation_max", None),
    )
    scored: JobScoreOutput = await scorer.run(score_input, JobScoreOutput)
    db.add(JobScore(
        job_id=job.id,
        role_match=scored.role_match,
        skill_match=scored.skill_match,
        startup_fit=scored.startup_fit,
        ai_relevance=scored.ai_relevance,
        location_fit=scored.location_fit,
        speed_of_hiring=scored.speed_of_hiring,
        compensation_fit=scored.compensation_fit,
        total_score=scored.total_score,
        decision=scored.decision,
        reasoning=scored.reasoning,
        resume_angle=scored.resume_angle,
        outreach_angle=scored.outreach_angle,
    ))
    job.fit_score = scored.total_score

    # Step 3: Route based on threshold
    threshold = settings.auto_review_threshold
    if scored.total_score >= threshold:
        job.application_status = "pending_review"
    else:
        job.application_status = "skipped"
    db.commit()
    logger.info(
        "Parsed+scored job %d: %d/100 → %s",
        job.id,
        scored.total_score,
        job.application_status,
    )
