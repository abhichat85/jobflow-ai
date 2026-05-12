from pydantic import BaseModel

from app.agents.base import BaseAgent


class FollowupInput(BaseModel):
    original_message: str
    channel: str
    days_since_sent: int
    followup_number: int
    company_name: str
    role_title: str
    contact_name: str
    candidate_positioning: str


class FollowupOutput(BaseModel):
    message: str
    subject: str | None = None


class FollowupWriterAgent(BaseAgent[FollowupInput, FollowupOutput]):
    name = "followup_writer"
    prompt_file = "followup.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: FollowupInput) -> str:
        return f"""## Original Message
Channel: {input_data.channel}
{input_data.original_message}

## Context
Days since sent: {input_data.days_since_sent}
Follow-up number: {input_data.followup_number}
Company: {input_data.company_name}
Role: {input_data.role_title}
Contact: {input_data.contact_name}

## Candidate
{input_data.candidate_positioning}"""
