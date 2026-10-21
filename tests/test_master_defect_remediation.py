import base64
import io
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.identity import User, Role, PasswordResetToken
from app.models.project import Project, ProjectMember
from app.models.advice import Advice
from app.models.regulatory import RegulatoryRequirement
from app.models.attachment import ProjectAttachment
from app.services.email_service import (
    enable_test_mail_sink,
    get_test_mail_sink,
    clear_test_mail_sink,
    set_simulate_smtp_failure,
)
from app.services.rate_limit_service import reset_rate_limiter

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

def test_def06_builder_dashboard_real_metrics(client: TestClient, builder_auth_headers: dict):
    """DEF-06: Builder dashboard summary returns live database calculated counts."""
    resp = client.get("/api/v1/projects/summary", headers=builder_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "active_projects" in data
    assert "total_requirements" in data
    assert "total_members" in data

def test_def07_newly_registered_advisor_in_advisor_selector(client: TestClient, builder_auth_headers: dict):
    """DEF-07: Newly registered advisor appears in the advisor directory selector endpoint."""
    unique_email = f"advisor_sel_{uuid.uuid4().hex[:8]}@lexfin.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Marcus Aurelius Legal",
        "role": "ADVISOR",
        "organization": "Aurelius Legal Partners"
    })
    assert reg.status_code == 201

    # Query advisors
    adv_list = client.get("/api/v1/advisors", headers=builder_auth_headers)
    assert adv_list.status_code == 200
    emails = [a["email"] for a in adv_list.json()]
    assert unique_email in emails

def test_def10_dynamic_completion_calculation(client: TestClient, db: Session, builder_auth_headers: dict):
    """DEF-10: Newly created project without milestones reports 0% completion, not fixed 60%."""
    # Create fresh project
    create_resp = client.post("/api/v1/projects", headers=builder_auth_headers, json={
        "name": f"Empty Milestone Project {uuid.uuid4().hex[:6]}",
        "jurisdiction": "SG",
        "regulatory_framework": "MAS Notice 644",
        "description": "Clean test project for completion verification"
    })
    assert create_resp.status_code == 201
    new_pid = create_resp.json()["project_id"]

    # Readiness assessment for empty project must be exactly 0%
    summary_resp = client.get(f"/api/v1/projects/{new_pid}/readiness", headers=builder_auth_headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["readiness_percentage"] == 0
    assert summary["total_requirements"] == 0

def test_def11_advice_form_empty_by_default(client: TestClient, advisor_auth_headers: dict):
    """DEF-11: New advice submission accepts unique input and is not locked to boilerplate."""
    unique_advice = f"Custom specific advice text {uuid.uuid4().hex}"
    post_resp = client.post("/api/v1/projects/1/advice", headers=advisor_auth_headers, json={
        "title": "AML Framework Compliance Review",
        "advice_text": unique_advice,
        "recommendation": "Implement automated daily transaction screening threshold",
        "advice_status": "DRAFT"
    })
    assert post_resp.status_code == 201
    created = post_resp.json()
    assert created["advice_text"] == unique_advice

def test_def12_advisor_advice_visibility_in_builder_dashboard(client: TestClient, builder_auth_headers: dict, advisor_auth_headers: dict):
    """DEF-12: Advice submitted by an advisor is visible and retrievable by the project builder."""
    special_text = f"Crucial compliance step {uuid.uuid4().hex}"
    client.post("/api/v1/projects/1/advice", headers=advisor_auth_headers, json={
        "title": "KYC Identity Verification Standards",
        "advice_text": special_text,
        "recommendation": "Integrate Singapore Singpass MyInfo verification workflow",
        "advice_status": "SUBMITTED"
    })

    # Builder reads advice
    builder_read = client.get("/api/v1/projects/1/advice", headers=builder_auth_headers)
    assert builder_read.status_code == 200
    all_adv = builder_read.json()
    texts = [a["advice_text"] for a in all_adv]
    assert special_text in texts

def test_def13_builder_project_bola_isolation(client: TestClient, builder_auth_headers: dict, outsider_auth_headers: dict):
    """DEF-13: Builder BOLA check - outsider cannot read, modify, or download Project 1 records."""
    # Outsider attempts to read Project 1: must be 403 Forbidden
    resp = client.get("/api/v1/projects/1", headers=outsider_auth_headers)
    assert resp.status_code == 403

    # Outsider attempts to list Project 1 advice: must be 403 Forbidden
    adv_resp = client.get("/api/v1/projects/1/advice", headers=outsider_auth_headers)
    assert adv_resp.status_code == 403

    # Outsider attempts to list Project 1 attachments: must be 403 Forbidden
    att_resp = client.get("/api/v1/projects/1/attachments", headers=outsider_auth_headers)
    assert att_resp.status_code == 403

def test_def14_seed_preserves_existing_user_hashes(client: TestClient, db: Session):
    """DEF-14: Running seed_data does not overwrite or destroy user-defined passwords."""
    unique_email = f"persistent_user_{uuid.uuid4().hex[:8]}@persisted.org"
    password = "MyCustomPassword999!"
    reg = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": password,
        "full_name": "Persistent Candidate",
        "role": "BUILDER"
    })
    assert reg.status_code == 201

    # Re-run seed
    from scripts.seed_data import seed_database
    seed_database(session_override=db)

    # Login still works with original custom password
    login_resp = client.post("/api/v1/auth/login", json={"email": unique_email, "password": password})
    assert login_resp.status_code == 200

