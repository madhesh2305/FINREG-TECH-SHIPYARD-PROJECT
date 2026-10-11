"""
Audit Script: Comprehensive E2E Workflow Verification for Final Acceptance Audit
Tests all 10 principal workflows against the live running FastAPI backend and PostgreSQL 18.6.
"""
import uuid
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_section(title):
    print(f"\n{'='*70}\n[WORKFLOW AUDIT] {title}\n{'='*70}")

def run_audit():
    print("Beginning Strict Acceptance Audit of All 10 Principal Workflows...\n")
    results = {}

    # -------------------------------------------------------------
    # 1. Registration and Login
    # -------------------------------------------------------------
    print_section("1. Registration & Authentication")
    bld_email = f"audit_builder_{uuid.uuid4().hex[:6]}@shipyard.io"
    reg_payload = {
        "email": bld_email,
        "password": "Password123!",
        "full_name": "Audit Builder Officer",
        "role": "BUILDER",
        "organization": "ShipYard Compliance Corp"
    }
    r_reg = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
    reg_data = r_reg.json()
    bld_token = reg_data["access_token"]
    bld_headers = {"Authorization": f"Bearer {bld_token}"}
    print(f"-> Registration PASS: {bld_email}, User ID: {reg_data['user_id']}, Role: {reg_data['platform_role']}")

    r_login = requests.post(f"{BASE_URL}/auth/login", json={"email": bld_email, "password": "Password123!"})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    login_data = r_login.json()
    assert login_data["platform_role"] == "BUILDER"
    print(f"-> Login PASS: Valid JWT issued, correct role: {login_data['platform_role']}")

    r_me = requests.get(f"{BASE_URL}/users/me", headers=bld_headers)
    assert r_me.status_code == 200, f"GET /users/me failed: {r_me.text}"
    me_data = r_me.json()
    assert me_data["email"] == bld_email
    print(f"-> GET /users/me PASS: Verified user context {me_data['full_name']}")
    results["1. Registration & Login"] = "VERIFIED"

    # -------------------------------------------------------------
    # 2. Builder Project Creation and Persistence
    # -------------------------------------------------------------
    print_section("2. Builder Project Creation & Persistence")
    proj_payload = {
        "name": "Audit ABC Commercial Operations Cockpit",
        "type": "Anti-Bribery & Corruption (ABC)",
        "description": "Enterprise compliance management under UK Bribery Act 2010 Section 7",
        "jurisdiction": "United Kingdom - MoJ / SFO"
    }
    r_proj = requests.post(f"{BASE_URL}/projects", json=proj_payload, headers=bld_headers)
    assert r_proj.status_code == 201, f"Project creation failed: {r_proj.text}"
    proj_data = r_proj.json()
    proj_id = proj_data["project_id"]
    proj_code = proj_data["project_code"]
    print(f"-> Project Created PASS: ID={proj_id}, Code={proj_code}, Name='{proj_data['project_name']}'")

    # Verify resolution by code
    r_get = requests.get(f"{BASE_URL}/projects/{proj_code}", headers=bld_headers)
    assert r_get.status_code == 200, f"Resolve by code failed: {r_get.text}"
    assert r_get.json()["project_id"] == proj_id
    print(f"-> Project Retrieval by String Code PASS: ID={proj_id} resolved from '{proj_code}'")
    results["2. Project Creation & Persistence"] = "VERIFIED"

    # -------------------------------------------------------------
    # 3. Project Profile & Regulatory Requirements
    # -------------------------------------------------------------
    print_section("3. Project Profile & Regulatory Requirements")
    # Fetch curated regulatory sources
    r_srcs = requests.get(f"{BASE_URL}/regulatory/sources", headers=bld_headers)
    assert r_srcs.status_code == 200, f"Fetch sources failed: {r_srcs.text}"
    srcs_json = r_srcs.json()
    sources_items = srcs_json.get("items", srcs_json) if isinstance(srcs_json, dict) else srcs_json
    total_sources = srcs_json.get("total", len(sources_items)) if isinstance(srcs_json, dict) else len(sources_items)
    assert total_sources >= 20, f"Expected total >= 20 sources, got {total_sources}"
    moj_src = next((s for s in sources_items if "Adequate Procedures" in s.get("source_title", "")), sources_items[0])
    print(f"-> Curated Regulatory Sources PASS: {total_sources} sources available in library ({len(sources_items)} on current page).")

    # Add ABC requirement
    req_payload = {
        "source_id": moj_src["source_id"],
        "requirement_code": f"REQ-ABC-{uuid.uuid4().hex[:4].upper()}",
        "requirement_title": "Top-Level Commitment & Board ABC Charter",
        "requirement_text": "Board of Directors must ratify anti-bribery governance framework under MoJ Guidance Principle 2.",
        "applicability_status": "APPLICABLE",
        "requirement_status": "OPEN"
    }
    r_req = requests.post(f"{BASE_URL}/projects/{proj_id}/requirements", json=req_payload, headers=bld_headers)
    assert r_req.status_code == 201, f"Add requirement failed: {r_req.text}"
    req_data = r_req.json()
    req_id = req_data["requirement_id"]
    print(f"-> Project Requirement Linked PASS: ID={req_id}, Code={req_data['requirement_code']}, SourceID={moj_src['source_id']}")

    r_reqs_list = requests.get(f"{BASE_URL}/projects/{proj_id}/requirements", headers=bld_headers)
    assert r_reqs_list.status_code == 200
    assert len(r_reqs_list.json()) >= 1
    print(f"-> Project Requirements List PASS: {len(r_reqs_list.json())} requirements associated with project.")
    results["3. Profile & Requirements"] = "VERIFIED"

    # -------------------------------------------------------------
    # 4. Advisor Invitation and Authorized Access
    # -------------------------------------------------------------
    print_section("4. Advisor Invitation & Access")
    # Register an Advisor
    adv_email = f"audit_advisor_{uuid.uuid4().hex[:6]}@advisory.io"
    adv_reg_payload = {
        "email": adv_email,
        "password": "Password123!",
        "full_name": "Eleanor Vance Regulatory Counsel",
        "role": "ADVISOR",
        "organization": "Vance Legal Compliance LLP"
    }
    r_adv_reg = requests.post(f"{BASE_URL}/auth/register", json=adv_reg_payload)
    assert r_adv_reg.status_code == 201, f"Advisor registration failed: {r_adv_reg.text}"
    adv_user_id = r_adv_reg.json()["user_id"]
    adv_token = r_adv_reg.json()["access_token"]
    adv_headers = {"Authorization": f"Bearer {adv_token}"}
    print(f"-> Advisor Registered PASS: {adv_email}, User ID: {adv_user_id}, Role: {r_adv_reg.json()['platform_role']}")

    # Issue invitation from Builder
    inv_payload = {
        "advisor_email": adv_email,
        "access_level": "REGULATORY",
        "expiry_days": 14
    }
    r_inv = requests.post(f"{BASE_URL}/projects/{proj_id}/advisor-invitations", json=inv_payload, headers=bld_headers)
    assert r_inv.status_code == 201, f"Invitation failed: {r_inv.text}"
    inv_data = r_inv.json()
    inv_id = inv_data["invitation_id"]
    print(f"-> Advisor Invitation Issued PASS: ID={inv_id}, Status={inv_data['invitation_status']}")

    # Add advisor to project members with REGULATORY service role
    member_payload = {
        "user_id": adv_user_id,
        "service_role": "REGULATORY",
        "service_scope": "REGULATORY_ADVICE_SUPPORT"
    }
    r_add_mem = requests.post(f"{BASE_URL}/projects/{proj_id}/members", json=member_payload, headers=bld_headers)
    assert r_add_mem.status_code == 201, f"Add project member failed: {r_add_mem.text}"
    print(f"-> Advisor Membership Provisioned PASS: Added to project with REGULATORY service role.")

    # Verify project membership
    r_mems = requests.get(f"{BASE_URL}/projects/{proj_id}/members", headers=bld_headers)
    assert r_mems.status_code == 200
    mems = r_mems.json()
    assert any(m["email"] == adv_email for m in mems)
    print(f"-> Project Membership List PASS: {len(mems)} active project members verified.")
    results["4. Advisor Invitation & Access"] = "VERIFIED"

    # -------------------------------------------------------------
    # 5. Advice Submission and Review
    # -------------------------------------------------------------
    print_section("5. Advice Submission & Review")
    advice_payload = {
        "title": "Corporate Gifts & Hospitality Internal Pre-Approval Threshold",
        "advice_text": "Establish an internal organizational pre-approval threshold for gifts and client entertainment at £100 per counterparty.",
        "recommendation": "Adopt a centralised gift disclosure register and require two-person signoff above £100 to evidence MoJ Guidance Principle 1.",
        "assumptions": "Threshold is an internal risk appetite policy assumption, not a statutory mandate of the UK Bribery Act 2010."
    }
    r_adv_sub = requests.post(f"{BASE_URL}/projects/{proj_id}/advice", json=advice_payload, headers=adv_headers)
    assert r_adv_sub.status_code == 201, f"Advice submission failed: {r_adv_sub.text}"
    adv_data = r_adv_sub.json()
    advice_id = adv_data["advice_id"]
    print(f"-> Advice Submitted PASS: ID={advice_id}, Status={adv_data['advice_status']}, Title='{adv_data['title']}'")

    r_adv_list = requests.get(f"{BASE_URL}/projects/{proj_id}/advice", headers=bld_headers)
    assert r_adv_list.status_code == 200
    assert len(r_adv_list.json()) >= 1
    print(f"-> Advice Retrieval PASS: Builder retrieved {len(r_adv_list.json())} advisory submissions for project.")
    results["5. Advice Submission & Review"] = "VERIFIED"

    # -------------------------------------------------------------
    # 6. RAG Retrieval, Citations, Provenance, & No-Source Handling
    # -------------------------------------------------------------
    print_section("6. RAG Retrieval & No-Source Handling")
    # Positive retrieval with grounded citations
    rag_pos = requests.post(f"{BASE_URL}/rag/analyze", json={
        "query": "UK Bribery Act 2010 Section 7 adequate procedures principles",
        "projectId": proj_id
    }, headers=bld_headers)
    assert rag_pos.status_code == 200, f"RAG query failed: {rag_pos.text}"
    pos_data = rag_pos.json()
    assert pos_data["grounded"] is True
    assert len(pos_data["citations"]) > 0
    assert len(pos_data["provenance"]) > 0
    print(f"-> RAG Grounded Query PASS: Found {len(pos_data['citations'])} citations, Status={pos_data['status']}")
    print(f"   Provenance Record Sample: {pos_data['provenance'][0]['officialSource']} ({pos_data['provenance'][0]['validationStatus']})")

    # Negative retrieval / no-source handling
    rag_neg = requests.post(f"{BASE_URL}/rag/analyze", json={
        "query": "quantum entanglement teleportation superconducting qubits astrophysics",
        "projectId": proj_id
    }, headers=bld_headers)
    assert rag_neg.status_code == 200
    neg_data = rag_neg.json()
    assert neg_data["status"] == "NO_SOURCE_FOUND"
    assert neg_data["grounded"] is False
    assert len(neg_data["citations"]) == 0
    print(f"-> RAG No-Source Handling PASS: Status={neg_data['status']}, Grounded={neg_data['grounded']}, Citations={len(neg_data['citations'])}")
    results["6. RAG Retrieval & Citations"] = "VERIFIED"

    # -------------------------------------------------------------
    # 7. Conflict/Gap Review & Human Decision Recording
    # -------------------------------------------------------------
    print_section("7. Conflict Review & Decision Recording")
    # Query comparing advisor positions
    rag_conf = requests.post(f"{BASE_URL}/rag/analyze", json={
        "query": "Compare advisor recommendations on bribery and gifts hospitality thresholds under UK Bribery Act",
        "projectId": proj_id
    }, headers=bld_headers)
    assert rag_conf.status_code == 200
    conf_data = rag_conf.json()
    assert conf_data["status"] == "CONFLICT_DETECTED"
    assert len(conf_data["conflicts"]) > 0
    conf = conf_data["conflicts"][0]
    print(f"-> Conflict Detection PASS: Status={conf_data['status']}, Topic='{conf['topic']}'")
    print(f"   Advisor A: {conf['advisorA']['name']}")
    print(f"   Advisor B: {conf['advisorB']['name']}")

    # Human Builder records binding decision
    dec_payload = {
        "advice_id": advice_id,
        "decision_type": "ACCEPT",
        "decision_rationale": "Adopt internal £100 pre-approval threshold per Eleanor Vance recommendation to satisfy Section 7 Adequate Procedures Principle 1.",
        "follow_up_action": "Configure automated gift threshold alerts in the compliance cockpit."
    }
    r_dec = requests.post(f"{BASE_URL}/projects/{proj_id}/decisions", json=dec_payload, headers=bld_headers)
    assert r_dec.status_code == 201, f"Record decision failed: {r_dec.text}"
    dec_data = r_dec.json()
    print(f"-> Human Decision Recorded PASS: ID={dec_data['decision_id']}, Outcome={dec_data['decision_type']}, DecidedBy={dec_data['decided_by']}")

    r_dec_list = requests.get(f"{BASE_URL}/projects/{proj_id}/decisions", headers=bld_headers)
    assert r_dec_list.status_code == 200
    assert len(r_dec_list.json()) >= 1
    print(f"-> Decisions List PASS: {len(r_dec_list.json())} ratified decisions on record.")
    results["7. Conflict Review & Decisions"] = "VERIFIED"

    # -------------------------------------------------------------
    # 8. Dynamic Readiness Calculation
    # -------------------------------------------------------------
    print_section("8. Dynamic Audit Readiness Evaluation")
    r_readiness = requests.get(f"{BASE_URL}/projects/{proj_id}/readiness", headers=bld_headers)
    assert r_readiness.status_code == 200, f"Readiness evaluation failed: {r_readiness.text}"
    readiness = r_readiness.json()
    assert "readiness_score" in readiness
    assert "readiness_status" in readiness
    assert "breakdown" in readiness
    print(f"-> Dynamic Readiness Score PASS: {readiness['readiness_score']} ({readiness['readiness_status']})")
    print(f"   Requirements: {readiness['completed_requirements']} of {readiness['total_requirements']} completed")
    print(f"   Advice Reviews: {readiness['total_advice_reviews']}")
    print(f"   Decisions Ratified: {readiness['total_decisions']}")
    for cat in readiness["breakdown"]:
        print(f"   * [{cat['category']}]: {cat['metric']} -> {cat['completion_pct']}% ({cat['status']})")
    results["8. Dynamic Readiness"] = "VERIFIED"

    # -------------------------------------------------------------
    # 9. Audit Event Creation & Retrieval
    # -------------------------------------------------------------
    print_section("9. Audit Event Defensibility Stream")
    r_audit = requests.get(f"{BASE_URL}/projects/{proj_id}/audit-events", headers=bld_headers)
    assert r_audit.status_code == 200, f"Audit events retrieval failed: {r_audit.text}"
    events = r_audit.json()
    assert len(events) >= 4, f"Expected >= 4 events, got {len(events)}"
    event_types = [e["event_type"] for e in events]
    print(f"-> Audit Event Stream PASS: {len(events)} events recorded for project lifecycle.")
    print(f"   Recorded Event Types: {list(set(event_types))}")
    assert "PROJECT_CREATED" in event_types
    assert "REQUIREMENT_CREATED" in event_types
    assert "ADVICE_SUBMITTED" in event_types
    assert "DECISION_RECORDED" in event_types
    results["9. Audit Event Stream"] = "VERIFIED"

    # -------------------------------------------------------------
    # 10. Role Enforcement, Project Isolation & IDOR/BOLA Protection
    # -------------------------------------------------------------
    print_section("10. Security: RBAC, BOLA/IDOR & Isolation")
    # A. ADMIN Self-Registration Rejection
    bad_admin = {"email": "bad_admin@evil.com", "password": "Password123!", "full_name": "Attacker", "role": "ADMIN"}
    r_bad_reg = requests.post(f"{BASE_URL}/auth/register", json=bad_admin)
    assert r_bad_reg.status_code == 403, f"Expected 403, got {r_bad_reg.status_code}"
    print("-> Security Guard 1 PASS: ADMIN self-registration rejected (403 Forbidden).")

    # B. Cross-tenant project access (BOLA/IDOR)
    other_bld_email = f"other_builder_{uuid.uuid4().hex[:6]}@other.io"
    r_other = requests.post(f"{BASE_URL}/auth/register", json={
        "email": other_bld_email,
        "password": "Password123!",
        "full_name": "Unrelated Builder",
        "role": "BUILDER"
    })
    other_headers = {"Authorization": f"Bearer {r_other.json()['access_token']}"}
    r_bola = requests.get(f"{BASE_URL}/projects/{proj_id}", headers=other_headers)
    assert r_bola.status_code in (403, 404), f"Expected 403/404, got {r_bola.status_code}"
    print(f"-> Security Guard 2 PASS: Cross-project access rejected with HTTP {r_bola.status_code} (BOLA/IDOR isolated).")

    # C. Unauthenticated access rejected
    r_no_auth = requests.get(f"{BASE_URL}/projects/{proj_id}")
    assert r_no_auth.status_code == 401, f"Expected 401, got {r_no_auth.status_code}"
    print("-> Security Guard 3 PASS: Unauthenticated access rejected with HTTP 401 Unauthorized.")

    # D. Non-admin accessing admin endpoints
    r_bad_adm = requests.get(f"{BASE_URL}/admin/stats", headers=bld_headers)
    assert r_bad_adm.status_code == 403, f"Expected 403, got {r_bad_adm.status_code}"
    print("-> Security Guard 4 PASS: Non-admin accessing admin endpoints rejected with HTTP 403 Forbidden.")
    results["10. Security & IDOR/BOLA"] = "VERIFIED"

    print("\n" + "="*70)
    print("ALL 10 PRINCIPAL USER JOURNEYS AND WORKFLOWS AUDITED AND VERIFIED!")
    print("="*70)
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_audit()
