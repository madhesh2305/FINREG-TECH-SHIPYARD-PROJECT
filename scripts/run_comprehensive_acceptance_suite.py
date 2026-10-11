"""
Comprehensive Acceptance Test Suite
FinRegTech ShipYard | FCC Project Cockpit
Validates Database Persistence, API Consistency, RBAC, and Route Contracts
"""
import os
import sys
import json
import datetime
import urllib.request
import urllib.error
from dotenv import load_dotenv

# Set up paths and load environment variables
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models import (
    Role, User, Project, ProjectProfile, ProjectMember,
    AdvisorProfile, AdvisorInvitation, RegulatorySource, RegulatoryRequirement,
    AuditEvent, Advice, Decision, ReadinessItem
)
import jwt

BASE_URL = "http://127.0.0.1:8000"

def log_section(title):
    print(f"\n{'='*75}\n[ACCEPTANCE SUITE] {title}\n{'='*75}")

def api_call(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return status, parsed
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

results = {
  "testDate": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "targetBackend": BASE_URL,
  "databaseEngine": engine.dialect.name,
  "databaseTarget": engine.url.database,
  "tests": {}
}

# =====================================================================
# 1. VERIFY BROWSER-REGISTERED USER IN POSTGRESQL (TEST 1 & TEST 3)
# =====================================================================
log_section("1. VERIFY BROWSER-REGISTERED USER IN POSTGRESQL")

# Read results from browser runner if available
browser_results_file = "browser_acceptance_results.json"
browser_user_email = None
if os.path.exists(browser_results_file):
    try:
        with open(browser_results_file, "r") as f:
            b_data = json.load(f)
            reg_stage = b_data.get("stages", {}).get("registration", {})
            browser_user_email = reg_stage.get("email")
    except Exception:
        pass

db = SessionLocal()
try:
    if browser_user_email:
        db_user = db.query(User).filter(User.email == browser_user_email).first()
        is_bcrypt = db_user.password_hash.startswith("$2b$") if db_user else False
        print(f"Browser-Registered User: {browser_user_email}")
        print(f"PostgreSQL Verification: ID={db_user.user_id if db_user else None}, Active={db_user.is_active if db_user else None}")
        print(f"Bcrypt Hash Confirmed ($2b$ prefix): {is_bcrypt}")
        print(f"Role ID: {db_user.role_id if db_user else None} ({db_user.role.role_name if db_user and db_user.role else 'None'})")
        
        results["tests"]["TEST-1-BROWSER-USER-DB"] = {
            "status": "PASS" if db_user and is_bcrypt and db_user.role and db_user.role.role_name == "BUILDER" else "FAIL",
            "userId": db_user.user_id if db_user else None,
            "email": browser_user_email,
            "bcryptHashed": is_bcrypt,
            "role": db_user.role.role_name if db_user and db_user.role else None
        }
    else:
        print("Warning: browser_acceptance_results.json not found or missing email.")
        results["tests"]["TEST-1-BROWSER-USER-DB"] = {"status": "BLOCKED"}
finally:
    db.close()


# =====================================================================
# 2. FULL API CONSISTENCY & WORKFLOW TRACEABILITY (TEST 2)
# =====================================================================
log_section("2. END-TO-END API CONSISTENCY & WORKFLOW TRACEABILITY (TEST 2)")

ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
builder_email = f"accept_builder_{ts}@finregtech.io"
advisor_email = f"accept_advisor_{ts}@finregtech.io"
test_password = "AcceptancePass2026!#"

# 2.1 Registration
s_reg_b, r_reg_b = api_call("POST", "/api/v1/auth/register", {
    "email": builder_email,
    "password": test_password,
    "full_name": "Acceptance Lead Builder",
    "role": "BUILDER",
    "organization": "ShipYard Audit Ltd"
})
print(f"2.1 Builder Registration: Status {s_reg_b}, UserID {r_reg_b.get('user_id')}")

# 2.2 Login
s_login_b, r_login_b = api_call("POST", "/api/v1/auth/login", {
    "email": builder_email,
    "password": test_password
})
builder_token = r_login_b.get("access_token")
print(f"2.2 Builder Login: Status {s_login_b}, Token Issued: {bool(builder_token)}")

# 2.3 Current User & Profile Update
s_me, r_me = api_call("GET", "/api/v1/users/me", token=builder_token)
print(f"2.3 GET /users/me: Status {s_me}, Platform Role: {r_me.get('platform_role')}")

s_patch_me, r_patch_me = api_call("PATCH", "/api/v1/users/me", {
    "full_name": "Acceptance Lead Builder (Senior)"
}, token=builder_token)
print(f"2.3 PATCH /users/me: Status {s_patch_me}, Updated Name: {r_patch_me.get('full_name')}")

# 2.4 Project Creation
s_proj_c, r_proj_c = api_call("POST", "/api/v1/projects", {
    "project_name": "Acceptance Cockpit ABC Shield",
    "project_code": f"PRJ-ACC-{ts[-4:]}",
    "description": "Prototype acceptance testing cockpit for UK Bribery Act 2010 Adequate Procedures.",
    "jurisdiction": "UK / England and Wales",
    "regulatory_scope": "UK Bribery Act 2010 (Section 7 Adequate Procedures)",
    "objectives": "Verify end-to-end defensible advisory governance and source-traceable compliance."
}, token=builder_token)
created_proj_id = r_proj_c.get("project_id") or r_proj_c.get("id")
created_proj_code = r_proj_c.get("project_code")
print(f"2.4 Create Project: Status {s_proj_c}, Project ID: {created_proj_id}, Code: {created_proj_code}")

# 2.5 Project List
s_proj_l, r_proj_l = api_call("GET", "/api/v1/projects", token=builder_token)
user_project_count = len(r_proj_l) if isinstance(r_proj_l, list) else 0
print(f"2.5 Project List: Status {s_proj_l}, Count for Builder: {user_project_count}")

# 2.6 Project Details (By String Code)
s_proj_d, r_proj_d = api_call("GET", f"/api/v1/projects/{created_proj_code}", token=builder_token)
print(f"2.6 Project Details (by code): Status {s_proj_d}, Resolved ID: {r_proj_d.get('project_id') or r_proj_d.get('id')}")

# 2.7 Regulatory Sources & Requirements
s_sources, r_sources = api_call("GET", "/api/v1/regulatory/sources", token=builder_token)
source_count = len(r_sources.get("sources", [])) if isinstance(r_sources, dict) else len(r_sources)
source_id = r_sources.get("sources", [{}])[0].get("source_id", 1) if isinstance(r_sources, dict) else 1
print(f"2.7 Regulatory Sources: Status {s_sources}, Total Sources: {source_count}, Using Source ID: {source_id}")

s_req_c, r_req_c = api_call("POST", f"/api/v1/projects/{created_proj_id}/requirements", {
    "source_id": source_id,
    "requirement_code": f"REQ-ACC-{ts[-4:]}",
    "requirement_title": "Proportionate Procedures for Third-Party Intermediaries",
    "requirement_text": "Establish risk-tiered due diligence workflows for commercial agents under Principle 1.",
    "applicability_status": "APPLICABLE",
    "requirement_status": "OPEN"
}, token=builder_token)
req_id = r_req_c.get("requirement_id") or r_req_c.get("id")
print(f"2.7 Create Requirement: Status {s_req_c}, Req ID: {req_id}")

# 2.8 Register Advisor & Issue Invitation
s_reg_a, r_reg_a = api_call("POST", "/api/v1/auth/register", {
    "email": advisor_email,
    "password": test_password,
    "full_name": "Acceptance Senior Advisor",
    "role": "ADVISOR",
    "organization": "FinReg Advisory LLP"
})
advisor_user_id = r_reg_a.get("user_id")
print(f"2.8 Advisor Registration: Status {s_reg_a}, UserID {advisor_user_id}")

s_login_a, r_login_a = api_call("POST", "/api/v1/auth/login", {
    "email": advisor_email,
    "password": test_password
})
advisor_token = r_login_a.get("access_token")
print(f"2.8 Advisor Login: Status {s_login_a}, Token Issued: {bool(advisor_token)}")

s_inv, r_inv = api_call("POST", f"/api/v1/projects/{created_proj_id}/advisor-invitations", {
    "advisor_email": advisor_email,
    "access_level": "REGULATORY",
    "expiry_days": 14
}, token=builder_token)
invitation_id = r_inv.get("invitation_id") or r_inv.get("id")
print(f"2.8 Advisor Invitation: Status {s_inv}, Invitation ID: {invitation_id}")

# Add advisor as active project member for advice submission
s_mem, r_mem = api_call("POST", f"/api/v1/projects/{created_proj_id}/members", {
    "user_id": advisor_user_id,
    "service_role": "REGULATORY",
    "service_scope": "UK Bribery Act 2010 Adequate Procedures Governance"
}, token=builder_token)
print(f"2.8 Project Member Provisioning: Status {s_mem}")

# 2.9 Advice Submission (by Advisor)
s_adv, r_adv = api_call("POST", f"/api/v1/projects/{created_proj_id}/advice", {
    "title": "Mandatory Senior Management Approval for High-Risk Intermediaries",
    "advice_text": "We advise instituting a strict £500 pre-approval threshold for corporate hospitality and gifts involving foreign public officials, aligned with MoJ Guidance Principle 2.",
    "recommendation": "Adopt dual-signoff policy with independent compliance register logging.",
    "assumptions": "Threshold is an internal risk appetite policy assumption, not a statutory mandate.",
    "advice_status": "SUBMITTED"
}, token=advisor_token)
advice_id = r_adv.get("advice_id") or r_adv.get("id")
print(f"2.9 Advice Submission: Status {s_adv}, Advice ID: {advice_id}")

# 2.10 Decision Recording (by Builder)
s_dec, r_dec = api_call("POST", f"/api/v1/projects/{created_proj_id}/decisions", {
    "decision_type": "ACCEPT",
    "decision_rationale": "Adopting independent dual-signoff policy to ensure full regulatory defensibility under UK Bribery Act Section 7.",
    "follow_up_action": "Configure automated gift threshold alerts in the compliance cockpit."
}, token=builder_token)
decision_id = r_dec.get("decision_id") or r_dec.get("id")
print(f"2.10 Decision Recording: Status {s_dec}, Decision ID: {decision_id}")

# 2.11 Readiness Calculation
s_readiness, r_readiness = api_call("GET", f"/api/v1/projects/{created_proj_id}/readiness", token=builder_token)
print(f"2.11 Project Readiness: Status {s_readiness}, Score: {r_readiness.get('readiness_score')}%")

# 2.12 Audit Events
s_audit, r_audit = api_call("GET", f"/api/v1/projects/{created_proj_id}/audit-events", token=builder_token)
events_count = len(r_audit) if isinstance(r_audit, list) else 0
print(f"2.12 Audit History: Status {s_audit}, Event Count: {events_count}")

# 2.13 Admin Functions
s_admin_login, r_admin_login = api_call("POST", "/api/v1/auth/login", {
    "email": "admin@finregtech.io",
    "password": "Password123!"
})
admin_token = r_admin_login.get("access_token")
s_admin_stats, r_admin_stats = api_call("GET", "/api/v1/admin/stats", token=admin_token)
s_admin_users, r_admin_users = api_call("GET", "/api/v1/admin/users", token=admin_token)
print(f"2.13 Admin Functions: Login Status {s_admin_login}, Stats Status {s_admin_stats}, Users Status {s_admin_users}")

all_api_passed = all([
    s_reg_b == 201, s_login_b == 200, s_me == 200, s_patch_me == 200,
    s_proj_c == 201, s_proj_l == 200, s_proj_d == 200, s_sources == 200,
    s_req_c == 201, s_reg_a == 201, s_login_a == 200, s_inv == 201,
    s_adv == 201, s_dec == 201, s_readiness == 200, s_audit == 200,
    s_admin_stats == 200, s_admin_users == 200
])
results["tests"]["TEST-2-API-CONSISTENCY"] = {
    "status": "PASS" if all_api_passed else "FAIL",
    "testedEndpointsCount": 16,
    "allPassed": all_api_passed
}


# =====================================================================
# 3. DIRECT DATABASE PERSISTENCE VERIFICATION (TEST 3)
# =====================================================================
log_section("3. DIRECT DATABASE PERSISTENCE VERIFICATION (TEST 3)")

db = SessionLocal()
try:
    # 3.1 Verify Builder User
    p_user = db.query(User).filter(User.email == builder_email).first()
    p_user_match = p_user and p_user.full_name == "Acceptance Lead Builder (Senior)"

    # 3.2 Verify Project & Profile
    p_proj = db.query(Project).filter(Project.project_id == created_proj_id).first()
    p_profile = db.query(ProjectProfile).filter(ProjectProfile.project_id == created_proj_id).first()
    p_proj_match = p_proj and p_proj.project_name == "Acceptance Cockpit ABC Shield" and p_proj.project_code == created_proj_code
    p_prof_match = p_profile and "UK Bribery Act 2010" in p_profile.regulatory_scope

    # 3.3 Verify Requirement
    p_req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_id == req_id).first()
    p_req_match = p_req and p_req.project_id == created_proj_id and p_req.requirement_status == "OPEN"

    # 3.4 Verify Invitation
    p_inv = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    p_inv_match = p_inv and p_inv.advisor_email == advisor_email and p_inv.project_id == created_proj_id

    # 3.5 Verify Advice
    p_adv = db.query(Advice).filter(Advice.advice_id == advice_id).first()
    p_adv_match = p_adv and p_adv.project_id == created_proj_id and p_adv.title == "Mandatory Senior Management Approval for High-Risk Intermediaries"

    # 3.6 Verify Decision
    p_dec = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    p_dec_match = p_dec and p_dec.project_id == created_proj_id and p_dec.decision_type == "ACCEPT"

    # 3.7 Verify Audit Events
    p_events = db.query(AuditEvent).filter(AuditEvent.project_id == created_proj_id).all()
    p_events_count = len(p_events)

    print(f"3.1 User Persisted: {p_user_match} (ID: {p_user.user_id if p_user else None})")
    print(f"3.2 Project Persisted: {p_proj_match} (Code: {p_proj.project_code if p_proj else None})")
    print(f"3.2 Profile Persisted: {p_prof_match} (Scope: {p_profile.regulatory_scope if p_profile else None})")
    print(f"3.3 Requirement Persisted: {p_req_match} (Code: {p_req.requirement_code if p_req else None})")
    print(f"3.4 Invitation Persisted: {p_inv_match} (Status: {p_inv.invitation_status if p_inv else None})")
    print(f"3.5 Advice Persisted: {p_adv_match} (Title: {p_adv.title if p_adv else None})")
    print(f"3.6 Decision Persisted: {p_dec_match} (Outcome: {p_dec.decision_type if p_dec else None})")
    print(f"3.7 Audit Events Persisted: {p_events_count} records")

    db_all_pass = all([p_user_match, p_proj_match, p_prof_match, p_req_match, p_inv_match, p_adv_match, p_dec_match, p_events_count >= 5])
    results["tests"]["TEST-3-DATABASE-PERSISTENCE"] = {
        "status": "PASS" if db_all_pass else "FAIL",
        "userPersisted": p_user_match,
        "projectPersisted": p_proj_match,
        "profilePersisted": p_prof_match,
        "requirementPersisted": p_req_match,
        "invitationPersisted": p_inv_match,
        "advicePersisted": p_adv_match,
        "decisionPersisted": p_dec_match,
        "auditEventsCount": p_events_count
    }