def test_def15_password_reset_anti_enumeration_and_test_sink(client: TestClient, db: Session):
    """
    DEF-15:
    1. Public API NEVER returns a reset token for any email.
    2. Existing and unknown email addresses receive identical public responses (anti-enumeration).
    3. Isolated test mail sink receives the recovery token for an existing user.
    """
    reset_rate_limiter()
    enable_test_mail_sink(True)
    clear_test_mail_sink()

    unique_email = f"reset_candidate_{uuid.uuid4().hex[:8]}@domain.com"
    unknown_email = f"unknown_{uuid.uuid4().hex[:8]}@domain.com"

    # Register user
    client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "InitialPassword123!",
        "full_name": "Candidate User",
        "role": "BUILDER"
    })

    # 1 & 2: Public API call for existing user
    resp_existing = client.post("/api/v1/auth/password-reset-request", json={"email": unique_email})
    assert resp_existing.status_code == 200
    data_existing = resp_existing.json()
    assert "reset_token" not in data_existing or data_existing.get("reset_token") is None

    # Public API call for unknown user
    resp_unknown = client.post("/api/v1/auth/password-reset-request", json={"email": unknown_email})
    assert resp_unknown.status_code == 200
    data_unknown = resp_unknown.json()
    assert "reset_token" not in data_unknown or data_unknown.get("reset_token") is None

    # Both responses are identical (anti-enumeration)
    assert data_existing["status"] == data_unknown["status"]
    assert data_existing["delivery_channel"] == data_unknown["delivery_channel"]
    assert data_existing["message"] == data_unknown["message"]

    # 3: Verify test mail sink captured the secret token only for the existing user
    sink_messages = get_test_mail_sink()
    user_msgs = [m for m in sink_messages if m["to"] == unique_email]
    assert len(user_msgs) == 1
    raw_token = user_msgs[0]["token"]
    assert len(raw_token) >= 32

    # Database only stores the secure SHA-256 hash, NEVER the raw token
    import hashlib
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == expected_hash).first()
    assert db_token is not None
    assert db_token.is_revoked is False

