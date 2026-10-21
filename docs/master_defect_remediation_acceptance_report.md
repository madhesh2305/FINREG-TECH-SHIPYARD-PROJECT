# FINREGTECH SHIPYARD — MASTER DEFECT REMEDIATION & SECURITY ACCEPTANCE REPORT

**Project:** FinRegTech ShipYard — FCC Project Cockpit  
**Target Repository:** `https://github.com/madhesh2305/FINREG-TECH-SHIPYARD-PROJECT`  
**Backend Branch:** `feature/vishal-backend`  
**Frontend Branch:** `feature/vishal-frontend`  
**Engineer:** Backend & Workflow Engineer Intern (Vishal)  
**Audit Date:** 2026-10-21  
**Test Database:** `finregtech_test` (PostgreSQL on localhost:5432)  
**Primary Database Status:** `"FinRegTech ShipYard"` strictly preserved and untouched  
**Backend Pytest Suite:** 106 passed, 0 failed in 34.15s  
**Defect Suite (`test_master_defect_remediation.py`):** 19 passed, 0 failed in 9.64s  
**Frontend Build Status:** Vite production build succeeded with 0 errors in 1.41s  
**Evidence Model:** Dual-layer classification distinguishing automated API/DB test evidence from browser/UI execution.  

---

## 1. Executive Summary & Audit Methodology

This report establishes the verified state of all 14 official defect specifications across two authoritative reports:
1. `FinRegTech_ShipYard_Defect_Report_Removed_DEF04_DEF08_DEF09_Added_Project_Isolation.docx` (DEF-01, 02, 03, 05, 06, 07, 10, 11, 12, 13)
2. `FinRegTech_ShipYard_Authentication_Password_Reset_File_Upload_Admin_Defect_Report.docx` (DEF-14, 15, 16, 17)

### Audit & Evidence Distinction Standard
In strict compliance with engineering governance:
- **API & Database Persistence Evidence:** Verified via automated regression suites executing against live PostgreSQL (`finregtech_test`). Status marked **PASS**.
- **Browser & UI Interaction Evidence:** In the absence of an in-repo browser automation framework (such as Playwright or Cypress), automated FastAPI `TestClient` tests do not constitute proof of browser rendering. Therefore, user interface behaviors are formally classified as **NOT VERIFIED** until manual tester walkthroughs or CDP-driven browser test scripts are executed. Full, reproducible manual testing protocols are provided for every defect.
- **Allowed Statuses:** `PASS`, `FAIL`, `BLOCKED`, `NOT VERIFIED`.

---

## 2. Master 14-Defect Evidence & Acceptance Matrix

