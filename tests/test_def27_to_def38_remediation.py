import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import get_db, SessionLocal
from app.models.identity import User, Role
from app.models.project import Project, ProjectMember
from app.models.advisor import AdvisorInvitation, AdvisorProfile
from app.models.regulatory import RegulatoryRequirement
from app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _create_test_user(db: Session, role_name: str, email: str = None) -> tuple[User, str]:
    role = db.query(Role).filter(Role.role_name == role_name.upper()).first()
    if not role:
        role = Role(role_name=role_name.upper(), description=f"{role_name} role")
        db.add(role)
        db.flush()

    unique_email = email or f"{role_name.lower()}_{uuid.uuid4().hex[:8]}@example.com"
    raw_password = "Password123!"
    user = User(
        email=unique_email,
        password_hash=get_password_hash(raw_password),
        full_name=f"Test {role_name.title()} User",
        role_id=role.role_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if role_name.upper() == "ADVISOR":
        prof = AdvisorProfile(
            user_id=user.user_id,
            organization_name=f"{user.full_name} Advisory",
            professional_title="Regulatory & Compliance Advisor",
            specialization="Financial Crime Compliance & Regulatory Strategy",
            bio=f"Verified compliance advisor {user.full_name}."
        )
        db.add(prof)
        db.commit()

    # Login to get bearer token
    res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": raw_password})
    token = res.json()["access_token"]
    return user, token


# =========================================================================
# DEF-27: Route RAG Queries with No Approved Resource to Human Verification
# =========================================================================
def test_def27_rag_query_routes_to_human_verification(db_session):
    builder, token = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_code = f"PRJ-DEF27-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "project_name": "DEF27 RAG Safety Project",
        "project_code": proj_code,
        "description": "Project for testing RAG fallback and human verification routing."
    }, headers=headers)
    assert p_res.status_code == 201
    project_id = p_res.json()["project_id"]

    # Query with novel/unapproved topic lacking approved corpus citations
    q_payload = {
        "project_id": proj_code,
        "query": f"What are the specific penalty brackets under hypothetical Space Crime Directive {uuid.uuid4().hex[:6]}?"
    }
    q_res = client.post("/api/v1/query", json=q_payload, headers=headers)
    assert q_res.status_code == 200
    data = q_res.json()

    assert data.get("human_verification_required") is True
    assert data["metadata"]["requires_human_review"] is True
    assert "human_review_task" in data
    task = data["human_review_task"]
    assert task["issue_type"] == "GAP"
    assert task["review_status"] == "OPEN"
    gap_id = task["conflict_gap_id"]

    # Verify task appears in project's human-reviews listing
    list_res = client.get(f"/api/v1/projects/{proj_code}/human-reviews", headers=headers)
    assert list_res.status_code == 200
    review_ids = [r["conflict_gap_id"] for r in list_res.json()]
    assert gap_id in review_ids

    # Reviewer updates task to RESOLVED
    update_res = client.patch(
        f"/api/v1/projects/{proj_code}/human-reviews/{gap_id}",
        json={"review_status": "RESOLVED", "resolution_notes": "Corpus gap reviewed by compliance officer; confirmed out of scope."},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["review_status"] == "RESOLVED"


# =========================================================================
# DEF-28: Newly Created Project Disappears / String ID & Owner Contracts
# =========================================================================
def test_def28_project_persistence_and_string_fields(db_session):
    builder, token = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {token}"}

    proj_code = f"PRJ-DEF28-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "name": "DEF28 Persistence Project",
        "code": proj_code,
        "description": "Persistence verification project."
    }, headers=headers)
    assert p_res.status_code == 201
    created_proj = p_res.json()

    # Verify contract: id and owner are strings (so .toLowerCase() never throws TypeError)
    assert isinstance(created_proj["id"], str)
    assert isinstance(created_proj["owner"], str)
    assert created_proj["id"].lower() == proj_code.lower()
    assert created_proj["owner"].lower() == builder.full_name.lower()

    # Re-login (simulate fresh session) and verify project is listed
    login_res = client.post("/api/v1/auth/login", json={"email": builder.email, "password": "Password123!"})
    new_token = login_res.json()["access_token"]
    list_res = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {new_token}"})
    assert list_res.status_code == 200
    projects = list_res.json()
    matched = [p for p in projects if p["code"] == proj_code]
    assert len(matched) == 1
    assert matched[0]["owner"] == builder.full_name


