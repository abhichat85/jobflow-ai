from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class OutreachInput(BaseModel):
    candidate_name: str
    candidate_positioning: str
    candidate_experience_summary: str
    company_name: str
    role_title: str
    job_description: str
    contact_name: str
    contact_title: str
    outreach_angle: str


class OutreachOutput(BaseModel):
    linkedin_message: str
    email_message: str
    email_subject: str
    twitter_message: str


class OutreachWriterAgent(BaseAgent[OutreachInput, OutreachOutput]):
    name = "outreach_writer"
    prompt_file = "outreach.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: OutreachInput) -> str:
        return f"""## Candidate
Name: {input_data.candidate_name}
Positioning: {input_data.candidate_positioning}
Experience: {input_data.candidate_experience_summary}

## Target
Company: {input_data.company_name}
Role: {input_data.role_title}
Contact: {input_data.contact_name} ({input_data.contact_title})
Outreach Angle: {input_data.outreach_angle}

## Job Description
{input_data.job_description}"""