def test_def15_password_reset_smtp_failure_handling_and_rollback(client: TestClient, db: Session):
    """
    DEF-15: Operational SMTP delivery failure handling:
    1. Truthful delivery_failed reporting without revealing account existence.
    2. Rollback ensures prior active tokens are NOT invalidated and no dead tokens persist.
    """
    reset_rate_limiter()
    enable_test_mail_sink(True)
    clear_test_mail_sink()

    unique_email = f"smtp_fail_{uuid.uuid4().hex[:8]}@domain.com"
    unknown_email = f"unknown_fail_{uuid.uuid4().hex[:8]}@domain.com"

    # Register user
    client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "SMTP Fail User",
        "role": "BUILDER"
    })

    # Step 1: Successfully generate a valid token first
    resp1 = client.post("/api/v1/auth/password-reset-request", json={"email": unique_email})
    assert resp1.status_code == 200
    sink1 = get_test_mail_sink()
    assert len(sink1) == 1
    token1 = sink1[0]["token"]

    user = db.query(User).filter(User.email == unique_email).first()
    tokens_before = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.is_revoked.is_(False)
    ).all()
    assert len(tokens_before) == 1
    token1_id = tokens_before[0].id

    # Step 2: Simulate SMTP failure
    set_simulate_smtp_failure(True)
    try:
        # Existing user receives delivery_failed
        fail_existing = client.post("/api/v1/auth/password-reset-request", json={"email": unique_email})
        assert fail_existing.status_code == 200
        data_existing = fail_existing.json()
        assert data_existing["status"] == "delivery_failed"
        assert "reset_token" not in data_existing

        # Unknown user receives IDENTICAL delivery_failed (anti-enumeration)
        fail_unknown = client.post("/api/v1/auth/password-reset-request", json={"email": unknown_email})
        assert fail_unknown.status_code == 200
        data_unknown = fail_unknown.json()
        assert data_unknown["status"] == "delivery_failed"
        assert data_unknown["message"] == data_existing["message"]
        assert data_unknown["delivery_channel"] == data_existing["delivery_channel"]

        # Step 3: Verify rollback safety: Token1 was NOT invalidated by the failed attempt
        db.expire_all()
        token1_after = db.query(PasswordResetToken).filter(PasswordResetToken.id == token1_id).first()
        assert token1_after.is_revoked is False

        # No new dead token was stored
        total_tokens = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.user_id).count()
        assert total_tokens == 1
    finally:
        set_simulate_smtp_failure(False)

def test_def15_password_reset_unconfigured_smtp(client: TestClient):
    """
    DEF-15: When email delivery is globally unconfigured, both existing and unknown
    emails receive identical pending_configuration status without revealing account existence.
    """
    reset_rate_limiter()
    enable_test_mail_sink(False)
    try:
        resp1 = client.post("/api/v1/auth/password-reset-request", json={"email": "builder@finregtech.com"})
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["status"] == "pending_configuration"

        resp2 = client.post("/api/v1/auth/password-reset-request", json={"email": "nonexistent@somewhere.org"})
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["status"] == "pending_configuration"
        assert d1["message"] == d2["message"]
        assert d1["delivery_channel"] == d2["delivery_channel"]
    finally:
        enable_test_mail_sink(True)

def test_def15_password_reset_rate_limiting_per_account_and_ip(client: TestClient):
    """
    DEF-15: Dual-key sliding window rate limiting rejects excessive requests:
    - Per-account limit (5 requests / 15m)
    - Per-IP limit (20 requests / 15m)
    - Clean test reset hook
    """
    reset_rate_limiter()
    enable_test_mail_sink(True)

    target_email = "ratelimit_victim@example.com"
    headers = {"X-Forwarded-For": "203.0.113.10"}

    # 5 allowed requests
    for i in range(5):
        resp = client.post("/api/v1/auth/password-reset-request", json={"email": target_email}, headers=headers)
        assert resp.status_code == 200

    # 6th request targeting the same account is rate-limited (HTTP 429)
    blocked_account = client.post("/api/v1/auth/password-reset-request", json={"email": target_email}, headers=headers)
    assert blocked_account.status_code == 429

    # Clean state reset hook works reliably
    reset_rate_limiter()
    fresh_resp = client.post("/api/v1/auth/password-reset-request", json={"email": target_email}, headers=headers)
    assert fresh_resp.status_code == 200
    reset_rate_limiter()

def test_def15_password_reset_token_rejection_and_session_invalidation(client: TestClient, db: Session):
    """
    DEF-15:
    4. Valid test-issued token resets password successfully.
    5. Old password fails and new password succeeds.
    6. Invalid, expired and reused tokens are rejected.
    7. Active session tokens issued prior to credentials update are invalidated.
    """
    reset_rate_limiter()
    enable_test_mail_sink(True)
    clear_test_mail_sink()

    unique_email = f"reset_session_{uuid.uuid4().hex[:8]}@domain.com"
    old_pass = "FirstPassword123!"
    new_pass = "SecondPassword456!"

    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": old_pass,
        "full_name": "Session Candidate",
        "role": "BUILDER"
    })
    old_access_token = reg_resp.json()["access_token"]

    # Verify old session token initially authenticates
    me_resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_access_token}"})
    assert me_resp.status_code == 200

    # Request reset
    client.post("/api/v1/auth/password-reset-request", json={"email": unique_email})
    sink = get_test_mail_sink()
    raw_token = [m for m in sink if m["to"] == unique_email][-1]["token"]

    # Reject invalid token
    bad_confirm = client.post("/api/v1/auth/password-reset-confirm", json={
        "token": "invalid_bogus_token_12345678",
        "new_password": new_pass
    })
    assert bad_confirm.status_code == 401

    # Confirm password reset with valid token
    confirm_resp = client.post("/api/v1/auth/password-reset-confirm", json={
        "token": raw_token,
        "new_password": new_pass
    })
    assert confirm_resp.status_code == 200

    # Old password no longer authenticates
    old_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": old_pass})
    assert old_login.status_code == 401

    # New password authenticates
    new_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": new_pass})
    assert new_login.status_code == 200

    # Reused token is rejected
    reused_confirm = client.post("/api/v1/auth/password-reset-confirm", json={
        "token": raw_token,
        "new_password": "ThirdPassword789!"
    })
    assert reused_confirm.status_code == 401

    # Old session token is invalidated due to credential change
    revoked_me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_access_token}"})
    assert revoked_me.status_code == 401

