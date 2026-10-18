"""
FINREGTECH SHIPYARD — MULTI-ROLE DASHBOARD & DATA INTEGRATION REGRESSION SUITE
Tests for DEF-01 through DEF-09 data integration, scoping, and PostgreSQL persistence.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.session import SessionLocal
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.models.advisor import AdvisorProfile, AdvisorInvitation

client = TestClient(app)

def unique_email(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@shipyard.io"

def test_def_01_advisor_empty_initial_projects():
    """DEF-01: Newly registered Advisor must NOT have any project assignments by default."""
    adv_email = unique_email("adv_def01")
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": adv_email,
            "password": "Password123!",
            "full_name": "Dr. Eleanor Clean",
            "role": "ADVISOR",
            "organization": "Clean Advisory Ltd"
        }
    )
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user_id"]

    # Verify through GET /projects
    headers = {"Authorization": f"Bearer {token}"}
    proj_resp = client.get("/api/v1/projects", headers=headers)
    assert proj_resp.status_code == 200
    projects = proj_resp.json()
    assert len(projects) == 0, f"Expected 0 projects for fresh advisor, found {len(projects)}"

    # Direct database verification
    db = SessionLocal()
    memberships = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
    db.close()
    assert len(memberships) == 0, f"Expected 0 database memberships for new advisor, found {len(memberships)}"

def test_def_02_advisor_login_and_notifications_handshake():
    """DEF-02: Advisor authentication and secondary endpoint fetches succeed cleanly without errors."""
    adv_email = unique_email("adv_def02")
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": adv_email,
            "password": "Password123!",
            "full_name": "Marcus Clean",
            "role": "ADVISOR",
            "organization": "Clean Advisory Ltd"
        }
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": adv_email, "password": "Password123!"}
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["platform_role"] == "ADVISOR"
    token = data["access_token"]

    # Secondary endpoints called upon dashboard load
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == adv_email
    assert me_resp.json()["platform_role"] == "ADVISOR"

    notif_resp = client.get("/api/v1/users/me/notifications", headers=headers)
    assert notif_resp.status_code == 200
    assert isinstance(notif_resp.json(), list)

def test_def_03_admin_dashboard_real_data_and_audit_stream():
    """DEF-03: Admin endpoints return live, non-mock counts and platform audit events."""
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@finregtech.io", "password": "Password123!"}
    )
    assert admin_login.status_code == 200
    token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Admin Stats
    stats_resp = client.get("/api/v1/admin/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_users"] > 0
    assert stats["active_users"] > 0
    assert stats["total_projects"] >= 0
    assert stats["regulatory_sources_count"] > 0
    assert stats["total_audit_events"] >= 0

    # 2. Admin Users Directory
    users_resp = client.get("/api/v1/admin/users", headers=headers)
    assert users_resp.status_code == 200
    users = users_resp.json()
    assert len(users) == stats["total_users"]

    # 3. Admin Audit Stream
    audit_resp = client.get("/api/v1/admin/audit-events", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert isinstance(events, list)

def test_def_04_and_05_registration_persistence_in_postgresql():
    """DEF-04 & DEF-05: Successive registrations persist isolated, traceable records in PostgreSQL."""
    user1_email = unique_email("bld1_def05")
    user2_email = unique_email("bld2_def05")

    # Register user 1
    r1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": user1_email,
            "password": "Password123!",
            "full_name": "First Builder",
            "role": "BUILDER"
        }
    )
    assert r1.status_code == 201
    u1_id = r1.json()["user_id"]

    # Register user 2
    r2 = client.post(
        "/api/v1/auth/register",
        json={
            "email": user2_email,
            "password": "Password123!",
            "full_name": "Second Builder",
            "role": "BUILDER"
        }
    )
    assert r2.status_code == 201
    u2_id = r2.json()["user_id"]

    assert u1_id != u2_id, "Each registration must produce a distinct user ID"

    # Direct PostgreSQL verification on schema identity.users
    db = SessionLocal()
    row1 = db.execute(
        text("SELECT user_id, email, full_name, is_active FROM identity.users WHERE user_id = :uid"),
        {"uid": u1_id}
    ).fetchone()
    row2 = db.execute(
        text("SELECT user_id, email, full_name, is_active FROM identity.users WHERE user_id = :uid"),
        {"uid": u2_id}
    ).fetchone()
    db.close()

    assert row1 is not None, f"User 1 ({u1_id}) was not found in identity.users"
    assert row1.email == user1_email
    assert row1.full_name == "First Builder"
    assert row1.is_active is True

    assert row2 is not None, f"User 2 ({u2_id}) was not found in identity.users"
    assert row2.email == user2_email
    assert row2.full_name == "Second Builder"
    assert row2.is_active is True

def test_def_06_and_08_builder_dashboard_scoping_and_creator_derivation():
    """DEF-06 & DEF-08: Builder summary is scoped and project owner is derived from principal."""
    builder_email = unique_email("bld_def08")
    b_name = f"Alice Builder {uuid.uuid4().hex[:4]}"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": builder_email,
            "password": "Password123!",
            "full_name": b_name,
            "role": "BUILDER"
        }
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initial summary should be zero projects
    sum_resp0 = client.get("/api/v1/projects/summary", headers=headers)
    assert sum_resp0.status_code == 200
    assert sum_resp0.json()["total_projects"] == 0

    # Create project
    p_code = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
    p_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "AML Risk Scope Project",
            "code": p_code,
            "type": "Anti-Bribery and Corruption (ABC)",
            "description": "Scoping test project"
        }
    )
    assert p_resp.status_code == 201
    p_data = p_resp.json()

    # DEF-08 verification: creator name derived authoritatively
    assert p_data["owner_name"] == b_name, f"Expected owner_name '{b_name}', got '{p_data.get('owner_name')}'"
    assert p_data["owner"] == b_name, f"Expected owner alias '{b_name}', got '{p_data.get('owner')}'"

    # Fetch projects list
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert len(projects) == 1
    assert projects[0]["owner_name"] == b_name
    assert projects[0]["owner"] == b_name

    # Summary updated
    sum_resp1 = client.get("/api/v1/projects/summary", headers=headers)
    assert sum_resp1.status_code == 200
    assert sum_resp1.json()["total_projects"] == 1
    assert sum_resp1.json()["active_projects"] == 1

def test_def_07_and_09_advisor_selector_and_invitation_lifecycle():
    """DEF-07 & DEF-09: Registered advisor appears in selector, can be invited and accepted."""
    # 1. Register a new advisor
    adv_email = unique_email("adv_def09")
    adv_name = f"Counsel David {uuid.uuid4().hex[:4]}"
    org_name = "David Legal Solutions"
    adv_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": adv_email,
            "password": "Password123!",
            "full_name": adv_name,
            "role": "ADVISOR",
            "organization": org_name
        }
    )
    assert adv_reg.status_code == 201
    adv_uid = adv_reg.json()["user_id"]
    adv_token = adv_reg.json()["access_token"]

    # 2. Register a builder who creates a project
    bld_email = unique_email("bld_def09")
    bld_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": bld_email,
            "password": "Password123!",
            "full_name": "Bob Builder",
            "role": "BUILDER"
        }
    )
    assert bld_reg.status_code == 201
    bld_token = bld_reg.json()["access_token"]
    bld_headers = {"Authorization": f"Bearer {bld_token}"}

    # DEF-07: Builder queries GET /advisors and finds the newly registered advisor
    adv_list_resp = client.get("/api/v1/advisors", headers=bld_headers)
    assert adv_list_resp.status_code == 200
    all_advisors = adv_list_resp.json()
    matching_adv = [a for a in all_advisors if a["email"] == adv_email]
    assert len(matching_adv) == 1, f"Newly registered advisor {adv_email} was not found in GET /advisors"
    assert matching_adv[0]["full_name"] == adv_name
    assert matching_adv[0]["organization_name"] == org_name

    # Create project by builder
    p_code = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
    p_resp = client.post(
        "/api/v1/projects",
        headers=bld_headers,
        json={"name": "Advisory Governance Project", "code": p_code}
    )
    assert p_resp.status_code == 201
    project_id = p_resp.json()["project_id"]

    # DEF-09: Builder invites the new advisor to the project
    invite_resp = client.post(
        f"/api/v1/projects/{project_id}/advisor-invitations",
        headers=bld_headers,
        json={
            "advisor_email": adv_email,
            "access_level": "REGULATORY",
            "expiry_days": 7
        }
    )
    assert invite_resp.status_code == 201, invite_resp.text
    invitation_id = invite_resp.json()["invitation_id"]
    assert invite_resp.json()["invitation_status"] == "PENDING"

    # Advisor accepts invitation
    adv_headers = {"Authorization": f"Bearer {adv_token}"}
    accept_resp = client.post(
        f"/api/v1/projects/{project_id}/advisor-invitations/{invitation_id}/accept",
        headers=adv_headers
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["invitation_status"] == "ACCEPTED"

    # Verify advisor now sees the project in GET /projects
    adv_projects_resp = client.get("/api/v1/projects", headers=adv_headers)
    assert adv_projects_resp.status_code == 200
    adv_projects = adv_projects_resp.json()
    assert len(adv_projects) == 1
    assert adv_projects[0]["project_id"] == project_id
    assert adv_projects[0]["name"] == "Advisory Governance Project"
