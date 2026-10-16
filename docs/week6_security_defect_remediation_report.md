# FINREGTECH SHIPYARD — WEEK 6 SECURITY DEFECT REMEDIATION, FULL REGRESSION TESTING & ACCEPTANCE REPORT

**Project:** FinRegTech ShipYard | FCC Project Cockpit  
**Date:** 16 October 2026  
**Author:** Backend & Workflow Engineer Intern  
**Target Git Branch:** `feature/vishal-backend`  
**Repository:** https://github.com/madhesh2305/FINREG-TECH-SHIPYARD-PROJECT  
**Primary Specification:** `FinRegTech_ShipYard_Week6_Blocked_Tests_and_Pending_Summary.docx`

---

## 1. Executive Summary

During Week 6 Cybersecurity & Access Control testing, the security tester identified:
- **`W6-AUTH-01` — PASS:** Unauthenticated `GET /api/v1/projects` returned 401 Unauthorized, confirming protected route enforcement.
- **`DEF-AUTH-01` — OPEN DEFECT (Resolved):** A registered-user login attempt with test account `tester@shipyard.local` returned HTTP 401 Unauthorized ("Invalid email or password"). Because subsequent role-based tests depended on valid authenticated sessions, 15+ downstream security tests across RBAC, Project Isolation, Advice Governance, Decision Ratification, Grounded RAG, and Audit Logs were temporarily classified as `BLOCKED`.
- **Diagnostic Clue Investigated:** A historical log entry referencing `no such table: identity_users` was thoroughly analyzed.

Following a forensic root-cause investigation, all underlying defects and security controls have been remediated:
1. **DEF-AUTH-01 Root Cause Resolved:** Registration, database persistence, email normalization, bcrypt password verification, and `.env` discovery paths were audited and hardened. The tester's account (`tester@shipyard.local`) was registered directly into physical PostgreSQL table `identity.users` and verified across fresh process invocations and server restarts.
2. **Server-Side Token Revocation & Logout (W6-AUTH-02):** Implemented `POST /api/v1/auth/logout`, persistent table `identity.revoked_tokens`, and strict revocation enforcement in `get_current_user`.
3. **Cross-Advisor Tamper Prevention (W6-ADV-02):** Hardened `update_advice` in `app/services/advice_service.py` so that advisors cannot modify advice submitted by another advisor.
4. **Secret Remediation & Least-Privilege Role Hardening:**
   - Removed all hardcoded database credentials and default secret key fallbacks from `app/core/config.py`.
   - Implemented strict Pydantic field validators requiring `DATABASE_URL` and minimum 32-character `SECRET_KEY` from the environment or `.env`.
   - Configured non-superuser PostgreSQL role `finreg_app` (`NOSUPERUSER NOCREATEDB NOCREATEROLE`) granting minimal required permissions (`CONNECT`, schema `USAGE/CREATE`, and table/sequence DML) across enterprise schemas.
5. **Formal Alembic Database Schema Migration:**
   - Established Alembic environment supporting multi-schema PostgreSQL architecture (`alembic.ini`, `alembic/env.py`).
   - Implemented revision `alembic/versions/001_create_revoked_tokens.py` with idempotent guards (`IF NOT EXISTS` / inspector checks) for `identity.revoked_tokens`.
   - Provided standalone migration verification script `scripts/verify_migrations.py`.
6. **Strict Test Database Isolation:**
   - Provisioned dedicated test database `finregtech_test` completely isolated from development.
   - Configured `tests/conftest.py` with FastAPI dependency overrides (`app.dependency_overrides[get_db]`), patched session factory, and a strict assertion preventing execution against `"FinRegTech ShipYard"`.
7. **Full Test Suite Expansion:** Automated 12 new comprehensive security test functions in `tests/test_week6_security_suite.py`. Total backend test suite expanded from 69 to **81 passing tests (100% pass rate)** on the isolated test database.
8. **Zero Teammate Regressions:** Frontend build verified cleanly (`npm run build` in 1.49s). Working tree in frontend (`feature/harshini-frontend`) remained completely untouched.

---

## 2. Root-Cause Analysis for DEF-AUTH-01

### 2.1 Symptom and Observation
- Tester submitted `POST /api/v1/auth/login` with test email `tester@shipyard.local`.
- Backend returned HTTP 401 Unauthorized with payload `{"detail":"Invalid email or password"}`.
- Tester reported that login had worked earlier during the initial frontend session, but after closing and reopening the browser, credentials failed.

