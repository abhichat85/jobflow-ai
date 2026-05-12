from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class CoverLetterInput(BaseModel):
    candidate_name: str
    candidate_positioning: str
    candidate_experience_summary: str
    job_description: str
    company_name: str
    role_title: str
    resume_angle: str


class CoverLetterOutput(BaseModel):
    cover_letter: str
    linkedin_message: str
    email_message: str
    application_answers: dict[str, str]


class CoverLetterAgent(BaseAgent[CoverLetterInput, CoverLetterOutput]):
    name = "cover_letter"
    prompt_file = "cover_letter.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: CoverLetterInput) -> str:
        return f"""## Candidate
Name: {input_data.candidate_name}
Positioning: {input_data.candidate_positioning}
Experience Summary: {input_data.candidate_experience_summary}
Resume Angle: {input_data.resume_angle}

## Job
Company: {input_data.company_name}
Role: {input_data.role_title}

## Job Description
{input_data.job_description}"""
