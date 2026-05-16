import json
from typing import Optional
from pydantic import BaseModel, field_validator


class PreferencesResponse(BaseModel):
    job_titles: list[str]
    locations: list[str]
    remote_preference: str
    seniority_levels: list[str]
    company_stage: str
    min_salary: Optional[int]
    linkedin_auth_status: str
    linkedin_search_urls: list[str]
    linkedin_search_url: Optional[str]  # legacy field for backward compat

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    job_titles: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    remote_preference: Optional[str] = None
    seniority_levels: Optional[list[str]] = None
    company_stage: Optional[str] = None
    min_salary: Optional[int] = None
