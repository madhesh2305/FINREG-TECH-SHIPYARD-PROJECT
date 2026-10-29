"""
Master Regression Test Suite for Defect Report Items:
- DEF-22: Project Isolation (A project created by one user must NOT appear in another user's dashboard or API)
- DEF-23: Advisor Account Role Persistence (Advisor account remains ADVISOR across login, token, and user profile)
- DEF-24: Inactive User Enforcement (Inactive user loses access immediately on token, login, and direct API)
- DEF-25: Newly Created Advisor Discovery (Newly registered advisor appears in directory and can be invited)
"""

import time
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.identity import User, Role
from app.models.project import Project, ProjectMember
from app.models.advisor import AdvisorProfile, AdvisorInvitation


# ---------------------------------------------------------------------------
# DEF-22: Project Isolation
# ---------------------------------------------------------------------------
def test_def22_cross_user_project_isolation(client: TestClient, db: Session):
    """
    Acceptance Criteria DEF-22:
    - User A creates Project A
    - User B creates Project B
    - User A lists projects: Project B must NOT appear
    - User B lists projects: Project A must NOT appear
    - User A calling direct GET /projects/{Project B ID} gets HTTP 403 Forbidden
    - User B calling direct GET /projects/{Project A ID} gets HTTP 403 Forbidden
    - Sub-resources (/requirements, /members, /advice, /decisions) strictly return 403 to non-members
    """
    uid_a = uuid.uuid4().hex[:6]
    uid_b = uuid.uuid4().hex[:6]

    email_a = f"builder_a_{uid_a}@finregtech.io"
    email_b = f"builder_b_{uid_b}@finregtech.io"

    # 1. Register User A (Builder)
    resp_a = client.post("/api/v1/auth/register", json={
        "email": email_a,
        "password": "Password123!",
        "full_name": f"Builder A {uid_a}",
        "role": "BUILDER",
        "organization": "Firm Alpha"
    })
    assert resp_a.status_code == 201, resp_a.text
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B (Builder)
    resp_b = client.post("/api/v1/auth/register", json={
        "email": email_b,
        "password": "Password123!",
        "full_name": f"Builder B {uid_b}",
        "role": "BUILDER",
        "organization": "Firm Beta"
    })
    assert resp_b.status_code == 201, resp_b.text
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates Project A
    code_a = f"PRJ-A-{uid_a.upper()}"
    resp_create_a = client.post("/api/v1/projects", json={
        "project_name": f"Alpha Project {uid_a}",
        "project_code": code_a,
        "description": "Alpha confidential compliance project",
        "jurisdiction": "UK",
        "regulatory_scope": "AML"
    }, headers=headers_a)
    assert resp_create_a.status_code == 201, resp_create_a.text
    proj_a_id = resp_create_a.json()["project_id"]

    # 4. User B creates Project B
    code_b = f"PRJ-B-{uid_b.upper()}"
    resp_create_b = client.post("/api/v1/projects", json={
        "project_name": f"Beta Project {uid_b}",
        "project_code": code_b,
        "description": "Beta confidential compliance project",
        "jurisdiction": "EU",
        "regulatory_scope": "ABC"
    }, headers=headers_b)
    assert resp_create_b.status_code == 201, resp_create_b.text
    proj_b_id = resp_create_b.json()["project_id"]

    # 5. User A lists projects -> Project B must NOT be in the list
    list_a = client.get("/api/v1/projects", headers=headers_a)
    assert list_a.status_code == 200
    user_a_project_ids = [p["project_id"] for p in list_a.json()]
    assert proj_a_id in user_a_project_ids
    assert proj_b_id not in user_a_project_ids, "DEF-22 VIOLATION: Project B appeared on User A's project list!"

    # 6. User B lists projects -> Project A must NOT be in the list
    list_b = client.get("/api/v1/projects", headers=headers_b)
    assert list_b.status_code == 200
    user_b_project_ids = [p["project_id"] for p in list_b.json()]
    assert proj_b_id in user_b_project_ids
    assert proj_a_id not in user_b_project_ids, "DEF-22 VIOLATION: Project A appeared on User B's project list!"

    # 7. User A attempts direct access to Project B -> Must be rejected with 403 Forbidden
    direct_a_to_b = client.get(f"/api/v1/projects/{proj_b_id}", headers=headers_a)
    assert direct_a_to_b.status_code == 403, f"Expected 403 Forbidden but got {direct_a_to_b.status_code}"

    # 8. User B attempts direct access to Project A -> Must be rejected with 403 Forbidden
    direct_b_to_a = client.get(f"/api/v1/projects/{proj_a_id}", headers=headers_b)
    assert direct_b_to_a.status_code == 403, f"Expected 403 Forbidden but got {direct_b_to_a.status_code}"

    # 9. Verify sub-resource isolation (requirements, members, advice, decisions)
    for sub in ["requirements", "members", "advice", "decisions"]:
        sub_resp = client.get(f"/api/v1/projects/{proj_b_id}/{sub}", headers=headers_a)
        assert sub_resp.status_code == 403, f"Expected 403 on /projects/{proj_b_id}/{sub} for outsider User A"