# =========================================================================
# DEF-29: Newly Created Project Displays 0% Progress (Not Fabricated 60%)
# =========================================================================
def test_def29_new_project_has_zero_progress(db_session):
    builder, token = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {token}"}

    proj_code = f"PRJ-DEF29-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "project_name": "DEF29 Fresh Project",
        "project_code": proj_code,
        "description": "Fresh project with no completed work."
    }, headers=headers)
    assert p_res.status_code == 201
    proj_data = p_res.json()

    # Brand new project must have progress 0 (not fabricated 60%)
    assert "progress" in proj_data
    assert proj_data["progress"] == 0

    # Query project details
    detail_res = client.get(f"/api/v1/projects/{proj_code}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["progress"] == 0


# =========================================================================
# DEF-30: Project Workflow Option & Steps
# =========================================================================
def test_def30_project_workflow_option_and_steps(db_session):
    builder, token = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {token}"}

    proj_code = f"PRJ-DEF30-{uuid.uuid4().hex[:6].upper()}"
    client.post("/api/v1/projects", json={
        "project_name": "DEF30 Workflow Project",
        "project_code": proj_code,
        "description": "Workflow verification project."
    }, headers=headers)

    # Call workflow endpoint
    wf_res = client.get(f"/api/v1/projects/{proj_code}/workflow", headers=headers)
    assert wf_res.status_code == 200
    wf_data = wf_res.json()
    assert wf_data["total_steps"] == 4
    step_names = [s["name"] for s in wf_data["steps"]]
    assert "Scope & risk assessment" in step_names
    assert "Control design" in step_names
    assert "Advisor validation" in step_names
    assert "Approval & implementation" in step_names

    # Step details endpoint
    step1_res = client.get(f"/api/v1/projects/{proj_code}/workflow/steps/1", headers=headers)
    assert step1_res.status_code == 200
    assert step1_res.json()["step"]["step_number"] == "01"


# =========================================================================
# DEF-31: Audit Logs Recording and Multi-Dashboard Scoped Retrieval
# =========================================================================
def test_def31_audit_logs_recording_and_retrieval(db_session):
    builder, token = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {token}"}

    # Perform action: create project (generates PROJECT_CREATED audit event)
    proj_code = f"PRJ-DEF31-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "project_name": "DEF31 Audit Project",
        "project_code": proj_code,
        "description": "Audit testing."
    }, headers=headers)
    assert p_res.status_code == 201

    # Project-specific audit endpoint
    proj_audit_res = client.get(f"/api/v1/projects/{proj_code}/audit-events", headers=headers)
    assert proj_audit_res.status_code == 200
    proj_events = proj_audit_res.json()
    assert len(proj_events) >= 1

    ev = proj_events[0]
    # Check frontend-compatible fields
    assert "id" in ev and ev["id"].startswith("AUD-")
    assert "dateTime" in ev
    assert "user" in ev
    assert "role" in ev
    assert "action" in ev
    assert "result" in ev
    assert "relevantDetails" in ev

    # Global / Scoped audit endpoint
    global_res = client.get("/api/v1/audit", headers=headers)
    assert global_res.status_code == 200
    assert len(global_res.json()) >= 1


# =========================================================================
# DEF-32: Duplicate Invitation Prevention
# =========================================================================
def test_def32_duplicate_invitation_prevention(db_session):
    builder, b_token = _create_test_user(db_session, "BUILDER")
    advisor, a_token = _create_test_user(db_session, "ADVISOR")
    headers = {"Authorization": f"Bearer {b_token}"}

    proj_code = f"PRJ-DEF32-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "project_name": "DEF32 Duplicate Inv Project",
        "project_code": proj_code,
        "description": "Testing duplicate invitation rejection."
    }, headers=headers)
    assert p_res.status_code == 201

    # First invitation: should succeed
    inv_payload = {
        "advisor_email": advisor.email,
        "access_level": "REGULATORY",
        "expiry_days": 7
    }
    inv1_res = client.post(f"/api/v1/projects/{proj_code}/advisor-invitations", json=inv_payload, headers=headers)
    assert inv1_res.status_code == 201

    # Second invitation to exact same advisor (even with different case): must be rejected with 409 Conflict
    dup_payload = {
        "advisor_email": advisor.email.upper(),
        "access_level": "REGULATORY",
        "expiry_days": 7
    }
    inv2_res = client.post(f"/api/v1/projects/{proj_code}/advisor-invitations", json=dup_payload, headers=headers)
    assert inv2_res.status_code == 409
    assert "active invitation already exists" in inv2_res.json()["detail"].lower()


