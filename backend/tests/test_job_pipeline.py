import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.profile import UserProfile
from app.models.resume import ResumeVariant


@pytest.fixture()
def client_with_profile():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    connection = test_engine.connect()
    Base.metadata.create_all(bind=connection)

    TestSession = sessionmaker(bind=connection)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed profile and resume variant
    db = TestSession()
    profile = UserProfile(
        name="Abhishek",
        email="test@test.com",
        positioning_statement="AI product builder",
        target_roles=["AI PM"],
        work_preference="remote",
    )
    db.add(profile)
    db.commit()
    variant = ResumeVariant(
        user_profile_id=profile.id,
        variant_name="ai_pm",
        positioning_statement="AI product builder",
    )
    db.add(variant)
    db.commit()
    db.close()

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=connection)
    connection.close()
    test_engine.dispose()


def test_create_job_from_jd(client_with_profile):
    resp = client_with_profile.post("/api/jobs", json={
        "job_description": "We need an AI PM...",
        "company_name": "Acme",
        "role_title": "AI PM",
        "source": "linkedin",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "discovered"