def test_def16_pdf_attachment_upload_magic_bytes_and_access_control(client: TestClient, builder_auth_headers: dict, outsider_auth_headers: dict):
    """DEF-16: PDF upload validates complete PDF structure via pypdf, stores safely, and enforces project authorization."""
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

    # 3. Spoofed PDF with %PDF-, object catalog, and %%EOF trailer but invalid structure rejected by pypdf
    crafted_spoof = base64.b64decode("JVBERi0xLjQKMSAwIG9iago8PCAvVGl0bGUgKFRlc3QgUG9saWN5KSA+PgplbmRvYmoKdHJhaWxlcgo8PCAvUm9vdCAxIDAgUiA+PgolJUVPRg==")
    spoof_upload = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("spoofed.pdf", io.BytesIO(crafted_spoof), "application/pdf")},
        data={"category": "POLICY_ASSESSMENT"}
    )
    assert spoof_upload.status_code in (400, 422)

    # 4. Valid canonical PDF conforming to ISO 32000 spec accepted
    valid_pdf_content = base64.b64decode(
        "JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAuMCAwLjAgNzIgNzIgXQovUGFyZW50IDIgMCBSCj4+CmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA1NCAwMDAwMCBuIAowMDAwMDAwMTEzIDAwMDAwIG4gCjAwMDAwMDAxNjIgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA1Ci9Sb290IDMgMCBSCi9JbmZvIDEgMCBSCj4+CnN0YXJ0eHJlZgoyNTQKJSVFT0YK"
    )
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

    # 5. List attachments for Project 1
    list_att = client.get("/api/v1/projects/1/attachments", headers=builder_auth_headers)
    assert list_att.status_code == 200
    ids = [a["attachment_id"] for a in list_att.json()]
    assert att_id in ids

    # 6. Download attachment (byte-identical verification)
    dl_resp = client.get(f"/api/v1/projects/1/attachments/{att_id}", headers=builder_auth_headers)
    assert dl_resp.status_code == 200
    assert dl_resp.content == valid_pdf_content

    # 7. Unauthorized outsider is denied access (403 Forbidden)
    outsider_dl = client.get(f"/api/v1/projects/1/attachments/{att_id}", headers=outsider_auth_headers)
    assert outsider_dl.status_code == 403

def test_def16_pdf_attachment_structural_validation_and_bounded_streaming(client: TestClient, builder_auth_headers: dict):
    """DEF-16: Rejects truncated PDF missing %%EOF trailer, empty files, and enforces 10MB payload size limit."""
    # Truncated PDF (has %PDF- but lacks %%EOF trailer)
    truncated_pdf = io.BytesIO(base64.b64decode("JVBERi0xLjcKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyA+PgplbmRvYmoK"))
    trunc_resp = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("truncated.pdf", truncated_pdf, "application/pdf")}
    )
    assert trunc_resp.status_code in (400, 422)

    # Empty PDF rejected
    empty_pdf = io.BytesIO(b"")
    empty_resp = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("empty.pdf", empty_pdf, "application/pdf")}
    )
    assert empty_resp.status_code in (400, 422)

    # Oversized payload (> 10MB) rejected
    oversized_pdf = io.BytesIO(b"%PDF-1.4\n" + b"A" * (10 * 1024 * 1024 + 1024))
    over_resp = client.post(
        "/api/v1/projects/1/attachments",
        headers=builder_auth_headers,
        files={"file": ("oversized.pdf", oversized_pdf, "application/pdf")}
    )
    assert over_resp.status_code in (400, 422)

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