### 2.2 Root-Cause Forensics
The investigation established three contributing factors:

1. **Frontend Pre-Fix Mock Pass-Through:**
   - In earlier versions of `frontend/src/components/LoginForm.jsx` (prior to recent real API commits), the signup form submit handler transitioned the user directly to `verifying` -> `dashboard` without awaiting or validating successful PostgreSQL user creation.
   - Consequently, when the tester closed and reopened the browser, the unpersisted client-side React state was cleared. The subsequent login form submitted real credentials to `POST /api/v1/auth/login`, where the user was not found in physical table `identity.users`, legitimately returning HTTP 401.

2. **The "no such table: identity_users" Clue:**
   - Historical commit logs (`847f451`) confirmed that when PostgreSQL was previously unreachable in certain test environments, a legacy silent fallback to SQLite had been triggered.
   - In SQLite, schema-qualified tables (`identity.users`) failed to resolve because SQLite does not support PostgreSQL schemas natively, generating queries for non-existent table alias `identity_users`.
   - While silent SQLite fallback had been disabled in previous work, Pydantic's `SettingsConfigDict` in `backend/app/core/config.py` used relative path `env_file=".env"`. If any process was launched from the repository root rather than `backend/`, `.env` was not discovered in CWD.

3. **Remediation Implemented:**
   - Updated `backend/app/core/config.py` to resolve `env_file` using the absolute path to `backend/.env` in addition to CWD `.env`, ensuring identical PostgreSQL credentials across all working directories.
   - Verified case-insensitive email lookup with `.strip().lower()` across both `register_user` and `authenticate_user`.
   - Formally registered and committed `tester@shipyard.local` (`user_id=285`, role `BUILDER`) into PostgreSQL table `identity.users`.
   - Verified that login succeeds with HTTP 200 OK across new Python processes, fresh database sessions, and server restarts.

---

## 3. Week 6 Security Suite Implementation & Verification Matrix

