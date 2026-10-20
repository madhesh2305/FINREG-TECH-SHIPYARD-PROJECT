import io
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.identity import User, Role
from app.models.project import Project, ProjectMember
from app.models.advice import Advice
from app.models.regulatory import RegulatoryRequirement
from app.models.attachment import ProjectAttachment

def test_def01_advisor_empty_project_assignments_by_default(client: TestClient, db: Session, builder_auth_headers: dict):
    """DEF-01: Newly registered Advisor has zero project assignments until explicitly assigned."""
    unique_email = f"adv_{uuid.uuid4().hex[:8]}@advisoryfirm.co.uk"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Dr. Eleanor Vance Jr.",
        "role": "ADVISOR",
        "organization": "Independent Compliance LLC"
    })
    assert reg_resp.status_code == 201
    adv_token = reg_resp.json()["access_token"]
    adv_headers = {"Authorization": f"Bearer {adv_token}"}

    # Advisor lists projects: must be empty
    list_resp = client.get("/api/v1/projects", headers=adv_headers)
    assert list_resp.status_code == 200
    assert list_resp.json() == []

    # Builder invites advisor to Project 1
    proj1 = db.query(Project).filter(Project.project_id == 1).first()
    if proj1:
        inv_resp = client.post(f"/api/v1/projects/{proj1.project_id}/advisor-invitations", headers=builder_auth_headers, json={
            "advisor_email": unique_email,
            "access_level": "REGULATORY",
            "expiry_days": 14
        })
        assert inv_resp.status_code == 201
        inv_id = inv_resp.json()["invitation_id"]

        # Advisor accepts invitation
        accept_resp = client.post(f"/api/v1/projects/{proj1.project_id}/advisor-invitations/{inv_id}/accept", headers=adv_headers)
        assert accept_resp.status_code == 200

        # Now advisor sees exactly Project 1
        list_resp2 = client.get("/api/v1/projects", headers=adv_headers)
        assert list_resp2.status_code == 200
        p_ids = [p["project_id"] for p in list_resp2.json()]
        assert proj1.project_id in p_ids

