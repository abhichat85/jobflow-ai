import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.profile import UserProfile
from app.models.resume import ResumeVariant
from app.models.job import Job, JobRequirement, JobScore
from app.models.asset import ApplicationAsset
from app.models.outreach import Contact, Outreach
from app.models.interview import Interview, InterviewPrep


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_create_job_with_requirements_and_score(db):
    job = Job(
        company_name="Acme AI",
        role_title="AI Product Manager",
        job_url="https://example.com/job/1",
        source="linkedin",
        job_description="We need an AI PM...",
        status="discovered",
    )
    db.add(job)
    db.commit()

    req = JobRequirement(
        job_id=job.id,
        must_have_skills=["Product Management", "AI/ML"],
        nice_to_have_skills=["LangChain"],
        years_experience_required=3,
        key_responsibilities=["Own the AI product roadmap"],
    )
    score = JobScore(
        job_id=job.id,
        role_match=22,
        skill_match=18,
        startup_fit=12,
        ai_relevance=14,
        location_fit=8,
        speed_of_hiring=7,
        compensation_fit=4,
        total_score=85,
        decision="apply",
        reasoning="Strong AI PM role at early-stage startup",
        resume_angle="ai_pm",
    )
    db.add_all([req, score])
    db.commit()

    assert req.id is not None
    assert score.total_score == 85
    assert score.decision == "apply"


def test_create_application_asset(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    variant = ResumeVariant(
        user_profile_id=profile.id,
        variant_name="ai_pm",
        positioning_statement="AI builder",
    )
    db.add(variant)
    db.commit()

    job = Job(company_name="Acme", role_title="PM", status="scored")
    db.add(job)
    db.commit()

    asset = ApplicationAsset(
        job_id=job.id,
        resume_variant_id=variant.id,
        tailored_summary="Experienced AI product builder...",
        cover_letter="Hi Team, ...",
        linkedin_message="Hey, ...",
        status="draft",
    )
    db.add(asset)
    db.commit()
    assert asset.id is not None
    assert asset.status == "draft"


def test_create_contact_and_outreach(db):
    job = Job(company_name="Acme", role_title="PM", status="ready")
    db.add(job)
    db.commit()

    contact = Contact(
        company_name="Acme",
        name="Jane Doe",
        title="CEO",
        linkedin_url="https://linkedin.com/in/janedoe",
        relationship_strength="cold",
    )
    db.add(contact)
    db.commit()

    outreach = Outreach(
        job_id=job.id,
        contact_id=contact.id,
        channel="linkedin",
        message_type="initial",
        message="Hey Jane, ...",
        status="draft",
    )
    db.add(outreach)
    db.commit()
    assert outreach.id is not None


def test_job_has_new_apply_fields(db):
    from app.models.job import Job
    job = Job(
        company_name="TestCo",
        role_title="AI PM",
        job_url="https://example.com/job/1",
        apply_url="https://boards.greenhouse.io/testco/jobs/1",
        ats_type="greenhouse",
        application_status="discovered",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    assert job.apply_url == "https://boards.greenhouse.io/testco/jobs/1"
    assert job.ats_type == "greenhouse"
    assert job.application_status == "discovered"


def test_create_interview_and_prep(db):
    job = Job(company_name="Acme", role_title="PM", status="applied")
    db.add(job)
    db.commit()

    interview = Interview(
        job_id=job.id,
        company_name="Acme",
        interview_stage="screening",
        interviewer_name="John",
        status="scheduled",
        outcome="pending",
    )
    db.add(interview)
    db.commit()

    prep = InterviewPrep(
        interview_id=interview.id,
        job_id=job.id,
        company_brief="Acme builds AI tools...",
        likely_questions=[{"q": "Tell me about yourself"}],
        questions_to_ask=["What's the biggest challenge?"],
        thirty_sixty_ninety_plan="First 30 days: ...",
    )
    db.add(prep)
    db.commit()
    assert prep.id is not None
