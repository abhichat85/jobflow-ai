from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class ResumeTailorInput(BaseModel):
    candidate_bio: str
    candidate_positioning: str
    experiences: list[dict]
    projects: list[dict]
    skills: list[str]
    variant_positioning: str
    variant_experience_ordering: list[int]
    job_description: str
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    key_responsibilities: list[str]


class ResumeTailorOutput(BaseModel):
    summary: str
    experience_bullets: dict[str, list[str]]
    skills_to_highlight: list[str]


class ResumeTailorAgent(BaseAgent[ResumeTailorInput, ResumeTailorOutput]):
    name = "resume_tailor"
    prompt_file = "resume_tailor.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: ResumeTailorInput) -> str:
        exp_section = ""
        for exp in input_data.experiences:
            exp_section += f"\n### {exp.get('role_title', '')} at {exp.get('company_name', '')}\n"
            exp_section += f"ID: {exp.get('id', '')}\n"
            for bp in exp.get("bullet_points", []):
                exp_section += f"- {bp}\n"

        return f"""## Candidate Profile
Bio: {input_data.candidate_bio}
Positioning: {input_data.candidate_positioning}

## Experiences
{exp_section}

## Skills
{', '.join(input_data.skills)}

## Resume Variant Positioning
{input_data.variant_positioning}

## Job Description
{input_data.job_description}

## Required Skills: {', '.join(input_data.must_have_skills)}
## Nice-to-Have: {', '.join(input_data.nice_to_have_skills)}
## Key Responsibilities:
{chr(10).join('- ' + r for r in input_data.key_responsibilities)}"""
