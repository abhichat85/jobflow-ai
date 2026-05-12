from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.profile import Experience, Project, Skill, UserProfile
from app.models.resume import ResumeVariant
from app.schemas.profile import (
    ExperienceCreate,
    ExperienceResponse,
    ProfileResponse,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ResumeVariantResponse,
    ResumeVariantUpdate,
    SkillCreate,
    SkillResponse,
)

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
