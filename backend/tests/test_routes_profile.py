def test_get_profile_creates_default(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == ""


def test_update_profile(client):
    client.get("/api/profile")
    resp = client.put("/api/profile", json={
        "name": "Abhishek",
        "email": "test@test.com",
        "target_roles": ["AI PM", "Founding PM"],
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Abhishek"
    assert resp.json()["target_roles"] == ["AI PM", "Founding PM"]


def test_experience_crud(client):
    client.get("/api/profile")
    resp = client.post("/api/profile/experiences", json={
        "type": "venture",
        "company_name": "Einstein Labs",
        "role_title": "Founder",
        "bullet_points": ["Built AI products"],
    })
    assert resp.status_code == 200
    exp_id = resp.json()["id"]

    resp = client.get("/api/profile/experiences")
    assert len(resp.json()) == 1

    resp = client.put(f"/api/profile/experiences/{exp_id}", json={
        "role_title": "CEO & Founder",
    })
    assert resp.json()["role_title"] == "CEO & Founder"

    resp = client.delete(f"/api/profile/experiences/{exp_id}")
    assert resp.status_code == 200


def test_skills_crud(client):
    client.get("/api/profile")
    resp = client.post("/api/profile/skills", json={
        "name": "Product Strategy",
        "category": "product",
        "proficiency": "expert",
    })
    assert resp.status_code == 200

    resp = client.get("/api/profile/skills")
    assert len(resp.json()) == 1
