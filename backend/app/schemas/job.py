from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobCreate(BaseModel):
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    job_url: Optional[str] = None
    source: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    company_stage: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    company_url: Optional[str] = None


class JobUpdate(BaseModel):
    status: Optional[str] = None
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    notes: Optional[str] = None


class JobBulkCreate(BaseModel):
    urls: list[str]


class JobRequirementResponse(BaseModel):
    id: int
    job_id: int
    must_have_skills: Optional[list[str]] = None
    nice_to_have_skills: Optional[list[str]] = None
    years_experience_required: Optional[int] = None
    education_requirements: Optional[str] = None
    key_responsibilities: Optional[list[str]] = None
    culture_signals: Optional[list[str]] = None
    red_flags: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobScoreResponse(BaseModel):
    id: int
    job_id: int
    role_match: int
    skill_match: int
    startup_fit: int
    ai_relevance: int
    location_fit: int
    speed_of_hiring: int
    compensation_fit: int
    total_score: int
    decision: Optional[str] = None
    reasoning: Optional[str] = None
    resume_angle: Optional[str] = None
    outreach_angle: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: int
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    job_url: Optional[str] = None
    source: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    company_stage: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    company_url: Optional[str] = None
    status: str
    fit_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobDetailResponse(JobResponse):
    requirements: list[JobRequirementResponse] = []
    scores: list[JobScoreResponse] = []
