import uuid
from fastapi.testclient import TestClient

def test_list_advisors(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/advisors", headers=builder_auth_headers)
    assert response.status_code == 200
    advisors = response.json()
    assert isinstance(advisors, list)
    assert len(advisors) >= 2
    assert any("Vance" in a["full_name"] for a in advisors)
    assert any("Reid" in a["full_name"] for a in advisors)

def test_get_advisor_by_id(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/advisors/1", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["advisor_profile_id"] == 1
    assert "specialization" in data

def test_advisor_invitation_lifecycle(client: TestClient, builder_auth_headers: dict):
    unique_email = f"adv.{uuid.uuid4().hex[:6]}@complianceexperts.co.uk"
    payload = {
        "advisor_email": unique_email,
        "access_level": "REGULATORY",
        "expiry_days": 14
    }
    # 1. Create invitation
    response = client.post("/api/v1/projects/1/advisor-invitations", json=payload, headers=builder_auth_headers)
    assert response.status_code == 201
    invitation = response.json()
    assert invitation["advisor_email"] == unique_email
    assert invitation["invitation_status"] == "PENDING"
    assert invitation["invitation_token"] is not None
    invitation_id = invitation["invitation_id"]

    # 2. List invitations
    list_resp = client.get("/api/v1/projects/1/advisor-invitations", headers=builder_auth_headers)
    assert list_resp.status_code == 200
    assert any(inv["invitation_id"] == invitation_id for inv in list_resp.json())

    # 3. Resend invitation
    resend_resp = client.post(f"/api/v1/projects/1/advisor-invitations/{invitation_id}/resend", headers=builder_auth_headers)
    assert resend_resp.status_code == 200
    assert resend_resp.json()["invitation_status"] == "PENDING"

    # 4. Revoke invitation
    revoke_resp = client.post(f"/api/v1/projects/1/advisor-invitations/{invitation_id}/revoke", headers=builder_auth_headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["invitation_status"] == "REVOKED"