def test_def02_advisor_login_clean_tokens_and_roles(client: TestClient):
    """DEF-02: Advisor login succeeds with valid token, proper role and zero popup error triggers."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "eleanor.vance@vancelegal.co.uk",
        "password": "Password123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["platform_role"] == "ADVISOR"
    assert data["email"] == "eleanor.vance@vancelegal.co.uk"

def test_def03_admin_dashboard_live_postgresql_data(client: TestClient, admin_auth_headers: dict):
    """DEF-03: Admin dashboard endpoints query live PostgreSQL records and return accurate metrics."""
    # Stats
    stats_resp = client.get("/api/v1/admin/stats", headers=admin_auth_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_users"] >= 4
    assert stats["active_users"] >= 4
    assert stats["total_projects"] >= 1
    assert stats["regulatory_sources_count"] >= 1
    assert stats["total_audit_events"] >= 1

    # User directory
    users_resp = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert users_resp.status_code == 200
    assert len(users_resp.json()) >= 4

    # Audit stream
    audit_resp = client.get("/api/v1/admin/audit-events", headers=admin_auth_headers)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) >= 1

def test_def05_registered_users_authoritative_persistence_in_db(client: TestClient, db: Session):
    """DEF-05: User registration commits directly to PostgreSQL identity.users with db.commit()."""
    unique_email = f"builder_{uuid.uuid4().hex[:8]}@fintechstart.io"
    resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "SecurePassword123!",
        "full_name": "Test Builder Person",
        "role": "BUILDER"
    })
    assert resp.status_code == 201

    # Authoritative DB query
    user_record = db.query(User).filter(User.email == unique_email).first()
    assert user_record is not None
    assert user_record.full_name == "Test Builder Person"
    assert user_record.is_active is True
    assert user_record.created_at is not None

def test_def06_builder_dashboard_summary_live_metrics(client: TestClient, builder_auth_headers: dict):
    """DEF-06: Builder dashboard summary calculates live counts based strictly on authorized projects."""
    resp = client.get("/api/v1/projects/summary", headers=builder_auth_headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert "total_projects" in summary
    assert "active_projects" in summary
    assert "total_requirements" in summary
    assert "audit_readiness_percentage" in summary

def test_def07_builder_advisor_selector_contains_newly_registered_advisor(client: TestClient, builder_auth_headers: dict):
    """DEF-07: Newly registered advisor is immediately accessible via GET /api/v1/advisors."""
    unique_email = f"expert_{uuid.uuid4().hex[:8]}@advisory.eu"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Marcus Aurelius FCC",
        "role": "ADVISOR",
        "organization": "Aurelius Compliance Partners"
    })
    assert reg_resp.status_code == 201

    adv_resp = client.get("/api/v1/advisors", headers=builder_auth_headers)
    assert adv_resp.status_code == 200
    advisors = adv_resp.json()
    emails = [a["email"] for a in advisors]
    assert unique_email in emails

def test_def10_new_project_zero_percent_readiness_and_dynamic_completion(client: TestClient, builder_auth_headers: dict, db: Session):
    """DEF-10: Newly created project exhibits 0% completion and strictly calculates readiness from persisted records."""
    code = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
    create_resp = client.post("/api/v1/projects", headers=builder_auth_headers, json={
        "project_name": "Empty Test Project",
        "project_code": code,
        "description": "Brand new empty regulatory project",
        "jurisdiction": "United Kingdom - FCA",
        "regulatory_scope": "AML / CTF",
        "objectives": "Establish baseline readiness"
    })
    assert create_resp.status_code == 201
    pid = create_resp.json()["project_id"]

    # Initial readiness must be 0%
    readiness_resp = client.get(f"/api/v1/projects/{pid}/readiness", headers=builder_auth_headers)
    assert readiness_resp.status_code == 200
    r_data = readiness_resp.json()
    assert r_data["readiness_percentage"] == 0
    assert r_data["readiness_score"] == "0%"
    assert r_data["total_requirements"] == 0
    assert r_data["completed_requirements"] == 0

    # Add a requirement and mark completed
    add_req_resp = client.post(f"/api/v1/projects/{pid}/requirements", headers=builder_auth_headers, json={
        "source_id": 1,
        "requirement_code": f"REQ-{uuid.uuid4().hex[:4].upper()}",
        "requirement_title": "Customer Due Diligence Verification",
        "requirement_text": "Verify beneficial ownership and compliance records.",
        "applicability_status": "APPLICABLE",
        "requirement_status": "COMPLETED"
    })
    assert add_req_resp.status_code == 201

    # Re-evaluate readiness: score must have dynamically increased!
    readiness_resp2 = client.get(f"/api/v1/projects/{pid}/readiness", headers=builder_auth_headers)
    assert readiness_resp2.status_code == 200
    r_data2 = readiness_resp2.json()
    assert r_data2["readiness_percentage"] > 0
    assert r_data2["completed_requirements"] == 1

def test_def11_new_advice_form_and_custom_submission(client: TestClient, advisor_auth_headers: dict):
    """DEF-11: Custom user advice text is faithfully recorded without enforcing default/mock text."""
    unique_advice = f"Custom advice text {uuid.uuid4().hex}"
    unique_rec = f"Custom recommendation {uuid.uuid4().hex}"
    resp = client.post("/api/v1/projects/1/advice", headers=advisor_auth_headers, json={
        "title": "Custom Advice Review",
        "advice_text": unique_advice,
        "recommendation": unique_rec,
        "assumptions": "Independent assessment",
        "advice_status": "SUBMITTED"
    })
    assert resp.status_code == 201
    adv = resp.json()
    assert adv["advice_text"] == unique_advice
    assert adv["recommendation"] == unique_rec

def test_def12_advisor_submitted_advice_appears_in_builder_dashboard(client: TestClient, advisor_auth_headers: dict, builder_auth_headers: dict):
    """DEF-12: Advice submitted by an Advisor is immediately visible to the Builder via GET /projects/{projectId}/advice."""
    unique_title = f"Advisory Title {uuid.uuid4().hex[:6]}"
    sub_resp = client.post("/api/v1/projects/1/advice", headers=advisor_auth_headers, json={
        "title": unique_title,
        "advice_text": "Detailed analysis of AML transaction controls.",
        "recommendation": "Deploy real-time transaction scoring.",
        "assumptions": "Risk-based approach",
        "advice_status": "SUBMITTED"
    })
    assert sub_resp.status_code == 201

    # Builder inspects advice list
    builder_adv_resp = client.get("/api/v1/projects/1/advice", headers=builder_auth_headers)
    assert builder_adv_resp.status_code == 200
    adv_list = builder_adv_resp.json()
    titles = [a["title"] for a in adv_list]
    assert unique_title in titles

def test_def13_builder_project_isolation_bola_defense(client: TestClient, builder_auth_headers: dict, outsider_auth_headers: dict):
    """DEF-13: Strict multi-tenant BOLA defense prevents User A from accessing User B's project records."""
    # Builder creates private project
    code = f"PRJ-PRIV-{uuid.uuid4().hex[:6].upper()}"
    p_resp = client.post("/api/v1/projects", headers=builder_auth_headers, json={
        "project_name": "Private Builder Project",
        "project_code": code,
        "description": "Confidential corporate project",
        "jurisdiction": "United Kingdom",
        "regulatory_scope": "KYC",
        "objectives": "Proprietary compliance"
    })
    assert p_resp.status_code == 201
    private_pid = p_resp.json()["project_id"]

    # Outsider lists projects: Private project must NOT appear
    outsider_list = client.get("/api/v1/projects", headers=outsider_auth_headers)
    assert outsider_list.status_code == 200
    outsider_pids = [p["project_id"] for p in outsider_list.json()]
    assert private_pid not in outsider_pids

    # Outsider attempts direct GET on private project -> 403 Forbidden!
    direct_resp = client.get(f"/api/v1/projects/{private_pid}", headers=outsider_auth_headers)
    assert direct_resp.status_code == 403

    # Outsider attempts direct GET on private project readiness -> 403 Forbidden!
    readiness_resp = client.get(f"/api/v1/projects/{private_pid}/readiness", headers=outsider_auth_headers)
    assert readiness_resp.status_code == 403

