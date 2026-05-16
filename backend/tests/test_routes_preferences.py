"""Tests for GET/PUT /api/settings/preferences."""


def test_get_preferences_returns_defaults(client):
    resp = client.get("/api/settings/preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_titles"] == []
    assert body["locations"] == []
    assert body["remote_preference"] == "any"
    assert body["seniority_levels"] == []
    assert body["company_stage"] == "any"
    assert body["min_salary"] is None
    assert body["linkedin_auth_status"] == "disconnected"
    assert body["linkedin_search_urls"] == []


def test_put_preferences_saves_and_builds_urls(client):
    resp = client.put("/api/settings/preferences", json={
        "job_titles": ["Product Manager", "Senior PM"],
        "locations": ["United States"],
        "remote_preference": "remote",
        "seniority_levels": ["Senior"],
        "company_stage": "any",
        "min_salary": None,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_titles"] == ["Product Manager", "Senior PM"]
    assert body["remote_preference"] == "remote"
    # URLs should be auto-constructed (2 titles → 2 URLs)
    assert len(body["linkedin_search_urls"]) == 2
    assert all("linkedin.com/jobs/search" in u for u in body["linkedin_search_urls"])
    assert all("f_WT=2" in u for u in body["linkedin_search_urls"])  # remote
    # legacy field also populated
    assert body["linkedin_search_url"] is not None


def test_put_preferences_partial_update(client):
    client.put("/api/settings/preferences", json={"job_titles": ["PM"]})
    resp = client.put("/api/settings/preferences", json={"remote_preference": "hybrid"})
    assert resp.status_code == 200
    body = resp.json()
    # Previously set field preserved
    assert body["job_titles"] == ["PM"]
    assert body["remote_preference"] == "hybrid"


def test_put_preferences_empty_titles_clears_search_urls(client):
    client.put("/api/settings/preferences", json={"job_titles": ["PM"]})
    resp = client.put("/api/settings/preferences", json={"job_titles": []})
    assert resp.status_code == 200
    assert resp.json()["linkedin_search_urls"] == []