# ---------------------------------------------------------------------------
# DEF-23: Advisor Role Persistence and Routing
# ---------------------------------------------------------------------------
def test_def23_advisor_account_persistence_and_routing(client: TestClient, db: Session):
    """
    Acceptance Criteria DEF-23:
    - Register a unique Advisor test account
    - Confirm persisted role in DB is ADVISOR and AdvisorProfile exists
    - Fresh login produces TokenResponse with platform_role == 'ADVISOR'
    - GET /api/v1/users/me returns platform_role == 'ADVISOR'
    - Advisor cannot create projects (POST /api/v1/projects is rejected with 403 Forbidden)
    - Re-authentication with email & password preserves ADVISOR role across sessions
    """
    uid = uuid.uuid4().hex[:6]
    advisor_email = f"advisor_{uid}@advisorygroup.co.uk"
    password = "StrongPassword123!"

    # 1. Register new Advisor
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": advisor_email,
        "password": password,
        "full_name": f"Dr. Advisor {uid}",
        "role": "ADVISOR",
        "organization": "Global Regulatory Advisory LLP"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert reg_data["platform_role"] == "ADVISOR", f"Expected ADVISOR, got {reg_data.get('platform_role')}"
    token_1 = reg_data["access_token"]

    # 2. Verify database records
    user_record = db.query(User).filter(User.email == advisor_email).first()
    assert user_record is not None
    assert user_record.role.role_name == "ADVISOR"
    prof_record = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == user_record.user_id).first()
    assert prof_record is not None, "DEF-23/25 VIOLATION: AdvisorProfile not created upon registration"

    # 3. Call GET /users/me with initial registration token
    me_resp_1 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_1}"})
    assert me_resp_1.status_code == 200
    assert me_resp_1.json()["platform_role"] == "ADVISOR"

    # 4. Fresh login (simulating returning user after browser restart)
    login_resp = client.post("/api/v1/auth/login", json={
        "email": advisor_email,
        "password": password
    })
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert login_data["platform_role"] == "ADVISOR", (
        f"DEF-23 VIOLATION: Advisor logged in and received role '{login_data.get('platform_role')}' instead of 'ADVISOR'"
    )
    token_2 = login_data["access_token"]

    # 5. Call GET /users/me with newly minted login token
    me_resp_2 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_2}"})
    assert me_resp_2.status_code == 200
    assert me_resp_2.json()["platform_role"] == "ADVISOR"

    # 6. Verify role boundaries: Advisor cannot create projects (Builder action)
    forbidden_action = client.post("/api/v1/projects", json={
        "project_name": "Should Fail",
        "project_code": f"FAIL-{uid.upper()}",
        "description": "Unauthorized",
        "jurisdiction": "UK",
        "regulatory_scope": "AML"
    }, headers={"Authorization": f"Bearer {token_2}"})
    assert forbidden_action.status_code == 403, (
        f"DEF-23 VIOLATION: Advisor was allowed to execute Builder action POST /projects (status {forbidden_action.status_code})"
    )


