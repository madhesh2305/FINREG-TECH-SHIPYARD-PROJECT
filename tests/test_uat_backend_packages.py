import uuid
from unittest.mock import MagicMock, patch
import httpx
from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, role: str, prefix: str):
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}_{uid}@finreguat.co.uk"
    password = "StrongPassword123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"{prefix.title()} {uid}",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert reg.status_code in (200, 201), reg.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200, me.text
    return {
        "email": email,
        "password": password,
        "token": token,
        "headers": headers,
        "user": me.json(),
    }


def _relogin_headers(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_uat_regulatory_source_lifecycle_permissions_and_persistence(
    client: TestClient,
    admin_auth_headers: dict,
):
    """
    Page 2 Regulatory Source Workflow:
    - Requires official source_url or document_name (provenance)
    - Submitting initializes as PENDING / PENDING_VALIDATION (even if VALIDATED sent)
    - BUILDER cannot validate/approve/reject/request-changes (403)
    - Only ADMIN can validate; CHANGES_REQUESTED & REJECTED require reason (422 if missing)
    - Persists across refresh / re-login with reviewer, timestamp, decision, reason
    - Emits SOURCE_CREATED, SOURCE_CHANGES_REQUESTED, SOURCE_APPROVED, SOURCE_REJECTED audit events
    """
    builder = _register_and_login(client, "BUILDER", "bld_src")
    advisor = _register_and_login(client, "ADVISOR", "adv_src")

    # Missing both URL and document_name -> 422
    bad_src = client.post(
        "/api/v1/regulatory/sources",
        headers=builder["headers"],
        json={
            "source_title": f"Missing Provenance Source {uuid.uuid4().hex[:6]}",
            "issuing_authority": "FCA",
            "jurisdiction": "UK",
            "publication_date": "2026-01-15",
        },
    )
    assert bad_src.status_code == 422

    # Advisor cannot submit regulatory source -> 403
    adv_submit = client.post(
        "/api/v1/regulatory/sources",
        headers=advisor["headers"],
        json={
            "source_title": "Advisor Unauthorized Source",
            "issuing_authority": "FCA",
            "jurisdiction": "UK",
            "source_url": "https://fca.org.uk/unauth",
            "publication_date": "2026-01-15",
        },
    )
    assert adv_submit.status_code == 403

    # Builder submits source with document_name + attempts self-setting VALIDATED -> must stay PENDING
    title = f"UAT FCA Anti-Bribery Register {uuid.uuid4().hex[:6]}"
    create_resp = client.post(
        "/api/v1/regulatory/sources",
        headers=builder["headers"],
        json={
            "source_title": title,
            "issuing_authority": "Financial Conduct Authority (FCA)",
            "jurisdiction": "UK",
            "document_name": "fca_abc_guidance_2026.pdf",
            "version_label": "v2026.2",
            "publication_date": "2026-02-01",
            "validation_status": "VALIDATED",
            "topic": "Anti-Bribery & Corruption",
            "provenance": "Official FCA PDF Upload UAT-24.11",
            "section_reference": "SYSC 6.1 / FCG Ch.6",
            "applicability_notes": "Applies pending project-level scoping",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    src = create_resp.json()
    sid = src["source_id"]
    assert src["validation_status"] == "PENDING"
    assert src["validation_state"] == "PENDING_VALIDATION"
    assert src["document_name"] == "fca_abc_guidance_2026.pdf"
    assert src["source_code"] == f"SRC-{sid:03d}"

    # Builder cannot validate or approve -> 403
    for action_call in (
        client.patch(
            f"/api/v1/regulatory/sources/{sid}/validate",
            headers=builder["headers"],
            json={"decision": "APPROVED", "reason": "Self approve attempt"},
        ),
        client.post(
            f"/api/v1/regulatory/sources/{sid}/approve",
            headers=builder["headers"],
            json={"decision": "APPROVED"},
        ),
    ):
        assert action_call.status_code == 403

    # Unapproved source is excluded from approved regulatory-requirements library by default
    lib_before = client.get("/api/v1/regulatory-requirements", headers=builder["headers"])
    assert lib_before.status_code == 200
    assert not any(item["source_id"] == sid for item in lib_before.json())

    # Admin requests changes without reason -> 422
    no_reason = client.patch(
        f"/api/v1/regulatory/sources/{sid}/validate",
        headers=admin_auth_headers,
        json={"decision": "CHANGES_REQUESTED", "reason": "   "},
    )
    assert no_reason.status_code == 422

    # Admin requests changes with reason -> persists PENDING + CHANGES_REQUESTED + reviewer metadata
    chg_resp = client.patch(
        f"/api/v1/regulatory/sources/{sid}/validate",
        headers=admin_auth_headers,
        json={"decision": "CHANGES_REQUESTED", "reason": "Attach full FCA annex page citations"},
    )
    assert chg_resp.status_code == 200, chg_resp.text
    chg_data = chg_resp.json()
    assert chg_data["validation_status"] == "PENDING"
    assert chg_data["validation_state"] == "CHANGES_REQUESTED"
    assert chg_data["review_reason"] == "Attach full FCA annex page citations"
    assert chg_data["reviewer_name"] is not None
    assert chg_data["reviewed_at"] is not None

    # Requirement creation must FAIL against CHANGES_REQUESTED source
    proj_resp = client.post(
        "/api/v1/projects",
        headers=builder["headers"],
        json={
            "project_name": f"Source Gate Test {uuid.uuid4().hex[:6]}",
            "jurisdiction": "SG",
            "regulatory_scope": "Anti-Bribery",
        },
    )
    assert proj_resp.status_code == 201
    pid = proj_resp.json()["project_id"]

    blocked_req = client.post(
        f"/api/v1/projects/{pid}/requirements",
        headers=builder["headers"],
        json={
            "source_id": sid,
            "requirement_code": f"REQ-BLK-{uuid.uuid4().hex[:5]}",
            "requirement_title": "Should Be Blocked",
            "requirement_text": "Cannot publish requirement from unapproved source.",
        },
    )
    assert blocked_req.status_code == 422

    # Admin approves source -> persists across fresh login
    app_resp = client.patch(
        f"/api/v1/regulatory/sources/{sid}/validate",
        headers=admin_auth_headers,
        json={"decision": "APPROVED", "reason": "Verified annex citations and official register match"},
    )
    assert app_resp.status_code == 200, app_resp.text
    assert app_resp.json()["validation_status"] == "VALIDATED"
    assert app_resp.json()["validation_state"] == "APPROVED"

    relogin_bld = _relogin_headers(client, builder["email"], builder["password"])
    fetched = client.get(f"/api/v1/regulatory/sources/{sid}", headers=relogin_bld)
    assert fetched.status_code == 200
    f_data = fetched.json()
    assert f_data["validation_state"] == "APPROVED"
    assert f_data["decision"] == "APPROVED"
    assert f_data["review_reason"] == "Verified annex citations and official register match"
    assert f_data["reviewer_name"] is not None

    # Second source rejected cleanly
    rej_create = client.post(
        "/api/v1/regulatory/sources",
        headers=builder["headers"],
        json={
            "source_title": f"Superseded Draft {uuid.uuid4().hex[:6]}",
            "issuing_authority": "FCA",
            "jurisdiction": "UK",
            "source_url": "https://fca.org.uk/draft-2019",
            "publication_date": "2019-01-01",
        },
    )
    assert rej_create.status_code == 201
    rej_sid = rej_create.json()["source_id"]

    rej_no_reason = client.post(
        f"/api/v1/regulatory/sources/{rej_sid}/reject",
        headers=admin_auth_headers,
        json={"decision": "REJECTED", "reason": ""},
    )
    assert rej_no_reason.status_code == 422

    rej_ok = client.post(
        f"/api/v1/regulatory/sources/{rej_sid}/reject",
        headers=admin_auth_headers,
        json={"decision": "REJECTED", "reason": "Superseded by 2026 statutory instrument"},
    )
    assert rej_ok.status_code == 200
    assert rej_ok.json()["validation_status"] == "REJECTED"
    assert rej_ok.json()["validation_state"] == "REJECTED"

    # Audit events verify full regulatory source lifecycle
    audit_resp = client.get("/api/v1/admin/audit-events?limit=100", headers=admin_auth_headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    sid_events = {e["event_type"] for e in events if e["entity_type"] == "REGULATORY_SOURCE" and e["entity_id"] == sid}
    assert {"SOURCE_CREATED", "SOURCE_CHANGES_REQUESTED", "SOURCE_APPROVED"}.issubset(sid_events)
    assert any(
        e["entity_type"] == "REGULATORY_SOURCE" and e["entity_id"] == rej_sid and e["event_type"] == "SOURCE_REJECTED"
        for e in events
    )


def test_uat_project_scope_requirements_and_advisor_requirements_isolation(
    client: TestClient,
    admin_auth_headers: dict,
):
    """
    Page 3 Requirement Creation & Project Scope:
    - Jurisdiction-scoped project creation (SG gets 0 UK baseline items; UK gets APPROVED UK sources marked UNDER_REVIEW)
    - Source approval does not auto-mark requirements APPLICABLE
    - Published requirements expose source_id, section_reference, source_version, jurisdiction, applicability_notes, validation_state
    - Advisor API /advisors/me/requirements returns [] before assignment, 403 for unassigned project, scoped reqs only after acceptance
    """
    builder = _register_and_login(client, "BUILDER", "bld_req")
    advisor = _register_and_login(client, "ADVISOR", "adv_req")

    # 1. Fresh SG project must not inherit unrelated UK/EU requirements
    sg_proj = client.post(
        "/api/v1/projects",
        headers=builder["headers"],
        json={
            "project_name": f"SG Scoped Project {uuid.uuid4().hex[:6]}",
            "jurisdiction": "SG",
            "regulatory_scope": "AML / MAS",
        },
    )
    assert sg_proj.status_code == 201
    sg_pid = sg_proj.json()["project_id"]
    sg_reqs = client.get(f"/api/v1/projects/{sg_pid}/requirements", headers=builder["headers"])
    assert sg_reqs.status_code == 200
    assert sg_reqs.json() == []

    # 2. Fresh UK project gets approved UK baseline requirements marked UNDER_REVIEW (not blind APPLICABLE)
    uk_proj = client.post(
        "/api/v1/projects",
        headers=builder["headers"],
        json={
            "project_name": f"UK Scoped Project {uuid.uuid4().hex[:6]}",
            "jurisdiction": "UK",
            "regulatory_scope": "Anti-Bribery & Corruption",
        },
    )
    assert uk_proj.status_code == 201
    uk_pid = uk_proj.json()["project_id"]
    uk_reqs_resp = client.get(f"/api/v1/projects/{uk_pid}/requirements?scoped_only=true", headers=builder["headers"])
    assert uk_reqs_resp.status_code == 200
    uk_reqs = uk_reqs_resp.json()
    assert len(uk_reqs) >= 1
    assert all(r["applicability_status"] == "UNDER_REVIEW" for r in uk_reqs)
    assert all("uk" in (r["jurisdiction"] or "").lower() for r in uk_reqs)

    # 3. Publish custom requirement from approved source 1 with full metadata
    req_code = f"REQ-UAT-{uuid.uuid4().hex[:6].upper()}"
    pub_resp = client.post(
        f"/api/v1/projects/{uk_pid}/requirements",
        headers=builder["headers"],
        json={
            "source_id": 1,
            "requirement_code": req_code,
            "requirement_title": "Adequate Procedures Board Sign-Off",
            "requirement_text": "Verify top-level commitment and proportionate ABC controls.",
            "section_reference": "Bribery Act 2010, Sec. 7 & Guidance Principle 2",
            "applicability_notes": "Confirmed applicable to UK commercial entity",
            "applicability_status": "APPLICABLE",
        },
    )
    assert pub_resp.status_code == 201, pub_resp.text
    pub = pub_resp.json()
    assert pub["source_id"] == 1
    assert pub["section_reference"] == "Bribery Act 2010, Sec. 7 & Guidance Principle 2"
    assert pub["source_version"] is not None
    assert pub["jurisdiction"] is not None
    assert pub["applicability_notes"] == "Confirmed applicable to UK commercial entity"
    assert pub["validation_state"] == "APPROVED"

    # 4. Advisor with NO accepted assignment gets [] and 403 on project scope
    adv_before = client.get("/api/v1/advisors/me/requirements", headers=advisor["headers"])
    assert adv_before.status_code == 200
    assert adv_before.json() == []
    adv_proj_denied = client.get(
        f"/api/v1/advisors/me/requirements?project_id={uk_pid}",
        headers=advisor["headers"],
    )
    assert adv_proj_denied.status_code == 403

    # Invite advisor -> still PENDING -> MUST STILL get [] and 403!
    inv_resp = client.post(
        f"/api/v1/projects/{uk_pid}/advisor-invitations",
        headers=builder["headers"],
        json={"advisor_email": advisor["email"], "access_level": "REGULATORY", "expiry_days": 7},
    )
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["invitation_id"]

    adv_pending = client.get("/api/v1/advisors/me/requirements", headers=advisor["headers"])
    assert adv_pending.status_code == 200
    assert adv_pending.json() == []
    assert client.get(f"/api/v1/projects/{uk_pid}/requirements", headers=advisor["headers"]).status_code == 403

    # Accept invitation -> NOW advisor sees ONLY accepted UK project requirements (not unrelated projects)
    acc_resp = client.post(
        f"/api/v1/projects/{uk_pid}/advisor-invitations/{inv_id}/accept",
        headers=advisor["headers"],
    )
    assert acc_resp.status_code == 200

    adv_after = client.get("/api/v1/advisors/me/requirements", headers=advisor["headers"])
    assert adv_after.status_code == 200
    items = adv_after.json()
    assert any(r["requirement_code"] == req_code for r in items)
    assert all(r["project_id"] == uk_pid for r in items)


def test_uat_advisor_access_cancellation_two_advisor_limit_and_project_deletion(
    client: TestClient,
    admin_auth_headers: dict,
):
    """
    Page 3 Advisor Access, Lifecycle, Limits & Project Removal (plus UAT #7, #8, #9):
    - Expertise selection (/advisors/select) and invitation do NOT grant project access prior to acceptance
    - 2-advisor limit enforces max 2 across BOTH pending invitations and accepted/active advisors
    - Cancellation/revocation removes ProjectMember + updates invitation status permanently across refresh
    - Cancelling frees a slot for re-inviting another advisor
    - Only the invited advisor may accept an invitation (403 otherwise)
    - DELETE /projects/{id} cleanly removes project and children while preserving immutable audit events
    """
    builder = _register_and_login(client, "BUILDER", "bld_adv")
    adv1 = _register_and_login(client, "ADVISOR", "sarah_j")
    adv2 = _register_and_login(client, "ADVISOR", "mira_k")
    adv3 = _register_and_login(client, "ADVISOR", "third_adv")

    proj_resp = client.post(
        "/api/v1/projects",
        headers=builder["headers"],
        json={
            "project_name": f"Advisor Governance Project {uuid.uuid4().hex[:6]}",
            "jurisdiction": "UK",
            "regulatory_scope": "Anti-Bribery",
        },
    )
    assert proj_resp.status_code == 201
    pid = proj_resp.json()["project_id"]

    # 1. Select Advisor 1 via expertise selection endpoint -> PENDING ONLY, NO access yet!
    sel_resp = client.post(
        f"/api/v1/projects/{pid}/advisors/select",
        headers=builder["headers"],
        json={"advisor_email": adv1["email"], "access_level": "LEGAL", "expiry_days": 7},
    )
    assert sel_resp.status_code == 201, sel_resp.text
    inv1_id = sel_resp.json()["invitation_id"]
    assert sel_resp.json()["invitation_status"] == "PENDING"

    # Verify adv1 has NO project access before accepting
    assert client.get(f"/api/v1/projects/{pid}", headers=adv1["headers"]).status_code == 403
    adv1_projects = client.get("/api/v1/projects", headers=adv1["headers"]).json()
    assert not any(p["project_id"] == pid for p in adv1_projects)

    # Adv2 cannot accept Adv1's invitation -> 403
    wrong_accept = client.post(
        f"/api/v1/projects/{pid}/advisor-invitations/{inv1_id}/accept",
        headers=adv2["headers"],
    )
    assert wrong_accept.status_code == 403

    # 2. Invite Advisor 2 and accept -> slot 1 ACCEPTED (adv2), slot 2 PENDING (adv1) = 2/2 occupied
    inv2_resp = client.post(
        f"/api/v1/projects/{pid}/advisor-invitations",
        headers=builder["headers"],
        json={"advisor_email": adv2["email"], "access_level": "REGULATORY", "expiry_days": 7},
    )
    assert inv2_resp.status_code == 201
    inv2_id = inv2_resp.json()["invitation_id"]

    assert client.post(
        f"/api/v1/projects/{pid}/advisor-invitations/{inv2_id}/accept",
        headers=adv2["headers"],
    ).status_code == 200

    # Summary counts check: 1 active + 1 pending = 2/2, remaining = 0
    sum_resp = client.get(f"/api/v1/projects/{pid}/advisor-summary", headers=builder["headers"])
    assert sum_resp.status_code == 200
    sdata = sum_resp.json()
    assert sdata["max_advisors"] == 2
    assert sdata["counts_rule"] == "PENDING_AND_ACCEPTED"
    assert sdata["active_advisors_count"] == 1
    assert sdata["pending_invitations_count"] == 1
    assert sdata["occupied_advisor_slots"] == 2
    assert sdata["remaining_advisor_slots"] == 0

    # 3. Attempting to invite a 3rd advisor (adv3) must fail with 409 Conflict
    inv3_blocked = client.post(
        f"/api/v1/projects/{pid}/advisor-invitations",
        headers=builder["headers"],
        json={"advisor_email": adv3["email"], "access_level": "TECH", "expiry_days": 7},
    )
    assert inv3_blocked.status_code == 409

    # 4. Adv1 accepts, then Builder cancels Adv1's invitation -> MUST revoke membership AND persist after refresh
    assert client.post(
        f"/api/v1/projects/{pid}/advisor-invitations/{inv1_id}/accept",
        headers=adv1["headers"],
    ).status_code == 200
    assert client.get(f"/api/v1/projects/{pid}", headers=adv1["headers"]).status_code == 200

    cancel_resp = client.post(
        f"/api/v1/projects/{pid}/advisor-invitations/{inv1_id}/cancel",
        headers=builder["headers"],
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["invitation_status"] == "REVOKED"

    # Re-login / refresh as Adv1 -> still revoked (403, not returned after refresh!)
    adv1_fresh = _relogin_headers(client, adv1["email"], adv1["password"])
    assert client.get(f"/api/v1/projects/{pid}", headers=adv1_fresh).status_code == 403
    assert not any(p["project_id"] == pid for p in client.get("/api/v1/projects", headers=adv1_fresh).json())

    # Check project detail assigned_advisors does NOT show cancelled Adv1
    proj_after_cancel = client.get(f"/api/v1/projects/{pid}", headers=builder["headers"]).json()
    assert adv1["user"]["full_name"] not in proj_after_cancel["assigned_advisors"]
    assert adv2["user"]["full_name"] in proj_after_cancel["assigned_advisors"]

    # Cancelling freed 1 slot -> inviting Adv3 now succeeds!
    inv3_ok = client.post(
        f"/api/v1/projects/{pid}/advisor-invitations",
        headers=builder["headers"],
        json={"advisor_email": adv3["email"], "access_level": "TECH", "expiry_days": 7},
    )
    assert inv3_ok.status_code == 201

    # 5. Non-owner (Adv2) cannot delete project -> 403
    assert client.delete(f"/api/v1/projects/{pid}", headers=adv2["headers"]).status_code == 403

    # 6. Owner deletes project -> succeeds, absent after refresh, audit history preserved
    del_resp = client.delete(f"/api/v1/projects/{pid}", headers=builder["headers"])
    assert del_resp.status_code == 200, del_resp.text
    assert del_resp.json()["status"] == "deleted"

    bld_fresh = _relogin_headers(client, builder["email"], builder["password"])
    assert client.get(f"/api/v1/projects/{pid}", headers=bld_fresh).status_code == 404
    assert not any(p["project_id"] == pid for p in client.get("/api/v1/projects", headers=bld_fresh).json())

    admin_events = client.get("/api/v1/admin/audit-events?limit=200", headers=admin_auth_headers).json()
    proj_audit_types = {e["event_type"] for e in admin_events if e["entity_id"] == pid}
    assert "PROJECT_DELETED" in proj_audit_types
    assert any(
        e["event_type"] == "ADVISOR_INVITATION_CANCELLED" and e["entity_id"] == inv1_id
        for e in admin_events
    )


def test_uat_audit_immutability_and_rag_boundary_health_and_503(
    client: TestClient,
    admin_auth_headers: dict,
):
    """
    Page 3 Audit Immutability & AI/RAG Health/503 Contract:
    - Audit events expose read-only endpoints; PATCH/PUT/DELETE/POST return 405 Method Not Allowed
    - /api/v1/rag/health reports connected when port 8001 responds and unreachable when offline
    - /api/v1/rag/analyze returns 503 Service Unavailable cleanly when upstream RAG is unreachable
    """
    # Audit immutability
    for method in (client.post, client.patch, client.put, client.delete):
        r1 = method("/api/v1/projects/1/audit-events", headers=admin_auth_headers)
        r2 = method("/api/v1/admin/audit-events", headers=admin_auth_headers)
        assert r1.status_code == 405
        assert r2.status_code == 405

    # RAG health check against offline port -> degraded + unreachable
    mock_client_down = MagicMock()
    mock_client_down.__enter__.return_value = mock_client_down
    mock_client_down.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client_down.post.side_effect = httpx.ConnectError("Connection refused")

    with patch("app.services.rag_service.httpx.Client", return_value=mock_client_down):
        h_down = client.get("/api/v1/rag/health")
        assert h_down.status_code == 200
        assert h_down.json()["status"] == "degraded"
        assert h_down.json()["rag_microservice"]["status"] == "unreachable"

        builder = _register_and_login(client, "BUILDER", "bld_rag")
        analyze_down = client.post(
            "/api/v1/rag/analyze",
            headers=builder["headers"],
            json={"query": "What are UK Bribery Act Section 7 adequate procedures?"},
        )
        assert analyze_down.status_code == 503
        assert "8001" in analyze_down.json()["detail"]

    # RAG health check when healthy
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    mock_resp_ok.json.return_value = {
        "status": "ok",
        "chromadb_status": "connected",
        "rag_pipeline_initialized": True,
    }
    mock_client_up = MagicMock()
    mock_client_up.__enter__.return_value = mock_client_up
    mock_client_up.get.return_value = mock_resp_ok

    with patch("app.services.rag_service.httpx.Client", return_value=mock_client_up):
        h_up = client.get("/api/v1/rag/health")
        assert h_up.status_code == 200
        assert h_up.json()["status"] == "healthy"
        assert h_up.json()["rag_microservice"]["status"] == "connected"
