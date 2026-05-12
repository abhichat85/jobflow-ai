from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InterviewCreate(BaseModel):
    job_id: int
    contact_id: Optional[int] = None
    company_name: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_stage: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_title: Optional[str] = None


class InterviewUpdate(BaseModel):
    interview_date: Optional[datetime] = None
    interview_stage: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_title: Optional[str] = None
    status: Optional[str] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    feedback: Optional[str] = None


class InterviewResponse(BaseModel):
    id: int
    job_id: int
    contact_id: Optional[int] = None
    company_name: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_stage: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_title: Optional[str] = None
    prep_doc_path: Optional[str] = None
    status: str
    outcome: str
    notes: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewPrepResponse(BaseModel):
    id: int
    interview_id: int
    job_id: int
    company_brief: Optional[str] = None
    product_analysis: Optional[str] = None
    role_analysis: Optional[str] = None
    likely_questions: Optional[list] = None
    suggested_answers: Optional[list] = None
    talking_points: Optional[list] = None
    questions_to_ask: Optional[list] = None
    thirty_sixty_ninety_plan: Optional[str] = None
    salary_negotiation_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