# =========================================================================
# DEF-33: Advisor-Selection Flow & Endpoint
# =========================================================================
def test_def33_advisor_selection_flow(db_session):
    builder, b_token = _create_test_user(db_session, "BUILDER")
    advisor, _ = _create_test_user(db_session, "ADVISOR")
    headers = {"Authorization": f"Bearer {b_token}"}

    proj_code = f"PRJ-DEF33-{uuid.uuid4().hex[:6].upper()}"
    client.post("/api/v1/projects", json={
        "project_name": "DEF33 Advisor Select Project",
        "project_code": proj_code,
        "description": "Testing advisor selection flow."
    }, headers=headers)

    # 1. Query eligible advisors list
    elig_res = client.get(f"/api/v1/projects/{proj_code}/advisors/eligible", headers=headers)
    assert elig_res.status_code == 200
    advisors_list = elig_res.json()
    assert len(advisors_list) >= 1

    # 2. Directly select advisor by email/id
    select_payload = {
        "advisor_email": advisor.email,
        "access_level": "LEGAL",
        "expiry_days": 7
    }
    sel_res = client.post(f"/api/v1/projects/{proj_code}/advisors/select", json=select_payload, headers=headers)
    assert sel_res.status_code == 201
    assert sel_res.json()["advisor_email"] == advisor.email.lower()
    assert sel_res.json()["access_level"] == "LEGAL"


# =========================================================================
# DEF-34: Sent Invitation Visible in Advisor Dashboard and Admin Monitoring
# =========================================================================
def test_def34_invitation_visibility_for_advisor_and_admin(db_session):
    builder, b_token = _create_test_user(db_session, "BUILDER")
    advisor, a_token = _create_test_user(db_session, "ADVISOR")
    admin, adm_token = _create_test_user(db_session, "ADMIN")

    proj_code = f"PRJ-DEF34-{uuid.uuid4().hex[:6].upper()}"
    client.post("/api/v1/projects", json={
        "project_name": "DEF34 Visibility Project",
        "project_code": proj_code,
        "description": "Invitation visibility test."
    }, headers={"Authorization": f"Bearer {b_token}"})

    # Builder invites advisor
    client.post(f"/api/v1/projects/{proj_code}/advisor-invitations", json={
        "advisor_email": advisor.email,
        "access_level": "TECH",
        "expiry_days": 7
    }, headers={"Authorization": f"Bearer {b_token}"})

    # Advisor checks their invitations inbox
    adv_res = client.get("/api/v1/users/me/invitations", headers={"Authorization": f"Bearer {a_token}"})
    assert adv_res.status_code == 200
    adv_invs = adv_res.json()
    matching_adv_inv = [i for i in adv_invs if i["project_code"] == proj_code]
    assert len(matching_adv_inv) == 1
    assert matching_adv_inv[0]["access_level"] == "TECH"
    assert matching_adv_inv[0]["status"] == "PENDING"

    # Admin checks monitoring tab
    adm_res = client.get("/api/v1/admin/advisor-invitations", headers={"Authorization": f"Bearer {adm_token}"})
    assert adm_res.status_code == 200
    admin_invs = adm_res.json()
    matching_adm_inv = [i for i in admin_invs if i["project"] == proj_code]
    assert len(matching_adm_inv) == 1
    assert matching_adm_inv[0]["invitedAdvisor"] == advisor.full_name


