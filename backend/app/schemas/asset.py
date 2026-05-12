from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssetUpdate(BaseModel):
    tailored_summary: Optional[str] = None
    tailored_bullets: Optional[dict] = None
    cover_letter: Optional[str] = None
    linkedin_message: Optional[str] = None
    email_message: Optional[str] = None
    application_answers: Optional[dict] = None


class AssetResponse(BaseModel):
    id: int
    job_id: int
    resume_variant_id: Optional[int] = None
    tailored_summary: Optional[str] = None
    tailored_bullets: Optional[dict] = None
    cover_letter: Optional[str] = None
    linkedin_message: Optional[str] = None
    email_message: Optional[str] = None
    application_answers: Optional[dict] = None
    pdf_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
