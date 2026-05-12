import pytest
from unittest.mock import AsyncMock, patch

from app.agents.job_scorer import JobScorerAgent, JobScoreInput, JobScoreOutput
from app.services.claude import ClaudeService


@pytest.mark.asyncio
async def test_job_scorer_returns_score():
    service = ClaudeService(api_key="test")
    agent = JobScorerAgent(service)

    mock_output = JobScoreOutput(
        role_match=22,
        skill_match=18,
        startup_fit=12,
        ai_relevance=14,
        location_fit=8,
        speed_of_hiring=7,
        compensation_fit=4,
        total_score=85,
        decision="apply",
        reasoning="Strong fit for AI PM role at early-stage startup",
        resume_angle="ai_pm",
        outreach_angle="Focus on AI agent building experience",
    )

    with patch.object(agent, "run", new_callable=AsyncMock, return_value=mock_output):
        result = await agent.run(
            JobScoreInput(
                job_description="AI PM role...",
                role_title="AI Product Manager",
                company_name="Acme",
                must_have_skills=["Product Management"],
                candidate_summary="AI product builder...",
                candidate_skills=["Product Strategy", "AI/ML"],
                candidate_target_roles=["AI PM"],
                candidate_work_preference="remote",
                candidate_target_locations=["Remote", "Bangalore"],
            ),
            JobScoreOutput,
        )
        assert result.total_score == 85
        assert result.decision == "apply"
