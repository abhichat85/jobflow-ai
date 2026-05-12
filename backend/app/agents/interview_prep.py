from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class InterviewPrepInput(BaseModel):
    candidate_bio: str
    candidate_positioning: str
    experiences: list[dict]
    projects: list[dict]
    skills: list[str]
    company_name: str
    company_url: Optional[str] = None
    job_description: str
    role_title: str
    interview_stage: str


class InterviewPrepOutput(BaseModel):
    company_brief: str
    product_analysis: str
    role_analysis: str
    likely_questions: list[dict]
    suggested_answers: list[dict]
    talking_points: list[str]
    questions_to_ask: list[str]
    thirty_sixty_ninety_plan: str
    salary_negotiation_notes: str


class InterviewPrepAgent(BaseAgent[InterviewPrepInput, InterviewPrepOutput]):
    name = "interview_prep"
    prompt_file = "interview_prep.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: InterviewPrepInput) -> str:
        exp_section = ""
        for exp in input_data.experiences:
            exp_section += f"\n- {exp.get('role_title', '')} at {exp.get('company_name', '')}"

        return f"""## Candidate
Bio: {input_data.candidate_bio}
Positioning: {input_data.candidate_positioning}
Experiences: {exp_section}
Skills: {', '.join(input_data.skills)}

## Interview
Company: {input_data.company_name}
URL: {input_data.company_url or 'N/A'}
Role: {input_data.role_title}
Stage: {input_data.interview_stage}

## Job Description
{input_data.job_description}"""