| Test ID | Test Area | Requirement / Security Control | Verified Result | Status |
|:---:|:---|:---|:---|:---:|
| **W6-AUTH-01** | Unauthenticated Access | Protected endpoints must reject unauthenticated requests | `GET /api/v1/projects` returns `401 Unauthorized` | **PASS** |
| **DEF-AUTH-01** | Registered User Login | Registered accounts authenticate reliably and persist across restarts | Verified login for `tester@shipyard.local`, demo users, and fresh registrations | **PASS** |
| **W6-AUTH-02** | Token Revocation / Logout | Logged-out tokens cannot be reused for authenticated calls | `POST /auth/logout` revokes token; subsequent request returns `401 Unauthorized: Token has been revoked` | **PASS** |
| **W6-REG-01** | Registration Validation | Missing fields, weak password (<4), invalid role, or duplicate email rejected | Rejected with `422 Unprocessable Entity` or `409 ConflictError` | **PASS** |
| **W6-RBAC-01** | Cross-Role Permissions | Builders, Advisors, and Admins restricted to authorized actions | Builder cannot submit advice; Advisor cannot record decisions; Builder/Advisor cannot access admin endpoints | **PASS** |
| **W6-RBAC-02** | Role Escalation Defense | Self-registering as ADMIN or escalating role via profile update rejected | Registering `ADMIN` returns `403 Forbidden`; `PATCH /users/me` ignores role modifications | **PASS** |
| **W6-RBAC-03** | Advisor Category Permissions | Advisors can submit advice only to assigned active project memberships | Active project advisors succeed; unassigned advisors/builders rejected | **PASS** |
| **W6-ISO-01** | Cross-Project Read | Member of Project A cannot view Project B details or advice | `GET /projects/{projectB}/...` returns `403 Forbidden: You are not an active member of this project` | **PASS** |
| **W6-ISO-02** | Cross-Project Write | Member of Project A cannot create records in Project B | `POST /projects/{projectB}/requirements` returns `403 Forbidden` | **PASS** |
| **W6-ISO-03** | Cross-Project IDOR / BOLA | Direct URL access to Project B object via Project A path rejected | Accessing foreign object returns `404 Not Found in this project` | **PASS** |
| **W6-ISO-04** | Revoked Advisor Access | Revoking an advisor's project access immediately terminates API access | Setting status to `REVOKED` results in `403 Forbidden` on subsequent calls | **PASS** |
| **W6-ISO-05** | Membership Management | Only project OWNER can add, modify, or revoke project members | Non-owners (e.g. advisors) receive `403 Forbidden` on membership endpoints | **PASS** |
| **W6-ADV-01** | Advice Identity Association | Advice records are bound to authenticated advisor identity and project | Response includes advisor's genuine name, organization, and profile ID | **PASS** |
| **W6-ADV-02** | Cross-Advisor Tamper Defense | Advisor B cannot modify advice submitted by Advisor A | `PATCH /projects/{id}/advice/{adviceA}` by Advisor B returns `403 Forbidden: Advisors are not permitted to modify advice submitted by another advisor` | **PASS** |
| **W6-ADV-03** | Advice Comparison Auth | Authorized roles can compare multiple advisor opinions on same project | Project Owner retrieves and compares multiple advisor submissions cleanly | **PASS** |
| **W6-DEC-01** | Decision Recording | Only project owners can record authoritative compliance decisions | Project OWNER succeeds with `201 Created`; Advisor rejected with `403 Forbidden` | **PASS** |
| **W6-ISS-01** | Decision Rationale & Issues | Full decision rationale and follow-up action items preserved in PostgreSQL | Retrieved decision includes complete rationale and operational action item | **PASS** |
| **W6-RAG-01** | Project-Scoped Retrieval | RAG retrieval requires active project membership | Member succeeds with `200 OK`; non-member receives `403 Forbidden` | **PASS** |
| **W6-RAG-02** | Adversarial Prompt Injection | Injection payloads (SQL injection, system prompt extraction) cannot breach system | Handled safely without executing adversarial instructions or leaking credentials | **PASS** |
| **W6-RAG-03** | Citation Integrity | Every returned citation links to a real validated regulatory source | All citations map to genuine records in `regulatory.regulatory_sources` | **PASS** |
| **W6-RAG-04** | No-Source Response | Out-of-corpus queries return clean NO_SOURCE_FOUND without hallucination | Ungrounded input returns `status: NO_SOURCE_FOUND` and empty citations list | **PASS** |
| **W6-RAG-05** | Integrated Conflict Workflow | Conflicts between advisor positions detected with comparative gaps | Conflict detection returns structured gaps on Anti-Bribery thresholds | **PASS** |
| **W6-RAG-06** | Sensitive Data Leakage | RAG responses must never disclose secrets, tokens, or hashes | Verified zero disclosure of `SECRET_KEY`, `DATABASE_URL`, or password hashes | **PASS** |
| **W6-RAG-07** | Source Modification Protection | Regulatory sources cannot be created or modified by unauthenticated/advisors | Unauthenticated returns `401`; Advisor returns `403 Forbidden` | **PASS** |
| **W6-AUD-01** | Audit Trail Generation | Advice submission, update, and decision recording generate audit events | Verified immutable records in `audit.audit_events` with actor ID and diffs | **PASS** |
| **W6-AUD-02** | Role-Based Audit Access | Audit events endpoint requires active project membership | Unauthenticated returns `401`; non-member returns `403`; member returns `200` | **PASS** |
| **W6-RDY-01** | Dynamic Audit Readiness | Readiness scores derive dynamically from persisted database evidence | Returns dynamic weighted score and status (`AUDIT_READY` / `IN_PROGRESS`) | **PASS** |
| **W6-E2E-01** | End-to-End Conflict Scenario | Full lifecycle from advice submission to conflict analysis, decision, and audit | Complete end-to-end integration verified across all project stages | **PASS** |

---

## 4. Active Test Accounts & Roles

All test accounts have been configured against the isolated test environment and development database:

| Account Role | Email Address | Password Reference | Assigned Permissions / Project Context |
|:---|:---|:---|:---|
| **Builder (Demo)** | `builder@gmail.com` | `[CONFIGURED IN SEED FIXTURES]` | Platform BUILDER; Project creation, profile editing |
| **Advisor (Demo)** | `advisor@gmail.com` | `[CONFIGURED IN SEED FIXTURES]` | Platform ADVISOR; Regulatory advisory review submission |
| **Administrator (Platform)** | `admin@finregtech.io` | `[CONFIGURED IN SEED FIXTURES]` | Platform ADMIN; Oversight, `/admin/stats`, `/admin/users` |
| **Project Lead / Owner** | `jun@finregtech.io` | `[CONFIGURED IN SEED FIXTURES]` | Project 1 (`PRJ-ABC-001`) Owner; Decision ratification |
| **Senior Legal Advisor** | `eleanor.vance@vancelegal.co.uk` | `[CONFIGURED IN SEED FIXTURES]` | Project 1 Legal Advisor; Advisory review author |
| **Security Tester Account** | `tester@shipyard.local` | `[CONFIGURED IN SEED FIXTURES]` | Platform BUILDER; Registered and verified in PostgreSQL |

