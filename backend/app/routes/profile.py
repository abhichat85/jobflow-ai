from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.profile_ingest import ProfileIngestAgent, ProfileIngestInput, ProfileIngestOutput
from app.agents.profile_synthesis import ProfileSynthesisAgent, ProfileSynthesisInput, ProfileSynthesisOutput
from app.database import get_db
from app.models.profile import Experience, Project, Skill, UserProfile
from app.models.resume import ResumeVariant
from app.schemas.profile import (
    ExperienceCreate,
    ExperienceResponse,
    ProfileIngestRequest,
    ProfileResponse,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ResumeVariantResponse,
    ResumeVariantUpdate,
    SkillCreate,
    SkillResponse,
)
from app.services.claude import ClaudeService
from app.services.scraper import ScraperService

router = APIRouter(prefix="/api/profile", tags=["profile"])

VARIANT_NAMES = [
    "ai_pm",
    "founding_pm",
    "ai_consultant",
    "founders_office",
    "growth_generalist",
]


def get_or_create_profile(db: Session) -> UserProfile:
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(name="", email="")
        db.add(profile)
        db.commit()
        db.refresh(profile)
        for vname in VARIANT_NAMES:
            db.add(ResumeVariant(user_profile_id=profile.id, variant_name=vname))
        db.commit()
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    return get_or_create_profile(db)