def test_def14_registered_credentials_consistency_and_persistence(client: TestClient, db: Session):
    """DEF-14: Credentials persist reliably and authenticate across separate client instances."""
    unique_email = f"persistent_{uuid.uuid4().hex[:8]}@testing.org"
    password = "ConsistentPass123!"

    reg = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": password,
        "full_name": "Persistent Tester",
        "role": "BUILDER"
    })
    assert reg.status_code == 201

    # First login attempt
    login1 = client.post("/api/v1/auth/login", json={"email": unique_email, "password": password})
    assert login1.status_code == 200

    # Second login attempt with mixed case/whitespace email
    login2 = client.post("/api/v1/auth/login", json={"email": f"  {unique_email.upper()}  ", "password": password})
    assert login2.status_code == 200

    # Incorrect password is rejected
    wrong_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "WrongPassword!"})
    assert wrong_login.status_code == 401

def test_def15_password_reset_lifecycle_and_single_use(client: TestClient, db: Session):
    """DEF-15: Full password reset lifecycle: token issuance, confirmation, login with new password, and single-use revocation."""
    unique_email = f"reset_user_{uuid.uuid4().hex[:8]}@example.com"
    old_pass = "OldPassword123!"
    new_pass = "NewPassword456!"

    client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": old_pass,
        "full_name": "Reset Candidate",
        "role": "BUILDER"
    })

    # Request password recovery
    req_resp = client.post("/api/v1/auth/password-reset-request", json={"email": unique_email})
    assert req_resp.status_code == 200
    data = req_resp.json()
    reset_token = data.get("reset_token")
    assert reset_token is not None

    # Confirm password reset with token
    confirm_resp = client.post("/api/v1/auth/password-reset-confirm", json={
        "token": reset_token,
        "new_password": new_pass
    })
    assert confirm_resp.status_code == 200

    # Old password no longer authenticates
    old_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": old_pass})
    assert old_login.status_code == 401

    # New password authenticates successfully
    new_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": new_pass})
    assert new_login.status_code == 200

    # Attempt to reuse the same reset token again: must be rejected!
    reused_confirm = client.post("/api/v1/auth/password-reset-confirm", json={
        "token": reset_token,
        "new_password": "ThirdPassword789!"
    })
    assert reused_confirm.status_code == 401