| Defect ID | Technical Remediation Applied | Files Changed | Automated API / Database Evidence | Automated Test Name | API Status | Browser / UI Status | Explicit Manual Verification Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | Removed automatic assignment of new advisors to Project 1. Workspace queries assignments strictly from authorized mapping table. | `backend/app/services/auth_service.py`<br>`frontend/src/components/AdvisorDashboardView.jsx` | `GET /api/v1/projects` returns empty array `[]` for new advisor until invited and accepted via `/advisor-invitations/{id}/accept`. | `test_def01_advisor_empty_project_assignments_by_default` | **PASS** | **NOT VERIFIED** | 1. Register new advisor in UI.<br>2. Log in and verify 0 projects in workspace table.<br>3. In Builder session, invite advisor to Project 1.<br>4. Accept invitation in Advisor workspace; confirm project appears immediately. |
| **DEF-02** | Cleared stale login error states and banners upon role toggle or retry. Added unmounting guards in advisor workspace. | `frontend/src/components/LoginForm.jsx`<br>`frontend/src/components/AdvisorDashboardView.jsx` | `POST /api/v1/auth/login` returns HTTP 200 with `platform_role="ADVISOR"`; error banner unmounts cleanly without stale error modals. | `test_def02_advisor_login_clean_tokens_and_roles` | **PASS** | **NOT VERIFIED** | 1. Enter incorrect password; observe red validation alert.<br>2. Enter correct credentials; verify dashboard mounts with zero contradictory error popups.<br>3. Simulate network disconnection on secondary request; verify in-widget notice appears truthfully. |
| **DEF-03** | Replaced static metrics with independent live data queries. Added separate loading, error, and empty states with per-widget retry buttons. | `backend/app/api/v1/admin.py`<br>`frontend/src/components/AdminDashboardView.jsx` | `GET /api/v1/admin/stats`, `GET /api/v1/admin/users`, `GET /api/v1/admin/audit-events` query live PostgreSQL tables. | `test_def03_admin_dashboard_live_postgresql_data` | **PASS** | **NOT VERIFIED** | 1. Log in as admin; verify live user count and audit log widgets render.<br>2. Disconnect network; verify each widget renders independent retry button.<br>3. Reconnect and click retry; verify widget recovers live state. |
| **DEF-05** | Enforced explicit `db.commit()` and `db.refresh()` on registration service so user records persist authoritatively in PostgreSQL. | `backend/app/services/auth_service.py`<br>`frontend/src/services/authService.js` | Direct PostgreSQL query `SELECT * FROM identity.users WHERE email = :email` confirms row is present immediately after registration. | `test_def05_registered_users_authoritative_persistence_in_db` | **PASS** | **NOT VERIFIED** | 1. Register new user via browser form.<br>2. Refresh page and restart backend server.<br>3. Log in with registered credentials; confirm successful session establishment. |
| **DEF-06** | Bound Builder dashboard summary cards to live calculation of active projects, requirements, members, and advice. | `backend/app/services/project_service.py`<br>`backend/app/api/v1/projects.py`<br>`frontend/src/components/DashboardView.jsx` | `GET /api/v1/projects/summary` returns dynamic aggregate counts derived exclusively from caller's authorized projects in PostgreSQL. | `test_def06_builder_dashboard_real_metrics` | **PASS** | **NOT VERIFIED** | 1. Log in as Builder A (1 project); verify summary cards match project metrics.<br>2. Log in as Builder B (0 projects); verify cards display 0 projects, 0 requirements, 0 advice. |
| **DEF-07** | Replaced static advisor dropdown with dynamic live query to `/api/v1/advisors` backed by `AdvisorProfile`. | `backend/app/api/v1/advisors.py`<br>`frontend/src/services/advisorService.js`<br>`frontend/src/components/DashboardView.jsx` | `GET /api/v1/advisors` returns newly registered advisors immediately upon registration. | `test_def07_newly_registered_advisor_in_advisor_selector` | **PASS** | **NOT VERIFIED** | 1. Register new advisor Dr. Vance.<br>2. Log in as Builder; open "Invite Advisor" modal.<br>3. Verify Dr. Vance appears in the dynamic selector dropdown. |
| **DEF-10** | Replaced fixed 60% completion fallback with dynamic readiness calculation derived strictly from real requirements, advice, and decisions. | `backend/app/api/v1/readiness.py`<br>`frontend/src/components/DashboardView.jsx` | `GET /api/v1/projects/{id}/readiness` returns `readiness_percentage: 0` when project has no completed items; scales dynamically as items are finished. | `test_def10_dynamic_completion_calculation` | **PASS** | **NOT VERIFIED** | 1. Create fresh project; verify readiness indicator shows 0%.<br>2. Complete 1 requirement and log advice; verify readiness percentage updates dynamically. |
| **DEF-11** | Advice form state initialized strictly to empty string `''`. Form state auto-resets on open and upon successful submission. | `frontend/src/components/AdvisorDashboardView.jsx` | `POST /api/v1/projects/{id}/advice` accepts clean user-authored text and persists in PostgreSQL `project_management.advice`. | `test_def11_advice_form_empty_by_default` | **PASS** | **NOT VERIFIED** | 1. Open advice creation modal as Advisor; verify all text areas and inputs are blank.<br>2. Enter guidance and submit; reopen modal; verify form has reset to blank. |
| **DEF-12** | Dynamically mapped `projectAdviceList` in Builder dashboard advice subtab; renders real advisor guidance, recommendation, and status. | `frontend/src/components/DashboardView.jsx` | Advisor posts advice via `POST /api/v1/projects/{id}/advice`; Builder immediately retrieves it via `GET /api/v1/projects/{id}/advice`. | `test_def12_advisor_advice_visibility_in_builder_dashboard` | **PASS** | **NOT VERIFIED** | 1. Submit advice as Advisor for Project 1.<br>2. Log in as Builder; navigate to Advice subtab; verify advice card displays title, text, and recommendation.<br>3. Refresh browser (F5); confirm advice persists. |
| **DEF-13** | Removed all hardcoded `\|\| 1` project fallbacks. Enforced BOLA/IDOR ownership checks; rendered empty state when builder has 0 projects. | `backend/app/security/authorization.py`<br>`frontend/src/components/DashboardView.jsx` | Non-member request to `/api/v1/projects/{id}`, `/advice`, or `/attachments` strictly returns HTTP 403 Forbidden. | `test_def13_builder_project_bola_isolation` | **PASS** | **NOT VERIFIED** | 1. Log in as Builder A (owns Project 1).<br>2. Manually alter URL or API target to Project 2 (owned by Builder B).<br>3. Verify 403 Forbidden alert is rendered; zero Project 2 records leaked. |
| **DEF-14** | Updated `seed_data.py` to preserve existing user password hashes rather than overwriting them with default hashes on seed runs. | `backend/scripts/seed_data.py` | Registered user with custom password retains authentication ability after full `seed_database()` execution. | `test_def14_seed_preserves_existing_user_hashes` | **PASS** | **PASS** (CLI) | 1. Register user with custom password.<br>2. Run `python -m scripts.seed_data`.<br>3. Authenticate with custom password; confirm login succeeds. |
| **DEF-15** | Hardened password recovery: single-use tokens, SHA-256 storage, rollback on delivery failure, anti-enumeration, dual-key sliding window rate limiter (`rate_limit_service.py`), session revocation. | `backend/app/services/auth_service.py`<br>`backend/app/services/email_service.py`<br>`backend/app/services/rate_limit_service.py`<br>`backend/app/schemas/auth.py`<br>`backend/app/models/identity.py`<br>`backend/alembic/versions/003_create_password_reset_tokens.py`<br>`backend/app/security/authentication.py`<br>`frontend/src/components/LoginForm.jsx` | 5 dedicated regression tests verifying: public response never exposes tokens, identical response shapes for existing vs. unknown emails, transactional rollback on SMTP failure, truthful unconfigured reporting, sliding window rate limits (HTTP 429), and session token revocation. | `test_def15_password_reset_anti_enumeration_and_test_sink`<br>`test_def15_password_reset_smtp_failure_handling_and_rollback`<br>`test_def15_password_reset_unconfigured_smtp`<br>`test_def15_password_reset_rate_limiting_per_account_and_ip`<br>`test_def15_password_reset_token_rejection_and_session_invalidation` | **PASS** | **NOT VERIFIED** | 1. In Login modal, click "Forgot Password".<br>2. Submit email with unconfigured SMTP; confirm UI displays amber "Delivery Blocked / Unconfigured" warning without error crash.<br>3. With test sink / SMTP active, request reset; retrieve token from test mail sink.<br>4. Enter token and new password; submit; confirm successful password change.<br>5. Log in with new credentials. |
| **DEF-16** | Replaced heuristic byte checks with real `pypdf` structural document validation. Bounded upload streaming directly into disk temporary files (10MB limit), safe UUID storage, and atomic DB rollback with disk cleanup. | `backend/app/api/v1/attachments.py`<br>`backend/app/models/attachment.py`<br>`backend/requirements.txt`<br>`frontend/src/services/adviceService.js`<br>`frontend/src/components/AdvisorDashboardView.jsx`<br>`frontend/src/components/DashboardView.jsx` | Spoofed PDFs (having fake headers/trailers but invalid structure) rejected with HTTP 422. Valid ISO 32000 PDFs accepted (HTTP 201). Truncated, empty, and oversized (>10MB) payloads rejected. Outsiders denied (HTTP 403). Downloaded file verified byte-identical. | `test_def16_pdf_attachment_upload_magic_bytes_and_access_control`<br>`test_def16_pdf_attachment_structural_validation_and_bounded_streaming` | **PASS** | **NOT VERIFIED** | 1. In Advisor project workspace, upload a valid PDF; verify upload success banner.<br>2. Rename a `.txt` file to `.pdf` and upload; verify rejection alert.<br>3. Upload oversized >10MB file; verify rejection alert.<br>4. Log in as Builder; download PDF; verify document opens cleanly with byte-identical content. |
| **DEF-17** | Preserved Admin dashboard role detection across browser refresh via persisted auth session. Added resilient error handling for admin data services. Restricted non-admin access. | `backend/app/api/v1/admin.py`<br>`frontend/src/components/LoginForm.jsx`<br>`frontend/src/components/AdminDashboardView.jsx` | `GET /api/v1/admin/stats` and `/users` return HTTP 200 for ADMIN, strictly HTTP 403 Forbidden for BUILDER and ADVISOR. Page refresh preserves admin session. | `test_def17_admin_dashboard_role_guard_and_resilience` | **PASS** | **NOT VERIFIED** | 1. Log in as admin; confirm Admin Cockpit renders.<br>2. Press browser refresh (F5); confirm admin cockpit remains active without falling back to Builder.<br>3. Log in as Builder; verify direct navigation to `/admin` is rejected. |

