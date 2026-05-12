def test_create_job(client):
    resp = client.post("/api/jobs", json={
        "company_name": "Acme AI",
        "role_title": "AI Product Manager",
        "job_url": "https://example.com/job/1",
        "source": "linkedin",
        "job_description": "We need an AI PM to lead our product team...",
    })
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "Acme AI"
    assert resp.json()["status"] == "discovered"


def test_list_jobs_with_filters(client):
    client.post("/api/jobs", json={
        "company_name": "Acme",
        "role_title": "PM",
    })
    client.post("/api/jobs", json={
        "company_name": "Beta",
        "role_title": "PM",
    })

    resp = client.get("/api/jobs")
    assert len(resp.json()) == 2

    resp = client.get("/api/jobs?status=discovered")
    assert len(resp.json()) == 2


def test_get_job_detail(client):
    resp = client.post("/api/jobs", json={
        "company_name": "Acme",
        "role_title": "PM",
    })
    job_id = resp.json()["id"]

    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "Acme"
    assert "requirements" in resp.json()
    assert "scores" in resp.json()


def test_update_job_status(client):
    resp = client.post("/api/jobs", json={"company_name": "Acme", "role_title": "PM"})
    job_id = resp.json()["id"]

    resp = client.put(f"/api/jobs/{job_id}", json={"status": "applied"})
    assert resp.json()["status"] == "applied"


def test_delete_job(client):
    resp = client.post("/api/jobs", json={"company_name": "Acme", "role_title": "PM"})
    job_id = resp.json()["id"]

    resp = client.delete(f"/api/jobs/{job_id}")
    assert resp.status_code == 200

    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 404