finally:
    db.close()


# =====================================================================
# 4. AUTHENTICATION & AUTHORIZATION CONTROLS (TEST 4)
# =====================================================================
log_section("4. AUTHENTICATION & AUTHORIZATION CONTROLS (TEST 4)")

# 4.1 Missing credentials
s_no_cred, _ = api_call("GET", "/api/v1/projects")

# 4.2 Malformed credentials
s_bad_cred, _ = api_call("GET", "/api/v1/projects", token="malformed_bad_jwt_token_xyz")

# 4.3 Expired credentials
expired_payload = {
    "sub": builder_email,
    "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
}
expired_jwt = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
s_exp_cred, _ = api_call("GET", "/api/v1/projects", token=expired_jwt)

# 4.4 Valid credentials for authorized project
s_valid_auth, r_valid_auth = api_call("GET", f"/api/v1/projects/{created_proj_code}", token=builder_token)

# 4.5 Cross-tenant / BOLA check: Unassigned user accessing project
# Advisor has not been added to Project 1 (PRJ-ABC-001)
s_outsider_proj, r_outsider_proj = api_call("GET", "/api/v1/projects/PRJ-ABC-001", token=advisor_token)
s_outsider_adv, r_outsider_adv = api_call("GET", "/api/v1/projects/PRJ-ABC-001/advice", token=advisor_token)