---

## 3. Detailed Security Hardenings

### 3.1 Password-Reset Delivery Reporting & Token Lifecycle (DEF-15)
- **Truthful Delivery Reporting:** The service evaluates both configuration status (`is_email_configured()`) and transport availability (`is_email_service_available()`).
  - Globally unconfigured: returns `status="pending_configuration"`, `delivery_channel="SMTP (Unconfigured)"`.
  - Transport failure / outage: returns `status="delivery_failed"`, `delivery_channel="Email (Service Unavailable)"`.
  - Operational: returns `status="success"`, `message="If an account associated with this email address exists, password recovery instructions have been dispatched."`.
- **Anti-Enumeration Contract:** For any given environment state, registered and non-registered email addresses receive 100% identical public response bodies, status codes, and message strings.
- **Transactional Rollback:** Email dispatch is attempted before revoking prior tokens or committing new tokens. If email sending fails, the database transaction is rolled back (`db.rollback()`), guaranteeing that prior active recovery tokens are not invalidated and no dead tokens linger in PostgreSQL.
- **Privacy-Preserving Dual-Key Rate Limiting:** Enforced via `app/services/rate_limit_service.py`:
  - Per-account sliding window (5 attempts / 15 minutes) using SHA-256 digests (`acct:<hash>`).
  - Per-client IP sliding window (20 attempts / 15 minutes) using SHA-256 digests (`src:<hash>`).
  - Zero raw emails retained in rate-limit memory keys.
  - Memory bounded via automatic expiration and capacity eviction (`MAX_TRACKED_KEYS = 2000`).
  - Explicit test isolation hook `reset_rate_limiter()` prevents test leakage.
  - Documented as single-process in-memory limiter.