# ---------------------------------------------------------------------------
# DEF-24: Inactive User Enforcement
# ---------------------------------------------------------------------------
def test_def24_inactive_user_immediate_session_revocation(client: TestClient, db: Session, admin_auth_headers):
    """
    Acceptance Criteria DEF-24:
    - User is active and has valid session token
    - Admin deactivates the user via PATCH /api/v1/admin/users/{userId}/status (is_active = False)
    - With existing token, subsequent requests to protected endpoints return HTTP 403 Forbidden
    - Fresh login attempts by the deactivated user return HTTP 403 Forbidden
    - GET /users/me returns HTTP 403 Forbidden
    """
    uid = uuid.uuid4().hex[:6]
    user_email = f"deactivateme_{uid}@finregtech.io"
    password = "Password123!"

    # 1. Register active user
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": password,
        "full_name": f"Test Deactivation {uid}",
        "role": "BUILDER"
    })
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["user_id"]
    active_token = reg_resp.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {active_token}"}

    # 2. Verify user can access protected endpoints while active
    pre_check = client.get("/api/v1/projects", headers=user_headers)
    assert pre_check.status_code == 200

    # 3. Admin marks account inactive
    deactivate_resp = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": False},
        headers=admin_auth_headers
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    # 4. Same session token attempts protected call -> Must be rejected with 403
    post_check = client.get("/api/v1/projects", headers=user_headers)
    assert post_check.status_code == 403, (
        f"DEF-24 VIOLATION: Deactivated user was still able to call /projects! Got status {post_check.status_code}"
    )
    assert "deactivated" in post_check.text.lower() or "inactive" in post_check.text.lower()

    # 5. Direct GET /users/me with existing token -> Must be rejected with 403
    me_check = client.get("/api/v1/users/me", headers=user_headers)
    assert me_check.status_code == 403

    # 6. Attempt fresh login with credentials -> Must be rejected with 403
    fresh_login = client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": password
    })
    assert fresh_login.status_code == 403, (
        f"DEF-24 VIOLATION: Deactivated user was able to log in again! Got status {fresh_login.status_code}"
    )


# ---------------------------------------------------------------------------
# DEF-25: Newly Created Advisor Discovery & Selection
# ---------------------------------------------------------------------------
def test_def25_newly_created_advisor_discovery_and_selection(client: TestClient, db: Session, builder_auth_headers):
    """
    Acceptance Criteria DEF-25:
    - Create a new Advisor account
    - Builder lists advisors via GET /api/v1/advisors
    - Newly created Advisor appears in the directory with complete, non-null profile data
    - Builder invites this newly created Advisor to a project via POST /api/v1/projects/{projectId}/advisor-invitations
    - Invitation is successfully persisted in PostgreSQL with PENDING status
    """
    uid = uuid.uuid4().hex[:6]
    advisor_email = f"advisor_discovery_{uid}@compliancelab.co.uk"
    advisor_name = f"Clara Advisor {uid}"

    # 1. Register new Advisor
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": advisor_email,
        "password": "Password123!",
        "full_name": advisor_name,
        "role": "ADVISOR",
        "organization": "Compliance Lab UK"
    })
    assert reg_resp.status_code == 201
    adv_user_id = reg_resp.json()["user_id"]

    # 2. Builder fetches advisors directory
    advisors_resp = client.get("/api/v1/advisors", headers=builder_auth_headers)
    assert advisors_resp.status_code == 200
    advisors_list = advisors_resp.json()
    assert isinstance(advisors_list, list)

    # 3. Verify newly created advisor appears in list
    matching = [a for a in advisors_list if a["email"] == advisor_email]
    assert len(matching) == 1, (
        f"DEF-25 VIOLATION: Newly created advisor '{advisor_email}' was not found in GET /advisors directory!"
    )
    found_advisor = matching[0]
    assert found_advisor["full_name"] == advisor_name
    assert found_advisor["user_id"] == adv_user_id
    assert found_advisor["organization_name"] == "Compliance Lab UK"
    assert found_advisor["advisor_profile_id"] is not None

    # 4. Builder invites this newly created Advisor to Project 1
    invite_resp = client.post(
        "/api/v1/projects/1/advisor-invitations",
        json={
            "advisor_email": advisor_email,
            "access_level": "REGULATORY",
            "expiry_days": 14
        },
        headers=builder_auth_headers
    )
    assert invite_resp.status_code == 201, invite_resp.text
    invite_data = invite_resp.json()
    assert invite_data["advisor_email"] == advisor_email
    assert invite_data["invitation_status"] == "PENDING"
    assert invite_data["access_level"] == "REGULATORY"
    assert invite_data["project_id"] == 1

    # 5. Verify invitation is recorded in DB
    inv_in_db = db.query(AdvisorInvitation).filter(
        AdvisorInvitation.project_id == 1,
        AdvisorInvitation.advisor_email == advisor_email
    ).first()
    assert inv_in_db is not None
    assert inv_in_db.invitation_status == "PENDING"
