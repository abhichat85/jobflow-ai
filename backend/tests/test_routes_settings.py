def test_get_settings_creates_defaults_if_missing(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["discovery_enabled"] is True
    assert body["auto_review_threshold"] == 65
    assert body["cover_letter_tone"] == "professional"
    # Cookie should NEVER be returned as plaintext
    assert "linkedin_cookie_encrypted" not in body
    assert body["linkedin_cookie_present"] is False


def test_put_settings_partial_update(client):
    resp = client.put("/api/settings", json={
        "auto_review_threshold": 75,
        "discovery_enabled": False,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["auto_review_threshold"] == 75
    assert body["discovery_enabled"] is False
    # Other fields unchanged
    assert body["cover_letter_tone"] == "professional"


def test_put_linkedin_cookie_encrypts_and_marks_present(client):
    resp = client.put("/api/settings", json={
        "linkedin_cookie": "AQEDtest-fake-cookie",
        "linkedin_search_url": "https://www.linkedin.com/jobs/search/?keywords=AI+PM",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["linkedin_cookie_present"] is True
    assert body["linkedin_search_url"].startswith("https://www.linkedin.com")
    # Plaintext never echoed back
    assert "AQEDtest-fake-cookie" not in resp.text


def test_clear_linkedin_cookie(client):
    client.put("/api/settings", json={"linkedin_cookie": "abc"})
    resp = client.put("/api/settings", json={"linkedin_cookie": ""})
    assert resp.status_code == 200
    assert resp.json()["linkedin_cookie_present"] is False
