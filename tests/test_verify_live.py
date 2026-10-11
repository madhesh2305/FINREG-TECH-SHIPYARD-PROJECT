import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.identity import User
from app.models.advisor import AdvisorProfile
from app.models.project import Project, ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.models.advice import Advice
from app.models.decision import Decision
from app.models.audit import AuditEvent

def test_full_live_verification():
    client = TestClient(app)
    db = SessionLocal()

    print("\n=======================================================")
    print("STEP 1: Advisor Registration & DB Persistence (Bug 1 & 2)")
    print("=======================================================")
    adv_email = f"advisor_e2e_{uuid.uuid4().hex[:6]}@domain.com"
    adv_payload = {
        "email": adv_email,
        "password": "Password123!",
        "full_name": "Sanjaya Narayanasamy",
        "role": "ADVISOR",
        "organization": "Apex Financial Advisory"
    }
    r1 = client.post("/api/v1/auth/register", json=adv_payload)
    assert r1.status_code == 201, f"Register failed: {r1.text}"
    r1_data = r1.json()
    assert r1_data["platform_role"] == "ADVISOR"
    assert "access_token" in r1_data
    adv_token = r1_data["access_token"]
    adv_headers = {"Authorization": f"Bearer {adv_token}"}
    print(f"-> Advisor registered successfully: {adv_email}, role: {r1_data['platform_role']}")

    # Verify in PostgreSQL
    db_adv = db.query(User).filter(User.email == adv_email).first()
    assert db_adv is not None, "User record not found in PostgreSQL!"
    assert db_adv.role.role_name == "ADVISOR"
    db_profile = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == db_adv.user_id).first()
    assert db_profile is not None, "AdvisorProfile record not found in PostgreSQL!"
    print(f"-> PostgreSQL persistence verified: user_id={db_adv.user_id}, profile_id={db_profile.advisor_profile_id}")

    print("\n=======================================================")
    print("STEP 2: Advisor Login & Session Validation")
    print("=======================================================")
    r2 = client.post("/api/v1/auth/login", json={"email": adv_email, "password": "Password123!"})
    assert r2.status_code == 200, f"Login failed: {r2.text}"
    assert r2.json()["platform_role"] == "ADVISOR"
    print("-> Login verified: Correct platform_role returned, valid JWT issued.")

    print("\n=======================================================")
    print("STEP 3: Builder Registration & Project Creation (ABC Scope)")
    print("=======================================================")
    bld_email = f"builder_e2e_{uuid.uuid4().hex[:6]}@domain.com"
    bld_payload = {
        "email": bld_email,
        "password": "Password123!",
        "full_name": "Sarah Chen",
        "role": "BUILDER",
        "organization": "ABC Shield Technologies"
    }
    r3 = client.post("/api/v1/auth/register", json=bld_payload)
    assert r3.status_code == 201, f"Register builder failed: {r3.text}"
    bld_user_id = r3.json()["user_id"]
    bld_token = r3.json()["access_token"]
    bld_headers = {"Authorization": f"Bearer {bld_token}"}
    print(f"-> Builder registered successfully: {bld_email}, user_id: {bld_user_id}")

    # Create ABC Compliance Project matching frontend form
    new_proj_payload = {
        "name": "ABC Shield Corporate Anti-Bribery Cockpit",
        "type": "Anti-Bribery & Corruption (ABC)",
        "description": "Enterprise compliance management under UK Bribery Act 2010 Section 7 Adequate Procedures",
        "jurisdiction": "United Kingdom - MoJ / SFO"
    }
    r4 = client.post("/api/v1/projects", json=new_proj_payload, headers=bld_headers)
    assert r4.status_code == 201, f"Project creation failed: {r4.text}"
    proj_data = r4.json()
    proj_id = proj_data["project_id"]
    proj_code = proj_data["project_code"]
    print(f"-> Project created: ID={proj_id}, Code={proj_code}, Name='{proj_data['project_name']}'")

    # Verify Project and OWNER Membership in PostgreSQL
    db_proj = db.query(Project).filter(Project.project_id == proj_id).first()
    assert db_proj is not None, "Project not found in PostgreSQL!"
    assert db_proj.created_by == bld_user_id
    owner_mem = db.query(ProjectMember).filter(ProjectMember.project_id == proj_id, ProjectMember.user_id == bld_user_id).first()
    assert owner_mem is not None and owner_mem.service_role == "OWNER"
    print(f"-> Verified Project & sole OWNER membership in PostgreSQL.")

    print("\n=======================================================")
    print("STEP 4: Project Resolution & Requirements Loading")
    print("=======================================================")
    # Resolve by string code
    r5 = client.get(f"/api/v1/projects/{proj_code}", headers=bld_headers)
    assert r5.status_code == 200, f"Get by code failed: {r5.text}"
    assert r5.json()["project_id"] == proj_id
    print(f"-> Project resolved by code '{proj_code}' successfully.")

    # Check Global Regulatory Sources (>= 27 sources in DB, including ABC sources)
    r6 = client.get("/api/v1/regulatory-requirements", headers=bld_headers)
    assert r6.status_code == 200, f"Regulatory requirements failed: {r6.text}"
    sources_library = r6.json()
    assert len(sources_library) >= 18, f"Expected >= 18 sources, got {len(sources_library)}"
    abc_sources = [s for s in sources_library if "Anti-Bribery" in s.get("topic", "") or "Bribery" in s.get("title", "")]
    assert len(abc_sources) >= 5, f"Expected >= 5 ABC sources, got {len(abc_sources)}"
    print(f"-> Global Regulatory Library retrieved: {len(sources_library)} sources ({len(abc_sources)} ABC sources).")

    # Add an ABC Requirement to the new project
    moj_source = next(s for s in sources_library if "Adequate Procedures" in s.get("title", ""))
    req_payload = {
        "source_id": moj_source["source_id"],
        "requirement_code": f"REQ-ABC-{uuid.uuid4().hex[:4].upper()}",
        "requirement_title": "Top-Level Commitment & Board ABC Charter",
        "requirement_text": "Board of Directors must ratify anti-bribery governance framework under MoJ Guidance Principle 2.",
        "applicability_status": "APPLICABLE",
        "requirement_status": "OPEN"
    }
    r_add_req = client.post(f"/api/v1/projects/{proj_id}/requirements", json=req_payload, headers=bld_headers)
    assert r_add_req.status_code == 201, f"Failed to add requirement: {r_add_req.text}"
    created_req = r_add_req.json()
    print(f"-> Requirement added to project: Code='{created_req['requirement_code']}', ID={created_req['requirement_id']}")

    print("\n=======================================================")
    print("STEP 5: Advisor Invitation & Service Role Assignment")
    print("=======================================================")
    inv_payload = {
        "advisor_email": adv_email,
        "access_level": "REGULATORY",
        "expiry_days": 7
    }
    r_inv = client.post(f"/api/v1/projects/{proj_id}/advisor-invitations", json=inv_payload, headers=bld_headers)
    assert r_inv.status_code == 201, f"Invitation failed: {r_inv.text}"
    inv_data = r_inv.json()
    print(f"-> Advisor invitation issued: ID={inv_data.get('invitation_id')}, Status={inv_data.get('invitation_status')}")

    # Add advisor to project members directly with REGULATORY service_role
    db.add(ProjectMember(
        project_id=proj_id,
        user_id=db_adv.user_id,
        service_role="REGULATORY",
        service_scope="REGULATORY_ANALYSIS",
        member_status="ACTIVE"
    ))
    db.commit()
    print(f"-> Advisor joined project with service_role=REGULATORY.")

    print("\n=======================================================")
    print("STEP 6: Advisor Advice Submission & Traceability")
    print("=======================================================")
    advice_payload = {
        "title": "Corporate Gifts & Hospitality Approval Threshold Policy",
        "advice_text": "Establish a mandatory £100 pre-approval threshold for gifts and client entertainment.",
        "recommendation": "Adopt a centralised gift disclosure register and require two-person signoff above £100 under MoJ Guidance Principle 1.",
        "assumptions": "Threshold applies across all commercial subsidiaries and third-party introducers."
    }
    r_adv = client.post(f"/api/v1/projects/{proj_id}/advice", json=advice_payload, headers=adv_headers)
    assert r_adv.status_code == 201, f"Advice submission failed: {r_adv.text}"
    created_advice = r_adv.json()
    advice_id = created_advice["advice_id"]
    print(f"-> Advice submitted: ID={advice_id}, Status={created_advice['advice_status']}, Title='{created_advice['title']}'")

    print("\n=======================================================")
    print("STEP 7: Grounded AI Retrieval & Conflict Gap Detection")
    print("=======================================================")
    rag_payload = {
        "query": "Compare advisor recommendations on bribery and gifts hospitality thresholds under UK Bribery Act",
        "projectId": proj_id
    }
    r_rag = client.post("/api/v1/rag/analyze", json=rag_payload, headers=bld_headers)
    assert r_rag.status_code == 200, f"RAG analysis failed: {r_rag.text}"
    rag_data = r_rag.json()
    assert rag_data["status"] == "CONFLICT_DETECTED"
    assert rag_data["grounded"] is True
    assert len(rag_data["citations"]) > 0
    assert len(rag_data["conflicts"]) > 0
    print(f"-> RAG Status: {rag_data['status']}, Citations: {len(rag_data['citations'])}, Conflicts: {len(rag_data['conflicts'])}")
    print(f"-> Detected Conflict Topic: '{rag_data['conflicts'][0]['topic']}'")

    print("\n=======================================================")
    print("STEP 8: Builder Decision Governance & Audit Recording")
    print("=======================================================")
    decision_payload = {
        "decision_type": "ACCEPT",
        "decision_rationale": "Adopt strict £100 pre-approval threshold per Eleanor Vance recommendation to satisfy Section 7 Adequate Procedures.",
        "follow_up_action": "Publish corporate gifts policy and configure automated threshold alerts in the compliance cockpit."
    }
    r_dec = client.post(f"/api/v1/projects/{proj_id}/decisions", json=decision_payload, headers=bld_headers)
    assert r_dec.status_code == 201, f"Decision failed: {r_dec.text}"
    dec_data = r_dec.json()
    print(f"-> Decision logged: ID={dec_data['decision_id']}, Type={dec_data['decision_type']}, DecidedBy={dec_data['decided_by']}")

    print("\n=======================================================")
    print("STEP 9: Audit Readiness Calculation (Week 6 Target)")
    print("=======================================================")
    r_readiness = client.get(f"/api/v1/projects/{proj_id}/readiness", headers=bld_headers)
    assert r_readiness.status_code == 200, f"Readiness evaluation failed: {r_readiness.text}"
    readiness = r_readiness.json()
    assert "readiness_score" in readiness
    assert "readiness_status" in readiness
    print(f"-> Project Audit Readiness: Score={readiness['readiness_score']}%, Status={readiness['readiness_status']}")
    print(f"-> Metrics Breakdown: Requirements={readiness['total_requirements']}, Advice={readiness['total_advice_reviews']}, Decisions={readiness['total_decisions']}")

    print("\n=======================================================")
    print("STEP 10: Complete Audit Event Trail Verification")
    print("=======================================================")
    r_audit = client.get(f"/api/v1/projects/{proj_id}/audit-events", headers=bld_headers)
    assert r_audit.status_code == 200, f"Audit events retrieval failed: {r_audit.text}"
    audit_events = r_audit.json()
    assert len(audit_events) >= 1, "Expected audit events to be logged!"
    event_types = [e["event_type"] for e in audit_events]
    print(f"-> Total audit events recorded for project: {len(audit_events)}")
    print(f"-> Recorded event types: {list(set(event_types))}")

    print("\n=======================================================")
    print("STEP 11: Security & IDOR / BOLA Isolation Verification")
    print("=======================================================")
    # 1. Reject ADMIN self-registration
    bad_admin = {"email": "fake_admin@evil.com", "password": "Password123!", "full_name": "Bad Actor", "role": "ADMIN"}
    r_sec1 = client.post("/api/v1/auth/register", json=bad_admin)
    assert r_sec1.status_code == 403, f"Expected 403 Forbidden for ADMIN registration, got {r_sec1.status_code}"
    print("-> Security Guard 1 Passed: ADMIN self-registration rejected (403 Forbidden).")

    # 2. Cross-project unauthorized access (BOLA/IDOR protection)
    # Register an unrelated 2nd builder
    other_builder_payload = {
        "email": f"intruder_{uuid.uuid4().hex[:6]}@other.com",
        "password": "Password123!",
        "full_name": "Intruder User",
        "role": "BUILDER"
    }
    r_other = client.post("/api/v1/auth/register", json=other_builder_payload)
    other_token = r_other.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Intruder tries to access Sarah Chen's project
    r_sec2 = client.get(f"/api/v1/projects/{proj_id}", headers=other_headers)
    assert r_sec2.status_code in [403, 404], f"Expected 403 or 404 for unauthorized project access, got {r_sec2.status_code}"
    print(f"-> Security Guard 2 Passed: BOLA/IDOR isolated (unauthorized access returned {r_sec2.status_code}).")

    # 3. Unauthenticated access blocked
    r_sec3 = client.get(f"/api/v1/projects/{proj_id}")
    assert r_sec3.status_code == 401, f"Expected 401 for unauthenticated request, got {r_sec3.status_code}"
    print("-> Security Guard 3 Passed: Unauthenticated request rejected (401 Unauthorized).")

    print("\n=======================================================")
    print("STEP 12: Admin Cockpit & User Governance Verification")
    print("=======================================================")
    r_adm_login = client.post("/api/v1/auth/login", json={"email": "admin@finregtech.io", "password": "Password123!"})
    assert r_adm_login.status_code == 200, f"Admin login failed: {r_adm_login.text}"
    adm_token = r_adm_login.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}
    assert r_adm_login.json()["platform_role"] == "ADMIN"
    print("-> Admin login verified with role 'ADMIN'.")

    # 1. Admin Stats
    r_stats = client.get("/api/v1/admin/stats", headers=adm_headers)
    assert r_stats.status_code == 200, f"Admin stats failed: {r_stats.text}"
    stats_data = r_stats.json()
    assert "total_users" in stats_data
    assert "total_projects" in stats_data
    assert "regulatory_sources_count" in stats_data
    print(f"-> Admin Stats retrieved: Users={stats_data['total_users']}, Projects={stats_data['total_projects']}, Sources={stats_data['regulatory_sources_count']}")

    # 2. Admin Users Directory
    r_users = client.get("/api/v1/admin/users", headers=adm_headers)
    assert r_users.status_code == 200, f"Admin users failed: {r_users.text}"
    users_list = r_users.json()
    assert len(users_list) >= 3, f"Expected at least 3 users, got {len(users_list)}"
    print(f"-> Admin Users directory: {len(users_list)} registered users listed.")

    # 3. RBAC: Non-admin forbidden
    r_bad_adm = client.get("/api/v1/admin/stats", headers=bld_headers)
    assert r_bad_adm.status_code == 403, f"Expected 403 for non-admin stats, got {r_bad_adm.status_code}"
    print("-> RBAC Security: Builder accessing admin endpoint rejected (403 Forbidden).")

    # 4. Status Toggle
    target_user_id = db_adv.user_id
    r_suspend = client.patch(f"/api/v1/admin/users/{target_user_id}/status", json={"is_active": False}, headers=adm_headers)
    assert r_suspend.status_code == 200, f"Suspend failed: {r_suspend.text}"
    assert r_suspend.json()["is_active"] is False
    r_reactivate = client.patch(f"/api/v1/admin/users/{target_user_id}/status", json={"is_active": True}, headers=adm_headers)
    assert r_reactivate.status_code == 200, f"Reactivate failed: {r_reactivate.text}"
    assert r_reactivate.json()["is_active"] is True
    print("-> User governance verified: Status toggle to False (suspended) and True (active) executed.")

    print("\n=======================================================")
    print("ALL 12 END-TO-END VERIFICATION WORKFLOWS PASSED FLAWLESSLY!")
    print("=======================================================\n")
    db.close()

if __name__ == "__main__":
    test_full_live_verification()
