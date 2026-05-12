from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ExperienceCreate(BaseModel):
    type: Optional[str] = None
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    bullet_points: Optional[list[str]] = None
    skills_used: Optional[list[str]] = None
    technologies: Optional[list[str]] = None
    achievements: Optional[list[str]] = None
    metrics: Optional[list[str]] = None
    sort_order: int = 0


class ExperienceResponse(ExperienceCreate):
    id: int
    user_profile_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    experience_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    repo_url: Optional[str] = None
    problem_statement: Optional[str] = None
    solution_summary: Optional[str] = None
    outcome: Optional[str] = None
    technologies: Optional[list[str]] = None
    ai_techniques: Optional[list[str]] = None
    is_featured: bool = False
    sort_order: int = 0


class ProjectResponse(ProjectCreate):
    id: int
    user_profile_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None
    years_of_experience: Optional[int] = None
    is_primary: bool = False


class SkillResponse(SkillCreate):
    id: int
    user_profile_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeVariantUpdate(BaseModel):
    positioning_statement: Optional[str] = None
    summary_text: Optional[str] = None
    target_role_types: Optional[list[str]] = None
    experience_ordering: Optional[list[int]] = None
    bullet_overrides: Optional[dict] = None


class ResumeVariantResponse(BaseModel):
    id: int
    user_profile_id: int
    variant_name: str
    positioning_statement: Optional[str] = None
    summary_text: Optional[str] = None
    target_role_types: Optional[list[str]] = None
    experience_ordering: Optional[list[int]] = None
    bullet_overrides: Optional[dict] = None
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    target_roles: Optional[list[str]] = None
    target_locations: Optional[list[str]] = None
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    currency: Optional[str] = None
    work_preference: Optional[str] = None
    notice_period: Optional[str] = None
    positioning_statement: Optional[str] = None
    bio: Optional[str] = None
    career_narrative: Optional[str] = None
    differentiators: Optional[list[str]] = None
    ats_keywords: Optional[list[str]] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    target_roles: Optional[list[str]] = None
    target_locations: Optional[list[str]] = None
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    currency: str = "INR"
    work_preference: Optional[str] = None
    notice_period: Optional[str] = None
    positioning_statement: Optional[str] = None
    bio: Optional[str] = None
    career_narrative: Optional[str] = None
    differentiators: Optional[list[str]] = None
    ats_keywords: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileIngestRequest(BaseModel):
    linkedin_text: Optional[str] = None
    resume_text: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    writing_samples: Optional[list[str]] = None
    additional_context: Optional[str] = None
