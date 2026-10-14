# COMPREHENSIVE REGRESSION TEST RESULTS & VERIFICATION LOG
## FinRegTech ShipYard | FCC Project Cockpit
**Application:** ABC Shield Prototype
**Test Run Timestamp:** October 14, 2026, 20:35 UTC+05:30
**Test Scope:** 100% Backend Pytest Suite, Database Integrity Audit, Frontend Production Build & Headless Chrome CDP Acceptance Audit
**Overall Verdict:** 100% PASS (Zero Failures, Zero Regressions)

---

### 1. Pytest Backend Test Suite Execution

```
Command: pytest tests/ -v
Runtime: Python 3.12.0 / pytest-9.1.1
Execution Time: 23.27s
Dialect: PostgreSQL 16 (Strict Production Mode)
Result: 69 PASSED, 0 FAILED, 0 SKIPPED (100% Pass Rate)
```

#### Module-by-Module Test Breakdown

| Test File | Test Function | Result | Execution Details |
|:---|:---|:---:|:---|
| `tests/test_admin.py` | `test_admin_stats_authorized` | **PASSED** | Admin retrieves platform-wide system counts |
| `tests/test_admin.py` | `test_admin_users_list` | **PASSED** | Admin retrieves paginated platform identity users |
| `tests/test_admin.py` | `test_admin_toggle_user_status` | **PASSED** | Admin activates/deactivates user with audit logging |
| `tests/test_admin.py` | `test_admin_endpoints_reject_builder` | **PASSED** | Enforces 403 Forbidden for non-admin accounts |
| `tests/test_admin.py` | `test_admin_endpoints_reject_unauthenticated` | **PASSED** | Enforces 401 Unauthorized for missing tokens |
| `tests/test_advice.py` | `test_submit_advice_success` | **PASSED** | Submits review; persists to `advice.advice` (201 Created) |
| `tests/test_advice.py` | `test_list_and_filter_project_advice` | **PASSED** | Filters advice by `status` (DRAFT, SUBMITTED) |
| `tests/test_advice.py` | `test_patch_advice_status` | **PASSED** | Transitions advice status with role authorization |
| `tests/test_advice.py` | `test_outsider_cannot_access_advice` | **PASSED** | BOLA defense: blocks users lacking project membership |
| `tests/test_advice.py` | `test_advice_bola_protection` | **PASSED** | Prevents accessing advice IDs across tenant projects |
| `tests/test_advisors.py` | `test_list_advisors` | **PASSED** | Lists accredited regulatory advisors from `advisor_profiles` |
| `tests/test_advisors.py` | `test_get_advisor_by_id` | **PASSED** | Retrieves single advisor profile with credentials |
| `tests/test_advisors.py` | `test_advisor_invitation_lifecycle` | **PASSED** | Issues invitation, accepts invitation, creates membership |
| `tests/test_ai_and_audit.py` | `test_ai_grounded_retrieval_success` | **PASSED** | RAG retrieval against curated UK rulebooks |
| `tests/test_ai_and_audit.py` | `test_ai_grounded_retrieval_no_match` | **PASSED** | Grounded fallback for out-of-scope regulatory queries |
| `tests/test_ai_and_audit.py` | `test_audit_events_retrieval` | **PASSED** | Queries immutable audit events by project ID |
| `tests/test_ai_and_audit.py` | `test_rag_analyze_conflict` | **PASSED** | Evaluates compliance conflicts against statutory rules |
| `tests/test_ai_and_audit.py` | `test_project_readiness_calculation` | **PASSED** | Computes mathematical audit readiness percentage |
| `tests/test_ai_and_audit.py` | `test_project_access_by_code` | **PASSED** | Resolves `PRJ-ABC-001` code to Project ID 1 |
| `tests/test_auth.py` | `test_login_success` | **PASSED** | Validates bcrypt hash and returns signed JWT bearer |
| `tests/test_auth.py` | `test_login_invalid_password` | **PASSED** | Rejects invalid password with 401 Unauthorized |
| `tests/test_auth.py` | `test_login_nonexistent_user` | **PASSED** | Rejects non-existent email with 401 Unauthorized |
| `tests/test_auth.py` | `test_get_current_user_me` | **PASSED** | Returns authenticated user profile from token |
| `tests/test_auth.py` | `test_get_current_user_no_token` | **PASSED** | Rejects unauthenticated request with 401 Unauthorized |
| `tests/test_auth.py` | `test_get_current_user_invalid_token` | **PASSED** | Rejects malformed JWT token with 401 Unauthorized |
| `tests/test_auth.py` | `test_inactive_user_cannot_login` | **PASSED** | Rejects deactivated accounts with 403 Forbidden |
| `tests/test_auth.py` | `test_patch_current_user_me` | **PASSED** | Updates full name and preferences |
| `tests/test_auth.py` | `test_change_password_endpoint` | **PASSED** | Verifies current password, updates bcrypt hash (200 OK) |
| `tests/test_auth.py` | `test_password_reset_request_truthful_response` | **PASSED** | Anti-enumeration check reporting truthful transport |
| `tests/test_auth.py` | `test_get_user_notifications` | **PASSED** | Returns live invitations and member project audit events |
| `tests/test_decisions.py` | `test_record_decision_success` | **PASSED** | Ratifies builder governance decision in `decision.decisions` |
| `tests/test_decisions.py` | `test_list_and_get_decisions` | **PASSED** | Lists decisions with requirement traceability |
| `tests/test_decisions.py` | `test_invalid_decision_type` | **PASSED** | Enforces valid decision enum (ACCEPT, REJECT, DEFER) |
| `tests/test_decisions.py` | `test_advisor_cannot_record_decision` | **PASSED** | Enforces separation of duties (advisors cannot ratify) |
| `tests/test_decisions.py` | `test_outsider_cannot_access_decisions` | **PASSED** | Blocks non-member access to project decisions |
| `tests/test_decisions.py` | `test_decision_creates_audit_log` | **PASSED** | Creates audit event for ratified compliance decision |
| `tests/test_members.py` | `test_list_project_members` | **PASSED** | Lists active project team members |
| `tests/test_members.py` | `test_add_and_update_member` | **PASSED** | Adds new project member with service role |
| `tests/test_members.py` | `test_outsider_cannot_manage_members` | **PASSED** | Enforces OWNER role for project roster changes |
| `tests/test_members.py` | `test_sole_owner_cannot_be_revoked` | **PASSED** | Preserves project ownership invariant |
| `tests/test_postgresql_persistence.py` | `test_db_dialect_is_strictly_postgresql` | **PASSED** | Verifies active dialect is PostgreSQL, not SQLite |
| `tests/test_postgresql_persistence.py` | `test_registration_persists_bcrypt_hash` | **PASSED** | Verifies persistent bcrypt hash in `identity.users` |
| `tests/test_postgresql_persistence.py` | `test_duplicate_registration_rejected` | **PASSED** | Enforces unique email constraint (409 Conflict) |
| `tests/test_postgresql_persistence.py` | `test_login_validates_persisted_hash` | **PASSED** | Authenticates against physical PostgreSQL database |
| `tests/test_postgresql_persistence.py` | `test_project_lifecycle_writes_to_postgresql` | **PASSED** | Creates project, profile, members, reqs in PostgreSQL |
| `tests/test_postgresql_persistence.py` | `test_project_isolation_bola_defense` | **PASSED** | Proves project isolation across distinct tenants |
| `tests/test_projects.py` | `test_list_projects` | **PASSED** | Returns projects user is member of |
| `tests/test_projects.py` | `test_create_project` | **PASSED** | Creates new project with default OWNER membership |
| `tests/test_projects.py` | `test_get_project_details` | **PASSED** | Returns project profile and metadata |
| `tests/test_projects.py` | `test_patch_project_details` | **PASSED** | Updates project profile and objective text |
| `tests/test_projects.py` | `test_dashboard_summary` | **PASSED** | Aggregates project cockpit counts and status |
| `tests/test_projects.py` | `test_outsider_cannot_access_project` | **PASSED** | Blocks unassigned users with 403 Forbidden |
| `tests/test_register.py` | `test_register_builder_success` | **PASSED** | Registers BUILDER user in PostgreSQL (201 Created) |
| `tests/test_register.py` | `test_register_advisor_success` | **PASSED** | Registers ADVISOR user with `AdvisorProfile` |
| `tests/test_register.py` | `test_register_duplicate_email` | **PASSED** | Rejects duplicate email address |
| `tests/test_register.py` | `test_register_invalid_role` | **PASSED** | Rejects unrecognized platform role names |
| `tests/test_register.py` | `test_login_with_demo_credentials` | **PASSED** | Authenticates seeded demo accounts |
| `tests/test_register.py` | `test_register_admin_forbidden` | **PASSED** | Forbids self-registration as ADMIN (403 Forbidden) |
| `tests/test_regulatory.py` | `test_list_regulatory_sources` | **PASSED** | Lists authoritative UK rulebooks (FCA, MLR, JMLSG) |
| `tests/test_regulatory.py` | `test_filter_regulatory_sources` | **PASSED** | Filters rulebooks by authority and topic |
| `tests/test_regulatory.py` | `test_get_regulatory_source_by_id` | **PASSED** | Retrieves single rulebook with statutory citations |
| `tests/test_regulatory.py` | `test_list_project_requirements` | **PASSED** | Lists requirements mapped to Project 1 |
| `tests/test_regulatory.py` | `test_create_and_patch_requirement` | **PASSED** | Creates and updates requirement validation status |
| `tests/test_regulatory.py` | `test_provenance_validation_rejects_unapproved_source` | **PASSED** | Rejects requirement with invalid source ID (422) |
| `tests/test_security_negative.py` | `test_outsider_cannot_access_project_endpoints` | **PASSED** | Comprehensive BOLA defense across 8 endpoints |
| `tests/test_security_negative.py` | `test_platform_admin_cannot_bypass_project_isolation` | **PASSED** | Proves Admin cannot access project without membership |
| `tests/test_security_negative.py` | `test_nested_object_bola_idor_defense` | **PASSED** | Prevents IDOR access to cross-project nested objects |
| `tests/test_security_negative.py` | `test_advisor_cannot_be_assigned_owner_role` | **PASSED** | Enforces regulatory separation of duties |
| `tests/test_verify_live.py` | `test_full_live_verification` | **PASSED** | Complete end-to-end multi-user platform lifecycle |

