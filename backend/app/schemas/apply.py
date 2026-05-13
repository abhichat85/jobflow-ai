from typing import Optional

from pydantic import BaseModel


class ApplyFormData(BaseModel):
    name: str
    email: str
    phone: str = ""
    linkedin_url: str = ""
    resume_pdf_path: str
    cover_letter_text: str
    custom_answers: dict[str, str] = {}


class ApplyPreviewResponse(BaseModel):
    job_id: int
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    fit_score: Optional[int] = None
    ats_type: Optional[str] = None
    apply_url: Optional[str] = None
    form_data: dict
    cover_letter_text: str


class ApplySubmitResponse(BaseModel):
    status: str
    task_id: str