@router.put("", response_model=ProfileResponse)
def update_profile(data: ProfileUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/experiences", response_model=list[ExperienceResponse])
def list_experiences(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return (
        db.query(Experience)
        .filter(Experience.user_profile_id == profile.id)
        .order_by(Experience.sort_order)
        .all()
    )


@router.post("/experiences", response_model=ExperienceResponse)
def create_experience(data: ExperienceCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    exp = Experience(user_profile_id=profile.id, **data.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.put("/experiences/{exp_id}", response_model=ExperienceResponse)
def update_experience(exp_id: int, data: ExperienceCreate, db: Session = Depends(get_db)):
    exp = db.query(Experience).get(exp_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exp, key, value)
    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/experiences/{exp_id}")
def delete_experience(exp_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experience).get(exp_id)
    db.delete(exp)
    db.commit()
    return {"ok": True}


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return db.query(Project).filter(Project.user_profile_id == profile.id).all()


@router.post("/projects", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    proj = Project(user_profile_id=profile.id, **data.model_dump())
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.put("/projects/{proj_id}", response_model=ProjectResponse)
def update_project(proj_id: int, data: ProjectCreate, db: Session = Depends(get_db)):
    proj = db.query(Project).get(proj_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(proj, key, value)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/skills", response_model=list[SkillResponse])
def list_skills(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return db.query(Skill).filter(Skill.user_profile_id == profile.id).all()


@router.post("/skills", response_model=SkillResponse)
def create_skill(data: SkillCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    skill = Skill(user_profile_id=profile.id, **data.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/resume-variants", response_model=list[ResumeVariantResponse])
def list_resume_variants(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return (
        db.query(ResumeVariant)
        .filter(ResumeVariant.user_profile_id == profile.id)
        .all()
    )


@router.put("/resume-variants/{variant_id}", response_model=ResumeVariantResponse)
def update_resume_variant(
    variant_id: int, data: ResumeVariantUpdate, db: Session = Depends(get_db)
):
    variant = db.query(ResumeVariant).get(variant_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, key, value)
    db.commit()
    db.refresh(variant)
    return variant


@router.post("/ingest", response_model=ProfileResponse)
async def ingest_profile(data: ProfileIngestRequest, db: Session = Depends(get_db)):
    """Ingest raw profile sources, extract structured data, and synthesize positioning."""

    # Step 1: Gather all source text
    sources: list[tuple[str, str]] = []
    if data.linkedin_text:
        sources.append(("LinkedIn", data.linkedin_text))
    if data.resume_text:
        sources.append(("Resume", data.resume_text))
    if data.writing_samples:
        for i, sample in enumerate(data.writing_samples):
            if sample.strip():
                sources.append((f"Writing Sample {i+1}", sample))
    if data.additional_context:
        sources.append(("Additional Context", data.additional_context))

    # Step 2: Scrape URLs if provided
    scraper = ScraperService()
    if data.github_url:
        try:
            content = await scraper.scrape_url(data.github_url)
            sources.append((f"GitHub ({data.github_url})", content[:8000]))
        except Exception:
            sources.append(("GitHub URL", data.github_url))
    if data.website_url:
        try:
            content = await scraper.scrape_url(data.website_url)
            sources.append((f"Website ({data.website_url})", content[:8000]))
        except Exception:
            sources.append(("Website URL", data.website_url))

    if not sources:
        raise HTTPException(status_code=400, detail="At least one source is required")

    combined = "\n\n".join(f"## Source: {label}\n\n{content}" for label, content in sources)

    # Step 3: Extract structured data
    claude = ClaudeService()
    ingest_agent = ProfileIngestAgent(claude)
    extracted = await ingest_agent.run(
        ProfileIngestInput(raw_content=combined),
        ProfileIngestOutput,
    )

    # Step 4: Synthesize positioning
    synth_agent = ProfileSynthesisAgent(claude)
    synthesized = await synth_agent.run(
        ProfileSynthesisInput(
            name=extracted.name,
            location=extracted.location,
            experiences=extracted.experiences,
            projects=extracted.projects,
            skills=extracted.skills,
            education=extracted.education,
        ),
        ProfileSynthesisOutput,
    )

    # Step 5: Get or create profile
    profile = db.query(UserProfile).first()
    if not profile:
        profile = UserProfile(
            name=extracted.name or "Unknown",
            email=extracted.email or "unknown@example.com",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Update profile fields (only overwrite if extracted/synthesized has a value)
    if extracted.name:
        profile.name = extracted.name
    if extracted.email:
        profile.email = extracted.email
    if extracted.phone:
        profile.phone = extracted.phone
    if extracted.location:
        profile.location = extracted.location
    if extracted.linkedin_url:
        profile.linkedin_url = extracted.linkedin_url
    if extracted.github_url:
        profile.github_url = extracted.github_url
    if extracted.website_url:
        profile.portfolio_url = extracted.website_url

    profile.positioning_statement = synthesized.positioning_statement
    profile.bio = synthesized.bio
    profile.career_narrative = synthesized.career_narrative
    profile.differentiators = synthesized.differentiators
    profile.ats_keywords = synthesized.ats_keywords
    profile.target_roles = synthesized.target_roles
    profile.target_locations = synthesized.target_locations
    profile.work_preference = synthesized.work_preference

    db.commit()
    db.refresh(profile)

    # Step 6: Replace experiences
    db.query(Experience).filter(Experience.user_profile_id == profile.id).delete()
    db.commit()

    for idx, exp in enumerate(extracted.experiences):
        def _parse_date(s):
            if not s:
                return None
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(s, "%Y-%m").date()
                except (ValueError, TypeError):
                    return None

        db_exp = Experience(
            user_profile_id=profile.id,
            type=exp.type,
            company_name=exp.company_name,
            role_title=exp.role_title,
            start_date=_parse_date(exp.start_date),
            end_date=_parse_date(exp.end_date),
            is_current=exp.is_current,
            bullet_points=exp.bullet_points,
            skills_used=exp.skills_used,
            sort_order=idx,
        )
        db.add(db_exp)
    db.commit()

    # Step 7: Replace projects
    db.query(Project).filter(Project.user_profile_id == profile.id).delete()
    db.commit()

    for idx, proj in enumerate(extracted.projects):
        db_proj = Project(
            user_profile_id=profile.id,
            name=proj.name,
            description=proj.description,
            url=proj.url,
            repo_url=proj.repo_url,
            outcome=proj.outcome,
            technologies=proj.technologies,
            ai_techniques=proj.ai_techniques,
            sort_order=idx,
        )
        db.add(db_proj)
    db.commit()

    # Step 8: Replace skills
    db.query(Skill).filter(Skill.user_profile_id == profile.id).delete()
    db.commit()

    for skill in extracted.skills:
        db_skill = Skill(
            user_profile_id=profile.id,
            name=skill.name,
            category=skill.category,
            proficiency=skill.proficiency,
            years_of_experience=skill.years_of_experience,
        )
        db.add(db_skill)
    db.commit()

    # Step 9: Update resume variants with synthesized angles
    expected_variants = ["ai_pm", "founding_pm", "ai_consultant", "founders_office", "growth_generalist"]
    for variant_name in expected_variants:
        db_variant = db.query(ResumeVariant).filter(
            ResumeVariant.user_profile_id == profile.id,
            ResumeVariant.variant_name == variant_name,
        ).first()
        if not db_variant:
            db_variant = ResumeVariant(
                user_profile_id=profile.id,
                variant_name=variant_name,
            )
            db.add(db_variant)

        synth_variant = next((v for v in synthesized.variants if v.variant_name == variant_name), None)
        if synth_variant:
            db_variant.positioning_statement = synth_variant.positioning_statement
            db_variant.summary_text = synth_variant.summary_text
            db_variant.target_role_types = synth_variant.target_role_types

    db.commit()
    db.refresh(profile)
    return profile
