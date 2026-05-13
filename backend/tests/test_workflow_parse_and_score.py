import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.job_parser import JobParseOutput
from app.agents.job_scorer import JobScoreOutput
from app.database import Base
from app.models.job import Job, JobRequirement, JobScore
from app.models.profile import UserProfile
from app.models.settings import UserSettings
from app.workflows.parse_and_score import run_parse_and_score


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.mark.asyncio
async def test_parse_and_score_high_score_goes_to_review(db, monkeypatch):
    # Seed
    db.add(UserProfile(name="Test", email="t@t.com"))
    db.add(UserSettings(auto_review_threshold=65))
    job = Job(job_url="https://boards.greenhouse.io/co/jobs/1",
              job_description="AI PM role", application_status="discovered")
    db.add(job)
    db.commit()

    # Mock agents
    parsed = JobParseOutput(
        company_name="Anthropic",
        role_title="AI PM",
        must_have_skills=["Python", "LLM"],
    )
    scored = JobScoreOutput(
        role_match=18, skill_match=18, startup_fit=18, ai_relevance=18,
        location_fit=8, speed_of_hiring=10, compensation_fit=10,
        total_score=82, decision="apply", reasoning="strong fit",
        resume_angle="ai_pm", outreach_angle="ai builder"
    )

    with patch("app.workflows.parse_and_score.JobParserAgent") as mock_parser_cls, \
         patch("app.workflows.parse_and_score.JobScorerAgent") as mock_scorer_cls, \
         patch("app.workflows.parse_and_score.ClaudeService"):
        mock_parser_cls.return_value.run = AsyncMock(return_value=parsed)
        mock_scorer_cls.return_value.run = AsyncMock(return_value=scored)
        await run_parse_and_score(db, job.id)

    db.refresh(job)
    assert job.application_status == "pending_review"
    assert job.fit_score == 82
    assert job.ats_type == "greenhouse"
    assert db.query(JobRequirement).filter_by(job_id=job.id).count() == 1
    assert db.query(JobScore).filter_by(job_id=job.id).count() == 1


@pytest.mark.asyncio
async def test_parse_and_score_low_score_is_skipped(db, monkeypatch):
    db.add(UserProfile(name="Test", email="t@t.com"))
    db.add(UserSettings(auto_review_threshold=65))
    job = Job(job_url="https://example.com/x", job_description="bad fit",
              application_status="discovered")
    db.add(job)
    db.commit()

    parsed = JobParseOutput(company_name="X", role_title="QA Tester")
    scored = JobScoreOutput(
        role_match=5, skill_match=5, startup_fit=5, ai_relevance=2,
        location_fit=5, speed_of_hiring=5, compensation_fit=5,
        total_score=32, decision="skip", reasoning="weak fit",
        resume_angle="growth_generalist", outreach_angle=""
    )

    with patch("app.workflows.parse_and_score.JobParserAgent") as mock_parser_cls, \
         patch("app.workflows.parse_and_score.JobScorerAgent") as mock_scorer_cls, \
         patch("app.workflows.parse_and_score.ClaudeService"):
        mock_parser_cls.return_value.run = AsyncMock(return_value=parsed)
        mock_scorer_cls.return_value.run = AsyncMock(return_value=scored)
        await run_parse_and_score(db, job.id)

    db.refresh(job)
    assert job.application_status == "skipped"
    assert job.fit_score == 32