# 4.6 Non-admin accessing admin endpoints
s_builder_admin_stats, _ = api_call("GET", "/api/v1/admin/stats", token=builder_token)
s_builder_admin_users, _ = api_call("GET", "/api/v1/admin/users", token=builder_token)

print(f"4.1 Missing Credentials: HTTP {s_no_cred} (Expected 401)")
print(f"4.2 Malformed Token: HTTP {s_bad_cred} (Expected 401)")
print(f"4.3 Expired Token: HTTP {s_exp_cred} (Expected 401)")
print(f"4.4 Authorized User Access: HTTP {s_valid_auth} (Expected 200)")
print(f"4.5 Outsider Project Access: HTTP {s_outsider_proj} (Expected 403)")
print(f"4.5 Outsider Advice Access: HTTP {s_outsider_adv} (Expected 403)")
print(f"4.6 Builder Access to Admin Stats: HTTP {s_builder_admin_stats} (Expected 403)")
print(f"4.6 Builder Access to Admin Users: HTTP {s_builder_admin_users} (Expected 403)")

security_pass = all([
    s_no_cred == 401,
    s_bad_cred == 401,
    s_exp_cred == 401,
    s_valid_auth == 200,
    s_outsider_proj in (403, 404),
    s_outsider_adv in (403, 404),
    s_builder_admin_stats == 403,
    s_builder_admin_users == 403
])
results["tests"]["TEST-4-SECURITY-CONTROLS"] = {
    "status": "PASS" if security_pass else "FAIL",
    "missingCredStatus": s_no_cred,
    "malformedTokenStatus": s_bad_cred,
    "expiredTokenStatus": s_exp_cred,
    "authorizedAccessStatus": s_valid_auth,
    "outsiderProjectStatus": s_outsider_proj,
    "outsiderAdviceStatus": s_outsider_adv,
    "builderAdminAccessStatus": s_builder_admin_stats
}


