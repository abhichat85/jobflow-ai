import pytest
from unittest.mock import AsyncMock, patch

from app.agents.profile_synthesis import (
    ProfileSynthesisAgent,
    ProfileSynthesisInput,
    ProfileSynthesisOutput,
    SynthesizedVariant,
)
from app.services.claude import ClaudeService


@pytest.mark.asyncio
async def test_profile_synthesis_returns_positioning():
    service = ClaudeService(api_key="test")
    agent = ProfileSynthesisAgent(service)

    mock_output = ProfileSynthesisOutput(
        positioning_statement="AI-native product builder with founder credentials",
        bio="I am a builder who...",
        career_narrative="My career has been a single thread of building AI products...",
        differentiators=["Shipped 4 AI agent products", "Founded venture studio"],
        target_roles=["AI Product Manager", "Founding PM"],
        target_locations=["Remote", "Bangalore"],
        work_preference="remote",
        variants=[
            SynthesizedVariant(
                variant_name="ai_pm",
                positioning_statement="AI PM angle",
                summary_text="Summary",
            )
        ],
        ats_keywords=["LLM", "Product Strategy"],
    )

    with patch.object(agent, "run", new_callable=AsyncMock, return_value=mock_output):
        result = await agent.run(
            ProfileSynthesisInput(name="Test", experiences=[]),
            ProfileSynthesisOutput,
        )
        assert result.positioning_statement == "AI-native product builder with founder credentials"
        assert len(result.variants) == 1
