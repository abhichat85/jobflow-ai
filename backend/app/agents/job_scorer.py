from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class JobScoreInput(BaseModel):
    job_description: str
    role_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    company_stage: Optional[str] = None
    must_have_skills: list[str] = []
    nice_to_have_skills: list[str] = []
    key_responsibilities: list[str] = []
    candidate_summary: str = ""
    candidate_skills: list[str] = []
    candidate_target_roles: list[str] = []
    candidate_work_preference: str = ""
    candidate_target_locations: list[str] = []
    candidate_salary_min: Optional[int] = None
    candidate_salary_max: Optional[int] = None


class JobScoreOutput(BaseModel):
    role_match: int
    skill_match: int
    startup_fit: int
    ai_relevance: int
    location_fit: int
    speed_of_hiring: int
    compensation_fit: int
    total_score: int
    decision: str
    reasoning: str
    resume_angle: str
    outreach_angle: str


class JobScorerAgent(BaseAgent[JobScoreInput, JobScoreOutput]):
    name = "job_scorer"
    prompt_file = "job_scorer.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: JobScoreInput) -> str:
        return f"""## Job Details
Title: {input_data.role_title}
Company: {input_data.company_name}
Location: {input_data.location} ({input_data.remote_type})
Salary: {input_data.salary_min}-{input_data.salary_max}
Company Stage: {input_data.company_stage}

## Job Description
{input_data.job_description}

## Required Skills
{', '.join(input_data.must_have_skills)}

## Nice-to-Have Skills
{', '.join(input_data.nice_to_have_skills)}

## Key Responsibilities
{chr(10).join('- ' + r for r in input_data.key_responsibilities)}

## Candidate Profile
Summary: {input_data.candidate_summary}
Skills: {', '.join(input_data.candidate_skills)}
Target Roles: {', '.join(input_data.candidate_target_roles)}
Work Preference: {input_data.candidate_work_preference}
Target Locations: {', '.join(input_data.candidate_target_locations)}
Salary Range: {input_data.candidate_salary_min}-{input_data.candidate_salary_max}"""
