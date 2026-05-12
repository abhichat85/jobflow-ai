from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.agents.profile_ingest import (
    ExtractedEducation,
    ExtractedExperience,
    ExtractedProject,
    ExtractedSkill,
)


class SynthesizedVariant(BaseModel):
    variant_name: str
    positioning_statement: str
    summary_text: str
    target_role_types: list[str] = []
    key_experiences: list[str] = []


class ProfileSynthesisInput(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    experiences: list[ExtractedExperience] = []
    projects: list[ExtractedProject] = []
    skills: list[ExtractedSkill] = []
    education: list[ExtractedEducation] = []


class ProfileSynthesisOutput(BaseModel):
    positioning_statement: str
    bio: str
    career_narrative: str
    differentiators: list[str] = []
    target_roles: list[str] = []
    target_locations: list[str] = []
    work_preference: str = "remote"
    variants: list[SynthesizedVariant] = []
    ats_keywords: list[str] = []


class ProfileSynthesisAgent(BaseAgent[ProfileSynthesisInput, ProfileSynthesisOutput]):
    name = "profile_synthesis"
    prompt_file = "profile_synthesis.md"
    model = "claude-opus-4-20250514"

    def build_user_prompt(self, input_data: ProfileSynthesisInput) -> str:
        exp_lines = []
        for e in input_data.experiences:
            exp_lines.append(f"- {e.role_title} at {e.company_name} ({e.type})")
            for bp in e.bullet_points[:5]:
                exp_lines.append(f"  - {bp}")

        proj_lines = [f"- {p.name}: {p.description or ''}" for p in input_data.projects]
        skill_lines = [
            f"- {s.name} ({s.category or 'general'}, {s.proficiency or 'unknown'})"
            for s in input_data.skills
        ]

        return f"""## Candidate
Name: {input_data.name or 'Unknown'}
Location: {input_data.location or 'Unknown'}

## Experiences
{chr(10).join(exp_lines) if exp_lines else 'None'}

## Projects
{chr(10).join(proj_lines) if proj_lines else 'None'}

## Skills
{chr(10).join(skill_lines) if skill_lines else 'None'}

## Education
{chr(10).join(f'- {e.degree} in {e.field} from {e.institution}' for e in input_data.education) if input_data.education else 'None'}"""