# =====================================================================
# 5. ORIGINAL 404 AND ROUTE CONTRACT VERIFICATION (TEST 5)
# =====================================================================
log_section("5. ORIGINAL 404 AND ROUTE CONTRACT VERIFICATION (TEST 5)")

# 5.1 Retest GET /api/v1/projects/PRJ-ABC-001 with Jun Chen (authorized owner)
s_jun_login, r_jun_login = api_call("POST", "/api/v1/auth/login", {
    "email": "jun@finregtech.io",
    "password": "Password123!"
})
jun_token = r_jun_login.get("access_token")

s_prj_abc, r_prj_abc = api_call("GET", "/api/v1/projects/PRJ-ABC-001", token=jun_token)
p_name = r_prj_abc.get("project_name") or r_prj_abc.get("name")
print(f"5.1 GET /api/v1/projects/PRJ-ABC-001: HTTP {s_prj_abc}, Name: '{p_name}'")

# 5.2 Retest PATCH /api/v1/users/me
s_patch_jun, r_patch_jun = api_call("PATCH", "/api/v1/users/me", {
    "full_name": "Jun Chen"
}, token=jun_token)
print(f"5.2 PATCH /api/v1/users/me: HTTP {s_patch_jun}, Returned Name: '{r_patch_jun.get('full_name')}'")

# 5.3 Negative 404 Control
s_neg_404, r_neg_404 = api_call("GET", "/api/v1/nonexistent-audit-route-9999", token=jun_token)
print(f"5.3 Negative 404 Route: HTTP {s_neg_404}, Detail: {r_neg_404.get('detail') if isinstance(r_neg_404, dict) else r_neg_404}")

# 5.4 Trusted Tools Feature Inspection
results["tests"]["TEST-5-ROUTE-CONTRACT"] = {
    "status": "PASS" if s_prj_abc == 200 and s_patch_jun == 200 and s_neg_404 == 404 else "FAIL",
    "projectCodeEndpoint": s_prj_abc,
    "patchUserMeEndpoint": s_patch_jun,
    "negative404Control": s_neg_404,
    "trustedToolsArchitecture": "Curated in frontend platform catalog (TRUSTED_TOOLS in toolService.js), selections persisted in browser localStorage. No backend table /tools exists or is required by schema specification."
}

# Save complete machine-readable results
with open("backend_acceptance_results.json", "w", encoding="utf-8") as out:
    json.dump(results, out, indent=2)

print("\n[ACCEPTANCE SUITE] Complete results written to backend_acceptance_results.json")
