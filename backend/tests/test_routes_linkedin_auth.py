"""Tests for LinkedIn auth endpoints."""
from unittest.mock import patch, AsyncMock


def test_start_auth_returns_session_id(client):
    with patch("app.routes.settings.asyncio") as mock_asyncio, \
         patch("app.routes.settings.open_login_window"):
        mock_asyncio.create_task = lambda coro: None
        mock_asyncio.get_event_loop = lambda: None
        resp = client.post("/api/settings/linkedin/start-auth")
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert len(body["session_id"]) == 36  # uuid4 format


def test_auth_status_waiting(client):
    from app.services.browser import _auth_sessions
    _auth_sessions["test-wait-id"] = {"status": "waiting"}
    resp = client.get("/api/settings/linkedin/auth-status/test-wait-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "waiting"


def test_auth_status_connected(client):
    from app.services.browser import _auth_sessions
    _auth_sessions["test-conn-id"] = {"status": "connected"}
    resp = client.get("/api/settings/linkedin/auth-status/test-conn-id")
    assert resp.status_code == 200
    assert resp.json()["status"] == "connected"


def test_auth_status_unknown_session_returns_404(client):
    resp = client.get("/api/settings/linkedin/auth-status/nonexistent-id")
    assert resp.status_code == 404


def test_disconnect_clears_cookie_and_status(client):
    # First set a cookie
    client.put("/api/settings", json={"linkedin_cookie": "fake-cookie"})
    resp = client.delete("/api/settings/linkedin/disconnect")
    assert resp.status_code == 200
    # Verify cookie cleared
    settings = client.get("/api/settings").json()
    assert settings["linkedin_cookie_present"] is False
    # Verify status
    prefs = client.get("/api/settings/preferences").json()
    assert prefs["linkedin_auth_status"] == "disconnected"
