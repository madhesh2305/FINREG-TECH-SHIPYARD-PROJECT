from fastapi.testclient import TestClient

def _ensure_advisor_is_project_member(client: TestClient, builder_auth_headers: dict):
    # Ensure Eleanor Vance (user_id 2) is a project member of project 1
    resp = client.post(
        "/api/v1/projects/1/members",
        json={"user_id": 2, "service_role": "LEGAL", "service_scope": "LEGAL_ADVICE_SUPPORT"},
        headers=builder_auth_headers
    )
    assert resp.status_code in (201, 409)

def test_submit_advice_success(client: TestClient, builder_auth_headers: dict, advisor_auth_headers: dict):
    _ensure_advisor_is_project_member(client, builder_auth_headers)

    payload = {
        "title": "EDD Trigger Threshold Review",
        "advice_text": "The control design covers standard CDD, but EDD should be explicit for complex structures.",
        "recommendation": "Implement additional verification steps for high-risk corporate customers.",
        "assumptions": "Based on UK MLR 2017 Regulation 33.",
        "advice_status": "SUBMITTED",
        "source_links": [
            {"source_id": 1, "reference_note": "MLR 2017 Regulation 33 EDD requirements"}
        ]
    }
    response = client.post("/api/v1/projects/1/advice", json=payload, headers=advisor_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["advice_status"] == "SUBMITTED"
    assert data["display_status"] == "Pending Review"
    assert data["advisor_name"] == "Eleanor Vance"
    assert len(data["source_links"]) == 1
    assert data["source_links"][0]["source_id"] == 1

def test_list_and_filter_project_advice(client: TestClient, builder_auth_headers: dict):
    # Builder lists advice
    response = client.get("/api/v1/projects/1/advice", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Filter by status
    filtered = client.get("/api/v1/projects/1/advice?status=SUBMITTED", headers=builder_auth_headers)
    assert filtered.status_code == 200
    assert all(a["advice_status"] == "SUBMITTED" for a in filtered.json())

def test_patch_advice_status(client: TestClient, builder_auth_headers: dict):
    # Fetch first advice
    advice_list = client.get("/api/v1/projects/1/advice", headers=builder_auth_headers).json()
    advice_id = advice_list[0]["advice_id"]

    # Project owner accepts / reviews advice
    patch_resp = client.patch(
        f"/api/v1/projects/1/advice/{advice_id}",
        json={"advice_status": "REVIEWED"},
        headers=builder_auth_headers
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["advice_status"] == "REVIEWED"
    assert updated["display_status"] == "Accepted"

def test_outsider_cannot_access_advice(client: TestClient, outsider_auth_headers: dict):
    response = client.get("/api/v1/projects/1/advice", headers=outsider_auth_headers)
    assert response.status_code == 403

def test_advice_bola_protection(client: TestClient, builder_auth_headers: dict):
    # Project 999 does not exist / user is not a member
    response = client.get("/api/v1/projects/999/advice", headers=builder_auth_headers)
    assert response.status_code == 404
