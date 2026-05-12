from typing import Optional

from pydantic import BaseModel

from app.agents.base import BaseAgent


class ExtractedExperience(BaseModel):
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    location: Optional[str] = None
    bullet_points: list[str] = []
    skills_used: list[str] = []


class ExtractedProject(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    repo_url: Optional[str] = None
    outcome: Optional[str] = None
    technologies: list[str] = []
    ai_techniques: list[str] = []


class ExtractedSkill(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None
    years_of_experience: Optional[int] = None


class ExtractedEducation(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None


class ProfileIngestInput(BaseModel):
    raw_content: str


class ProfileIngestOutput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    experiences: list[ExtractedExperience] = []
    projects: list[ExtractedProject] = []
    skills: list[ExtractedSkill] = []
    education: list[ExtractedEducation] = []


class ProfileIngestAgent(BaseAgent[ProfileIngestInput, ProfileIngestOutput]):
    name = "profile_ingest"
    prompt_file = "profile_ingest.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: ProfileIngestInput) -> str:
        return f"## Raw Source Material\n\n{input_data.raw_content}"