# =========================================================================
# DEF-35: Administrator Provisioning Controlled & Public Self-Reg Prohibited
# =========================================================================
def test_def35_administrator_provisioning(db_session):
    admin, adm_token = _create_test_user(db_session, "ADMIN")

    # 1. Public self-registration must NOT allow role ADMIN
    bad_self_reg = {
        "full_name": "Hacker Admin",
        "email": f"hacker_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Password123!",
        "role": "ADMIN"
    }
    self_res = client.post("/api/v1/auth/register", json=bad_self_reg)
    assert self_res.status_code == 403
    assert "administrator accounts cannot be self-registered" in self_res.json()["detail"].lower()

    # 2. Authorized Administrator provisions new Admin account
    new_admin_email = f"provisioned_admin_{uuid.uuid4().hex[:6]}@example.com"
    prov_res = client.post("/api/v1/admin/users", json={
        "full_name": "Provisioned Administrator",
        "email": new_admin_email,
        "password": "StrongPassword123!",
        "role": "ADMIN"
    }, headers={"Authorization": f"Bearer {adm_token}"})
    assert prov_res.status_code == 201
    assert prov_res.json()["platform_role"] == "ADMIN"

    # 3. New Admin can authenticate
    login_res = client.post("/api/v1/auth/login", json={
        "email": new_admin_email,
        "password": "StrongPassword123!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["platform_role"] == "ADMIN"


# =========================================================================
# DEF-36: Deactivated User Account Is Immediately Inactive & Blocked
# =========================================================================
def test_def36_deactivated_user_blocked(db_session):
    admin, adm_token = _create_test_user(db_session, "ADMIN")
    target_user, target_token = _create_test_user(db_session, "BUILDER")

    # Verify target user can access protected endpoint before deactivation
    pre_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {target_token}"})
    assert pre_res.status_code == 200

    # Admin deactivates target user
    deact_res = client.patch(
        f"/api/v1/admin/users/{target_user.user_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Attempt to use old JWT token: must be rejected with 403 Forbidden
    post_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {target_token}"})
    assert post_res.status_code == 403
    assert "deactivated" in post_res.json()["detail"].lower()

    # Attempt to log in again: must be rejected with 403 Forbidden
    login_res = client.post("/api/v1/auth/login", json={
        "email": target_user.email,
        "password": "Password123!"
    })
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["detail"].lower()


# =========================================================================
# DEF-37: Roles & Permissions Management in Admin Dashboard
# =========================================================================
def test_def37_roles_and_permissions_management(db_session):
    admin, adm_token = _create_test_user(db_session, "ADMIN")
    user, _ = _create_test_user(db_session, "BUILDER")
    headers = {"Authorization": f"Bearer {adm_token}"}

    # 1. Fetch roles definitions
    roles_res = client.get("/api/v1/admin/roles", headers=headers)
    assert roles_res.status_code == 200
    roles = roles_res.json()
    assert len(roles) >= 3
    role_names = [r["name"] for r in roles]
    assert "ADMIN" in role_names
    assert "BUILDER" in role_names
    assert "ADVISOR" in role_names

    # Check required table columns: ROLE, PERMITTED ACTIONS, ACCESS BOUNDARY, STATUS
    r0 = roles[0]
    assert "permittedActions" in r0
    assert "accessBoundary" in r0
    assert "status" in r0

    # 2. Reassign user's role to ADVISOR
    reassign_res = client.patch(
        f"/api/v1/admin/users/{user.user_id}/role",
        json={"role": "ADVISOR"},
        headers=headers
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["platform_role"] == "ADVISOR"


# =========================================================================
# DEF-38: Project Oversight Disable/Deactivate Project & Write Protection
# =========================================================================
def test_def38_project_disable_and_write_protection(db_session):
    admin, adm_token = _create_test_user(db_session, "ADMIN")
    builder, b_token = _create_test_user(db_session, "BUILDER")

    proj_code = f"PRJ-DEF38-{uuid.uuid4().hex[:6].upper()}"
    p_res = client.post("/api/v1/projects", json={
        "project_name": "DEF38 Disable Test Project",
        "project_code": proj_code,
        "description": "Project to test administrative disable and write protection."
    }, headers={"Authorization": f"Bearer {b_token}"})
    assert p_res.status_code == 201

    # 1. Admin disables project via oversight
    dis_res = client.post(
        f"/api/v1/admin/projects/{proj_code}/disable",
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "DISABLED"

    # 2. Project owner tries to modify disabled project: must be blocked with 403 Forbidden
    mod_res = client.patch(
        f"/api/v1/projects/{proj_code}",
        json={"project_name": "Illegal Modification on Disabled Project"},
        headers={"Authorization": f"Bearer {b_token}"}
    )
    assert mod_res.status_code == 403
    assert "disabled" in mod_res.json()["detail"].lower()

    # 3. Project owner tries to issue an advisor invitation on disabled project: blocked
    inv_res = client.post(
        f"/api/v1/projects/{proj_code}/advisor-invitations",
        json={"advisor_email": "test_adv@example.com", "access_level": "REGULATORY", "expiry_days": 7},
        headers={"Authorization": f"Bearer {b_token}"}
    )
    assert inv_res.status_code == 403
    assert "disabled" in inv_res.json()["detail"].lower()

    # 4. Admin re-activates project
    act_res = client.post(
        f"/api/v1/admin/projects/{proj_code}/activate",
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACTIVE"

    # 5. Project owner can now update project normally
    ok_mod_res = client.patch(
        f"/api/v1/projects/{proj_code}",
        json={"project_name": "Reactivated Project Name"},
        headers={"Authorization": f"Bearer {b_token}"}
    )
    assert ok_mod_res.status_code == 200
    assert ok_mod_res.json()["name"] == "Reactivated Project Name"