---

### 2. Frontend Production Build Audit

```
Command: npm run build
Bundler: Vite 8.3.0
Output Directory: dist/
Modules Transformed: 1902 modules
Build Duration: 874ms
Exit Code: 0 (Zero errors, Zero TypeScript/JSX syntax faults)
```

Assets generated:
- `dist/index.html`: 1.03 kB (gzip: 0.55 kB)
- `dist/assets/index-C45d9ga1.css`: 86.33 kB (gzip: 13.02 kB)
- `dist/assets/index-C8CsH4_H.js`: 482.34 kB (gzip: 115.45 kB)

---

### 3. Database Integrity & Taxonomy Audit Results

```
Command: python scripts/audit_database_integrity.py
Target Database: PostgreSQL 16 ("FinRegTech ShipYard")
Dialect: postgresql+psycopg2
Audit Timestamp: 2026-10-14 20:35 UTC+05:30
Result: 100% HEALTHY, ZERO CORRUPTION, ZERO ORPHANS
```

- **Project 1 Invariant (ABC Shield):**
  - Project ID: `1`
  - Project Code: `PRJ-ABC-001`
  - Status: `ACTIVE`
  - Associated Members: `8`
  - Regulatory Requirements: `54`
  - Advisory Reviews: `39`
  - Ratified Decisions: `73`
