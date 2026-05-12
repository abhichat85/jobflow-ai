from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.services.claude import ClaudeService


class JobParseInput(BaseModel):
    raw_text: str
    source_url: Optional[str] = None


class JobParseOutput(BaseModel):
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    company_stage: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    must_have_skills: list[str] = []
    nice_to_have_skills: list[str] = []
    years_experience_required: Optional[int] = None
    education_requirements: Optional[str] = None
    key_responsibilities: list[str] = []
    culture_signals: list[str] = []
    red_flags: list[str] = []


class JobParserAgent(BaseAgent[JobParseInput, JobParseOutput]):
    name = "job_parser"
    prompt_file = "job_parser.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: JobParseInput) -> str:
        parts = [f"## Job Description\n\n{input_data.raw_text}"]
        if input_data.source_url:
            parts.append(f"\nSource URL: {input_data.source_url}")
        return "\n".join(parts)
