def test_contact_crud(client):
    resp = client.post("/api/contacts", json={
        "name": "Jane Doe",
        "company_name": "Acme",
        "title": "CEO",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Jane Doe"

    resp = client.get("/api/contacts")
    assert len(resp.json()) == 1


def test_outreach_workflow(client):
    contact = client.post("/api/contacts", json={"name": "Jane", "company_name": "Acme"}).json()

    resp = client.post("/api/outreach", json={
        "contact_id": contact["id"],
        "channel": "linkedin",
        "message_type": "initial",
        "message": "Hey Jane...",
    })
    assert resp.json()["status"] == "draft"

    outreach_id = resp.json()["id"]
    resp = client.post(f"/api/outreach/{outreach_id}/approve")
    assert resp.json()["status"] == "sent"
    assert resp.json()["scheduled_followup_at"] is not None


def test_crm_pipeline(client):
    client.post("/api/jobs", json={"company_name": "A", "role_title": "PM"})
    client.post("/api/jobs", json={"company_name": "B", "role_title": "PM"})

    resp = client.get("/api/crm/pipeline")
    assert resp.json()["discovered"] == 2

    resp = client.get("/api/crm/stats")
    assert resp.json()["total_jobs"] == 2