- **Referential Integrity:**
  - Orphaned Project Members: `0`
  - Orphaned Regulatory Requirements: `0`
  - Orphaned Advisory Reviews: `0`
  - Orphaned Decisions: `0`
  - True Orphaned Audit Events: `0`
- **Regulatory Curated Sources:**
  - 27 out of 27 rulebooks verified valid and source-grounded.

---

### 4. Headless Chrome Acceptance Audit Results (CDP)

```
Test Script: backend/scripts/verify_13_defects_e2e.js
Browser: Chrome 155.0.8059.40 (Native Headless)
Frontend Origin: http://127.0.0.1:5173
Backend Origin: http://127.0.0.1:8000
Audit Timestamp: 2026-10-14 20:34 UTC+05:30
```

```
======================================================
FINAL DEFECT ACCEPTANCE AUDIT: 13/13 DEFECTS VERIFIED FIXED
======================================================
- DEF-01: PASS (Advisor Registration Routes to Advisor Dashboard)
- DEF-02: PASS (Password Reset Truthful Messaging)
- DEF-03: PASS (Dynamic User Greeting)
- DEF-04: PASS (Settings Role Field Locked Under Administrator RBAC)
- DEF-05: PASS (Notification Bell Live Data & Clean Empty State)
- DEF-06: PASS (Tools View Details Enabled for Approved Tools)
- DEF-07: PASS (Login Authenticates Registered Users Without Mock Rejection)
- DEF-08: PASS (Advisor View Status Opens Full Details Modal)
- DEF-09: PASS (Advisor Review Button Navigates to Review Tab)
- DEF-10: PASS (Assigned Projects Open Navigates to Requirements)
- DEF-11: PASS (Dynamic Status Update upon Advice Submission)
- DEF-12: PASS (Database Persistence on Registration)
- DEF-13: PASS (New Registered Users Persisted to PostgreSQL)
======================================================
```