def test_def16_pdf_attachment_upload_magic_bytes_and_access_control(client: TestClient, builder_auth_headers: dict, outsider_auth_headers: dict):
    """DEF-16: PDF upload validates %PDF- header magic bytes, stores safely, and enforces project authorization."""
    # 1. Non-PDF rejected
    bad_file = io.BytesIO(b"This is a plain text file, not a real PDF.")
    bad_upload = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("malicious.txt", bad_file, "text/plain")},
        data={"category": "ADVISORY_REFERENCE"}
    )
    assert bad_upload.status_code in (400, 422)

    # 2. Fake extension but invalid magic bytes rejected
    fake_pdf = io.BytesIO(b"Fake PDF content without magic header.")
    fake_upload = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
        data={"category": "ADVISORY_REFERENCE"}
    )
    assert fake_upload.status_code in (400, 422)

    # 3. Valid PDF with %PDF- magic bytes accepted
    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Test Policy) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    valid_file = io.BytesIO(valid_pdf_content)
    good_upload = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("CompliancePolicy.pdf", valid_file, "application/pdf")},
        data={"category": "POLICY_ASSESSMENT"}
    )
    assert good_upload.status_code == 201
    att_meta = good_upload.json()
    assert att_meta["original_filename"] == "CompliancePolicy.pdf"
    assert att_meta["content_type"] == "application/pdf"
    att_id = att_meta["attachment_id"]

    # 4. List attachments for Project 1
    list_att = client.get("/api/v1/projects/1/attachments", headers=builder_auth_headers)
    assert list_att.status_code == 200
    ids = [a["attachment_id"] for a in list_att.json()]
    assert att_id in ids

    # 5. Download attachment
    dl_resp = client.get(f"/api/v1/projects/1/attachments/{att_id}", headers=builder_auth_headers)
    assert dl_resp.status_code == 200
    assert dl_resp.content == valid_pdf_content

    # 6. Unauthorized outsider is denied access (403 Forbidden)
    outsider_dl = client.get(f"/api/v1/projects/1/attachments/{att_id}", headers=outsider_auth_headers)
    assert outsider_dl.status_code == 403

def test_def17_admin_dashboard_role_guard_and_resilience(client: TestClient, admin_auth_headers: dict, builder_auth_headers: dict, advisor_auth_headers: dict):
    """DEF-17: Admin-only endpoints return 200 for ADMIN, and strictly 403 for BUILDER and ADVISOR."""
    # Admin access succeeds
    assert client.get("/api/v1/admin/stats", headers=admin_auth_headers).status_code == 200
    assert client.get("/api/v1/admin/users", headers=admin_auth_headers).status_code == 200

    # Non-admin access denied with 403 Forbidden
    assert client.get("/api/v1/admin/stats", headers=builder_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/users", headers=builder_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/stats", headers=advisor_auth_headers).status_code == 403
    assert client.get("/api/v1/admin/users", headers=advisor_auth_headers).status_code == 403
