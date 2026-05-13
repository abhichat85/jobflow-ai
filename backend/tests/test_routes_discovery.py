from unittest.mock import patch


def test_get_discovery_status_returns_defaults(client):
    resp = client.get("/api/discovery/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert body["interval_hours"] == 6
    assert body["last_run_at"] is None
    assert body["last_count"] is None


def test_run_discovery_enqueues_task(client):
    fake_task = type("T", (), {"id": "abc-123"})()
    with patch("app.tasks.discover_jobs.delay", return_value=fake_task):
        resp = client.post("/api/discovery/run")
    assert resp.status_code == 200
    assert resp.json()["status"] == "started"
    assert resp.json()["task_id"] == "abc-123"
