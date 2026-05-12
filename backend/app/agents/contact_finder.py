from pydantic import BaseModel

from app.agents.base import BaseAgent


class ContactFinderInput(BaseModel):
    company_name: str
    role_title: str
    company_url: str | None = None


class FoundContact(BaseModel):
    name: str
    title: str
    relevance: str
    suggested_channel: str


class ContactFinderOutput(BaseModel):
    contacts: list[FoundContact]


class ContactFinderAgent(BaseAgent[ContactFinderInput, ContactFinderOutput]):
    name = "contact_finder"
    prompt_file = "contact_finder.md"
    model = "claude-sonnet-4-20250514"

    def build_user_prompt(self, input_data: ContactFinderInput) -> str:
        return f"""Company: {input_data.company_name}
Role being applied to: {input_data.role_title}
Company URL: {input_data.company_url or 'N/A'}"""
