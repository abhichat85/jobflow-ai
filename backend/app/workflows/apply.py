"""Apply workflow: prepare a preview and submit the application."""
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.form_fillers.base import ApplicationData
from app.form_fillers.factory import UnsupportedATSError, get_form_filler
from app.models.application import ApplicationAttempt
from app.models.job import Job
from app.models.profile import UserProfile
from app.services.browser import get_browser_service
from app.services.claude import ClaudeService

logger = logging.getLogger(__name__)


async def _generate_cover_letter(profile: UserProfile, job: Job) -> str:
    """Generate a cover letter using CoverLetterAgent.

    Note: this is patched out in tests; production callers will exercise the
    real Claude-backed agent.
    """
    from app.agents.cover_letter import (
        CoverLetterAgent,
        CoverLetterInput,
        CoverLetterOutput,
    )

    claude = ClaudeService()
    agent = CoverLetterAgent(claude)
    positioning = profile.positioning_statement or profile.bio or ""
    experience_summary = profile.career_narrative or profile.bio or ""
    result: CoverLetterOutput = await agent.run(
        CoverLetterInput(
            candidate_name=profile.name or "",
            candidate_positioning=positioning,
            candidate_experience_summary=experience_summary,
            job_description=job.job_description or "",
            company_name=job.company_name or "",
            role_title=job.role_title or "",
            resume_angle="",
        ),
        CoverLetterOutput,
    )
    return result.cover_letter


async def prepare_application(db: Session, job_id: int) -> dict:
    """Build the preview shown in the Review UI before user approves."""
    job = db.query(Job).get(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    profile = db.query(UserProfile).first()
    if not profile:
        raise ValueError("No UserProfile — set up profile first")

    cover_letter = await _generate_cover_letter(profile, job)

    # Resume path: use the default variant's most recent PDF, or generate one.
    # For now we point at a known asset path; PDF generation is triggered server-side.
    resume_pdf_path = str(
        settings.data_dir / "assets" / f"resume_{profile.id}_{job.id}.pdf"
    )

    return {
        "job_id": job.id,
        "company_name": job.company_name,
        "role_title": job.role_title,
        "fit_score": job.fit_score,
        "ats_type": job.ats_type,
        "apply_url": job.apply_url,
        "form_data": {
            "name": profile.name or "",
            "email": profile.email or "",
            "phone": profile.phone or "",
            "linkedin_url": profile.linkedin_url or "",
            "resume_pdf_path": resume_pdf_path,
            "cover_letter_text": cover_letter,
            "custom_answers": {},
        },
        "cover_letter_text": cover_letter,
    }


async def run_submit_application(db: Session, job_id: int, form_data: dict) -> dict:
    """Submit the application. form_data is the user-approved payload."""
    job = db.query(Job).get(job_id)
    if not job:
        return {"success": False, "error": f"Job {job_id} not found"}

    job.application_status = "applying"
    db.commit()

    try:
        filler = get_form_filler(job.ats_type, browser=get_browser_service())
    except UnsupportedATSError as e:
        job.application_status = "failed"
        db.add(ApplicationAttempt(
            job_id=job.id,
            status="failed",
            error_message=str(e),
            form_data=form_data,
        ))
        db.commit()
        return {"success": False, "error": str(e)}

    data = ApplicationData(
        name=form_data["name"],
        email=form_data["email"],
        phone=form_data["phone"],
        linkedin_url=form_data["linkedin_url"],
        resume_pdf_path=form_data["resume_pdf_path"],
        cover_letter_text=form_data["cover_letter_text"],
        custom_answers=form_data.get("custom_answers", {}),
    )

    result = await filler.fill(job.apply_url, data)

    db.add(ApplicationAttempt(
        job_id=job.id,
        status="success" if result.success else "failed",
        cover_letter_text=form_data["cover_letter_text"],
        form_data=form_data,
        confirmation_text=result.confirmation_text,
        screenshot_path=result.screenshot_path,
        error_message=result.error_message,
    ))
    job.application_status = "applied" if result.success else "failed"
    db.commit()

    return {
        "success": result.success,
        "confirmation_text": result.confirmation_text,
        "screenshot_path": result.screenshot_path,
        "error_message": result.error_message,
    }
