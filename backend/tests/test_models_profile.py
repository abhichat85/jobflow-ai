import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.profile import UserProfile, Experience, Project, Skill
from app.models.resume import ResumeVariant


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_create_user_profile(db):
    profile = UserProfile(
        name="Abhishek Chatterjee",
        email="test@example.com",
        location="Bangalore",
        target_roles=["AI Product Manager", "Founding PM"],
        work_preference="remote",
        positioning_statement="AI product builder",
    )
    db.add(profile)
    db.commit()
    assert profile.id is not None
    assert profile.target_roles == ["AI Product Manager", "Founding PM"]


def test_create_experience(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    exp = Experience(
        user_profile_id=profile.id,
        type="venture",
        company_name="Einstein Labs",
        role_title="Founder",
        is_current=True,
        bullet_points=["Built AI products", "Shipped MVPs"],
        skills_used=["Product Strategy", "AI"],
        technologies=["Python", "Next.js"],
    )
    db.add(exp)
    db.commit()
    assert exp.id is not None
    assert exp.bullet_points[0] == "Built AI products"


def test_create_project(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    project = Project(
        user_profile_id=profile.id,
        name="Pulse",
        description="Product intelligence system",
        technologies=["Next.js", "Claude API"],
        ai_techniques=["RAG", "Agent workflows"],
        is_featured=True,
    )
    db.add(project)
    db.commit()
    assert project.id is not None


def test_create_skill(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    skill = Skill(
        user_profile_id=profile.id,
        name="Product Strategy",
        category="product",
        proficiency="expert",
        years_of_experience=5,
        is_primary=True,
    )
    db.add(skill)
    db.commit()
    assert skill.id is not None


def test_create_resume_variant(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    variant = ResumeVariant(
        user_profile_id=profile.id,
        variant_name="ai_pm",
        positioning_statement="AI product builder",
        target_role_types=["AI PM", "LLM PM"],
        experience_ordering=[1, 2, 3],
    )
    db.add(variant)
    db.commit()
    assert variant.id is not None


def test_profile_relationships(db):
    profile = UserProfile(name="Test", email="t@t.com")
    db.add(profile)
    db.commit()

    exp = Experience(
        user_profile_id=profile.id,
        type="employment",
        company_name="Acme",
        role_title="PM",
    )
    skill = Skill(
        user_profile_id=profile.id,
        name="Python",
        category="technical",
        proficiency="advanced",
    )
    db.add_all([exp, skill])
    db.commit()

    db.refresh(profile)
    assert len(profile.experiences) == 1
    assert len(profile.skills) == 1