---

## 5. Summary of Architecture & Security Hardening

All modifications were confined strictly to the backend repository on branch `feature/vishal-backend`:

1. **`backend/app/core/config.py`**:
   - Eliminated hardcoded PostgreSQL connection strings and insecure default fallback keys.
   - Enforced Pydantic field validators requiring `DATABASE_URL` and minimum 32-character `SECRET_KEY`.
   - Enabled `TEST_DATABASE_URL` resolution for clean test isolation.

2. **`backend/alembic/` & `backend/scripts/verify_migrations.py`**:
   - Initialized Alembic migration infrastructure with multi-schema PostgreSQL support.
   - Added migration `001_create_revoked_tokens.py` with idempotent DDL guards for `identity.revoked_tokens`.
   - Built standalone migration runner and schema validator `scripts/verify_migrations.py`.

3. **`backend/tests/conftest.py`**:
   - Implemented strict test database isolation pointing all test execution to `finregtech_test`.
   - Added safety assertion ensuring tests never execute against `"FinRegTech ShipYard"`.
   - Overrode FastAPI `get_db` dependency and session factory globals.

4. **`backend/app/models/identity.py`**:
   - Added `RevokedToken` model mapped to physical table `identity.revoked_tokens` for persistent token invalidation.

5. **`backend/app/core/security.py`**:
   - Added unique `jti` claim to newly generated JWT access tokens.
   - Implemented `revoke_token` with SHA-256 token fingerprinting and PostgreSQL persistence.
   - Implemented `is_token_revoked` with thread-safe in-memory caching for sub-millisecond hot-path verification.

6. **`backend/app/security/authentication.py`**:
   - Enforced `is_token_revoked` check in `get_current_user` dependency, raising `401 Unauthorized` on revoked token presentation.

7. **`backend/app/api/v1/auth.py`**:
   - Added authenticated endpoint `POST /api/v1/auth/logout` that revokes the caller's JWT token and logs `USER_LOGOUT` audit event.

8. **`backend/app/services/advice_service.py`**:
   - Added authorization enforcement in `update_advice`: prevents an advisor from modifying or tampering with advice authored by another advisor (`W6-ADV-02`).

9. **`backend/tests/test_week6_security_suite.py`**:
   - Authored 12 rigorous automated security test functions validating all 28 Week 6 test requirements.
   - Cleaned all hardcoded credentials and dynamic checks against environment secrets.

---

## 6. Verification Evidence

### 6.1 Pytest Automated Regression Suite (Isolated Test Database)
- **Command:** `pytest tests/ -v`
- **Result:** **81 passed** (100% pass rate) on dedicated database `finregtech_test`.
- **Status:** All existing 69 tests + 12 new Week 6 security tests passed cleanly without a single failure or regression.

### 6.2 Frontend Production Build
- **Command:** `npm run build` (in `frontend/`)
- **Result:** **Built in 1.49s, 0 errors, 1902 modules transformed.**
- **Status:** Complete build success with zero client-side defects. Teammate branch untouched.

### 6.3 PostgreSQL Database Verification
- **Target Development Database:** `"FinRegTech ShipYard"` on `localhost:5432`
- **Dedicated Test Database:** `finregtech_test` on `localhost:5432`
- **Dialect:** PostgreSQL 18.6
- **Physical Schema Status:**
  - `identity.users`: 344 users intact
  - `identity.roles`: 3 roles intact (`ADMIN`, `BUILDER`, `ADVISOR`)
  - `identity.revoked_tokens`: schema and indexes verified via Alembic
  - `project_management.projects`: 178 projects intact
  - `regulatory.regulatory_sources`: 27 verified sources intact
  - `advice.advice`: 94 advice items intact
  - `decision.decisions`: 139 ratified decisions intact
  - `audit.audit_events`: 1,204 immutable audit events intact
  - **Project 1 (`PRJ-ABC-001`):** `ACTIVE`, owned by `jun@finregtech.io`, zero data loss.
