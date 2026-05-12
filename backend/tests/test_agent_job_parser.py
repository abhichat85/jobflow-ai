import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.job_parser import JobParserAgent, JobParseInput, JobParseOutput
from app.services.claude import ClaudeService


@pytest.mark.asyncio
async def test_job_parser_returns_structured_output():
    service = ClaudeService(api_key="test")
    agent = JobParserAgent(service)

    mock_output = JobParseOutput(
        company_name="Acme AI",
        role_title="AI Product Manager",
        location="Remote",
        remote_type="remote",
        salary_min=150000,
        salary_max=200000,
        salary_currency="USD",
        company_stage="series_a",
        company_size="50-100",
        company_industry="AI/ML",
        must_have_skills=["Product Management", "AI/ML"],
        nice_to_have_skills=["LangChain"],
        years_experience_required=3,
        education_requirements=None,
        key_responsibilities=["Own AI product roadmap"],
        culture_signals=["Fast-paced", "Ownership culture"],
        red_flags=[],
    )

    with patch.object(agent, "run", new_callable=AsyncMock, return_value=mock_output):
        result = await agent.run(
            JobParseInput(raw_text="We are looking for an AI PM..."),
            JobParseOutput,
        )
        assert result.company_name == "Acme AI"
        assert "Product Management" in result.must_have_skills