### 3.2 Real Structural PDF Document Validation (DEF-16)
- **Pure Python Parser:** Integrated `pypdf>=5.0.0` and `python-multipart>=0.0.12`.
- **Structural Integrity Checks:** Replaced loose byte heuristics with `pypdf.PdfReader(stream, strict=False)`. Rejects spoofed files containing `%PDF-` and `%%EOF` markers without valid object trees, catalogs, or pages. Requires `len(reader.pages) >= 1`.
- **Bounded Streaming & Safe Temporary Files:** Streaming upload body is spooled into a temporary file on disk (`tempfile.NamedTemporaryFile`) outside the web root. Bounded read loop enforces strict 10MB limit chunk-by-chunk even when `Content-Length` is absent or manipulated.
- **Atomic Operations & Cleanup:** Temporary files are atomically moved (`os.replace`) to final storage upon successful validation. On any validation error, DB failure, or oversized payload, temporary files are removed immediately (`os.remove`).
- **No False Antivirus Claims:** Documented truthfully that antivirus scanning is unconfigured in this prototype environment.

---

## 4. Reproducible Verification Evidence

### 4.1 Backend Pytest Regression Suite
- **Command:** `venv\Scripts\python.exe -m pytest tests`
- **Exit Status:** 0 (Clean exit)
- **Test Results:** 106 passed, 0 failed in 34.15s
- **Database Used:** `finregtech_test` (PostgreSQL localhost:5432)
- **Primary Database:** `"FinRegTech ShipYard"` untouched

