from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContactCreate(BaseModel):
    company_name: Optional[str] = None
    name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    twitter_handle: Optional[str] = None
    source: Optional[str] = None
    relationship_strength: str = "cold"
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    twitter_handle: Optional[str] = None
    relationship_strength: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: int
    company_name: Optional[str] = None
    name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    twitter_handle: Optional[str] = None
    source: Optional[str] = None
    relationship_strength: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutreachCreate(BaseModel):
    job_id: Optional[int] = None
    contact_id: int
    channel: str
    message_type: str = "initial"
    message: Optional[str] = None
    subject: Optional[str] = None


class OutreachUpdate(BaseModel):
    message: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OutreachResponse(BaseModel):
    id: int
    job_id: Optional[int] = None
    contact_id: int
    channel: str
    message_type: str
    message: Optional[str] = None
    subject: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    scheduled_followup_at: Optional[datetime] = None
    reply_received_at: Optional[datetime] = None
    reply_summary: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutreachGenerateRequest(BaseModel):
    job_id: int
    contact_id: int
    channel: str = "linkedin"
