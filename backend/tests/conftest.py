"""
Shared test configuration.

Each test module that needs a FastAPI test client uses the `client` fixture
defined here via conftest. The fixture:
  1. Creates a single shared SQLite connection for the test (using a named
     file-based URI so all sessions share the same in-process database).
  2. Creates all tables on that connection.
  3. Overrides the `get_db` dependency to return sessions bound to that
     shared connection.
  4. Tears everything down after each test.

Note: We use a single shared connection bound to every session so that
SQLite's in-memory database is visible to all sessions (each new :memory:
connection gets its own empty database, which would cause "no such table").
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # Use a single connection; bind all sessions to it so SQLite in-memory
    # tables are visible across the entire test.
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

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Teardown
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=connection)
    connection.close()
    test_engine.dispose()