### 4.2 Defect Remediation Test Suite
- **Command:** `venv\Scripts\python.exe -m pytest tests/test_master_defect_remediation.py -v`
- **Exit Status:** 0 (Clean exit)
- **Test Results:** 19 passed, 0 failed in 9.64s
- **Detailed Defect Suite Results:**
  - `test_def01_advisor_empty_project_assignments_by_default`: PASSED
  - `test_def02_advisor_login_clean_tokens_and_roles`: PASSED
  - `test_def03_admin_dashboard_live_postgresql_data`: PASSED
  - `test_def05_registered_users_authoritative_persistence_in_db`: PASSED
  - `test_def06_builder_dashboard_real_metrics`: PASSED
  - `test_def07_newly_registered_advisor_in_advisor_selector`: PASSED
  - `test_def10_dynamic_completion_calculation`: PASSED
  - `test_def11_advice_form_empty_by_default`: PASSED
  - `test_def12_advisor_advice_visibility_in_builder_dashboard`: PASSED
  - `test_def13_builder_project_bola_isolation`: PASSED
  - `test_def14_seed_preserves_existing_user_hashes`: PASSED
  - `test_def15_password_reset_anti_enumeration_and_test_sink`: PASSED
  - `test_def15_password_reset_smtp_failure_handling_and_rollback`: PASSED
  - `test_def15_password_reset_unconfigured_smtp`: PASSED
  - `test_def15_password_reset_rate_limiting_per_account_and_ip`: PASSED
  - `test_def15_password_reset_token_rejection_and_session_invalidation`: PASSED
  - `test_def16_pdf_attachment_upload_magic_bytes_and_access_control`: PASSED
  - `test_def16_pdf_attachment_structural_validation_and_bounded_streaming`: PASSED
  - `test_def17_admin_dashboard_role_guard_and_resilience`: PASSED

### 4.3 Frontend Production Build
- **Command:** `npm run build`
- **Exit Status:** 0 (Clean exit)
- **Duration:** 1.41s
- **Output:**
  - `dist/index.html` (1.03 kB)
  - `dist/assets/index-C_KaZoyt.css` (88.39 kB)
  - `dist/assets/index-k6Mg-OEL.js` (501.21 kB)
- **Compile Errors / Warnings:** 0 errors

### 4.4 Database & Migration Verification
- **Command:** `venv\Scripts\alembic.exe heads`
- **Current Revision:** `001_create_revoked_tokens`
- **Head Revision:** `003_create_password_reset_tokens (head)`
- **Safety Rule Compliance:** Primary database `"FinRegTech ShipYard"` preserved with zero modifications, drops, or schema truncations.

---

## 5. Known Limitations & Outstanding Testing

1. **Browser Automation Framework Absence:** Because no headless browser runner (Playwright, Selenium, Puppeteer) is installed in the repository, frontend UI states are classified as **NOT VERIFIED** in this report, pending independent manual execution following the protocols in Section 2.
2. **Single-Process Rate Limiter:** The dual-key sliding window rate limiter operates in-memory within the active application process. In a distributed multi-worker deployment, a shared cache (such as Redis) would be required for global rate enforcement.
3. **Local SMTP Configuration:** Production email delivery requires valid SMTP credentials in `.env` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`). When unconfigured, the application safely and truthfully surfaces `SMTP (Unconfigured)` without account enumeration.
4. **Antivirus Scanning Daemon:** PDF upload validation enforces strict ISO 32000 structural document checks via `pypdf`, but external ClamAV/antivirus daemon scanning is not configured in this prototype.
