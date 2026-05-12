import pytest
from unittest.mock import AsyncMock, patch

from app.agents.profile_ingest import (
    ProfileIngestAgent,
    ProfileIngestInput,
    ProfileIngestOutput,
    ExtractedExperience,
    ExtractedSkill,
)
from app.services.claude import ClaudeService


@pytest.mark.asyncio
async def test_profile_ingest_returns_structured_output():
    service = ClaudeService(api_key="test")
    agent = ProfileIngestAgent(service)

    mock_output = ProfileIngestOutput(
        name="Abhishek Chatterjee",
        email="test@example.com",
        location="Bangalore, India",
        experiences=[
            ExtractedExperience(
                company_name="Einstein Labs",
                role_title="Founder",
                type="founder",
                is_current=True,
                bullet_points=["Built AI agent products", "Designed venture studio model"],
                skills_used=["AI/ML", "Product Strategy"],
            )
        ],
        skills=[
            ExtractedSkill(name="Product Strategy", category="product", proficiency="expert"),
        ],
    )

    with patch.object(agent, "run", new_callable=AsyncMock, return_value=mock_output):
        result = await agent.run(
            ProfileIngestInput(raw_content="LinkedIn text..."),
            ProfileIngestOutput,
        )
        assert result.name == "Abhishek Chatterjee"
        assert len(result.experiences) == 1
        assert result.experiences[0].company_name == "Einstein Labs"
