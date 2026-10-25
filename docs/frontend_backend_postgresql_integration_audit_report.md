# FINREGTECH SHIPYARD — FRONTEND–BACKEND–POSTGRESQL INTEGRATION AUDIT REPORT

**Project:** FinRegTech ShipYard — FCC Project Cockpit v0.1  
**Audit Date:** 21 October 2026  
**Auditor Role:** Senior Full-Stack Integration & QA Auditor / Backend & Workflow Engineer Intern  
**Repository:** `https://github.com/madhesh2305/FINREG-TECH-SHIPYARD-PROJECT`  
**Backend Branch:** `feature/vishal-backend` (Verified Remote HEAD: `961cb9f`)  
**Frontend Branch Audited:** `feature/harshini-frontend` (Verified Remote HEAD: `4a33599`)  
**Main Branch:** `main` (Verified Remote HEAD: `358057a`)  
**Isolated Test Database:** `finregtech_test` (PostgreSQL 16, Port 5432) — *Verified via `SELECT current_database()`*  
**Protected Primary Database:** `"FinRegTech ShipYard"` (PostgreSQL 16, Port 5432) — *Protected; Zero writes or resets*  

---

## A. Overall Integration Verdict

### **PARTIALLY INTEGRATED**

**Executive Summary:**  
While Harshini's frontend (`feature/harshini-frontend` @ `4a33599`) has configured its API base URL to target `http://localhost:8000/api/v1` and correctly routes two read endpoints (`POST /rag/analyze` and `GET /regulatory-requirements`), **zero core business write actions currently persist to PostgreSQL**. 

Due to a schema mismatch in user registration (`name` instead of `full_name`), the backend rejects registration requests with `HTTP 422 Unprocessable Entity`. The frontend catch blocks suppress this error, store the user's plaintext password in browser `localStorage`, and return apparent success. Subsequent logins fail backend authentication (HTTP 401), causing the frontend to issue synthetic bearer tokens (`jwt_token_...`) and operate entirely inside a client-side `localStorage` shadow store. Furthermore, advice submission, decisions, and admin oversight make **zero backend API calls**, reading and mutating only `localStorage`.

---

## B. Branch and Configuration State

### 1. Remote Branch Inventory & HEAD Commit Verifications
- **Backend (`feature/vishal-backend`):** Remote HEAD is `961cb9f` (`fix(backend): remove demo data and verify persistence`). Commit author: Vishal S.R. Confirmed live on GitHub.
- **Frontend (`feature/harshini-frontend`):** Remote HEAD is `4a33599` (`fix(admin): resolve ReferenceError in AdminDashboardView metricCards rendering`). Commit author: harshini2111. Confirmed live on GitHub.
- **Main (`main`):** Remote HEAD is `358057a` (`Initial commit`).
- **Ancestry Relationship:** Both `feature/harshini-frontend` and Vishal's working branches diverged from common ancestor `642e114`. Harshini's branch has 10 independent commits that have not been merged into `main` or reconciled with backend API schemas.
- **Local Worktree Alignment:**
  - `backend` workspace is on `feature/vishal-backend` at `961cb9f`.
  - `frontend` workspace is on `feature/vishal-frontend` at `cbc0a51`. Harshini's branch was inspected non-destructively via `origin/feature/harshini-frontend` without modifying any frontend files.

### 2. Runtime & Network Configuration
- **Frontend Dev Server:** Configured for Vite on `http://localhost:5173`.
- **Frontend API Base URL:** Configured in `frontend/.env` as `VITE_API_URL=http://localhost:8000/api/v1`. Default in `src/services/api.js` is `'http://localhost:8000/api/v1'`.
- **Backend Host & Port:** Configured in `backend/.env` for `127.0.0.1:8000` (API prefix: `/api/v1`).
- **CORS Configuration:** `backend/app/core/config.py` explicitly allows origins:
  `["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]`.
- **Server Status:** Neither port 8000 nor 5173 was actively listening prior to the test suite; test executions used in-process FastAPI `TestClient` and safe test server scripts.

---

## C. Frontend-to-Backend Traceability Matrix

Evaluation of all 17 primary workflows between Harshini's frontend (`feature/harshini-frontend`) and Vishal's backend (`feature/vishal-backend`):

| # | Frontend Page / Action | Frontend Service & Function | HTTP Method & URL | Backend Route Declaration | Auth / Role Requirements | PostgreSQL Operation | Integration Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | User Registration | `authService.js` -> `registerUser()` | `POST /api/v1/auth/register` | `app/api/v1/auth.py` -> `@router.post("/auth/register")` | Public | None (Rejected by FastAPI with HTTP 422) | **SCHEMA MISMATCH & FRONTEND MOCK/FALLBACK** |
| **2** | User Login | `authService.js` -> `loginUser()` | `POST /api/v1/auth/login` | `app/api/v1/auth.py` -> `@router.post("/auth/login")` | Public | None (Fails 401; mints synthetic token) | **FRONTEND MOCK/FALLBACK** |
| **3** | Session Restoration (F5) | `LoginForm.jsx` (initial state) | None | None | None | None | **FRONTEND MOCK/FALLBACK** |
| **4** | User Profile Update | `userService.js` -> `updateUserProfile()` | `PUT /api/v1/user/profile` | `app/api/v1/users.py` -> `@router.patch("/users/me")` | Authenticated | None (Backend returns 404 Not Found) | **BACKEND MISSING / MISMATCH & FRONTEND MOCK/FALLBACK** |
| **5** | Project List & Details | `projectService.js` -> `getProjects()`, `getProjectDetails()` | `GET /api/v1/projects`, `GET /api/v1/projects/{id}` | `app/api/v1/projects.py` -> `@router.get("/projects")` | Project Member | `SELECT ... FROM projects` (Bypassed by fallback) | **FRONTEND MOCK/FALLBACK & CRITICAL BOLA/IDOR** |
| **6** | Project Creation | `projectService.js` -> `createProject()` | `POST /api/v1/projects` | `app/api/v1/projects.py` -> `@router.post("/projects")` | `BUILDER` | None (Rejected with 401 under fake token) | **PARTIAL MATCH / FRONTEND MOCK/FALLBACK** |
| **7** | Advisor Invitations | `advisorService.js` -> `sendAdvisorInvitation()` | `POST /api/v1/projects/{id}/advisor-invitations` | `app/api/v1/project_members.py` -> `@router.post("/.../advisor-invitations")` | Project Owner (`BUILDER`) | None (Fails under fake token; returns fake success) | **FRONTEND MOCK/FALLBACK** |
| **8** | Regulatory Requirements | `regulatoryService.js` -> `getRegulatoryRequirements()` | `GET /api/v1/regulatory-requirements` | `app/api/v1/regulatory.py` -> `@router.get("/regulatory-requirements")` | Public / Authenticated | `SELECT ... FROM regulatory_requirements` | **MATCH** |
| **9** | Advice Submission & Review | `AdvisorDashboardView.jsx` -> `handleSubmitAdvice()` | None (Zero API calls; deleted `adviceService.js`) | `app/api/v1/advice.py` -> `@router.post("/.../advice")` | `ADVISOR` | None (Mutates `localStorage` only) | **FRONTEND MOCK/FALLBACK** |
| **10** | Conflict / RAG Analysis | `ragService.js` -> `analyzeRAGConflict()` | `POST /api/v1/rag/analyze` | `app/api/v1/ai.py` -> `@router.post("/rag/analyze")` | Public / Authenticated | `SELECT ... FROM regulatory_sources` | **MATCH** |
| **11** | Decisions & Rationale | `AdviceDecisionsView.jsx` -> `handleRecordDecision()` | None (Zero API calls) | `app/api/v1/decisions.py` -> `@router.post("/.../decisions")` | Project Owner (`BUILDER`) | None (Updates React in-memory state only) | **FRONTEND MOCK/FALLBACK** |
| **12** | Readiness Assessment | `DashboardView.jsx` -> `<ReadinessView />` | None (Zero API calls) | `app/api/v1/readiness.py` -> `@router.get("/.../readiness")` | Project Member | None (Renders empty default in-memory) | **FRONTEND MOCK/FALLBACK** |
| **13** | Audit Trail History | `auditService.js` -> `getAuditEvents()` | `GET /api/v1/projects/{id}/audit-events` | `app/api/v1/audit.py` -> `@router.get("/.../audit-events")` | Project Member | `SELECT ... FROM audit_events` | **PARTIAL MATCH** |
| **14** | Admin Dashboard & Stats | `AdminDashboardView.jsx` | None (Zero API calls; deleted `adminService.js`) | `app/api/v1/admin.py` -> `@router.get("/admin/stats")` | Platform `ADMIN` | None (Reads `getRegisteredUsers()` from `localStorage`) | **FRONTEND MOCK/FALLBACK** |
| **15** | Notifications | `userService.js` -> `updateNotificationPreferences()` | `PUT /api/v1/user/notifications` | `app/api/v1/users.py` -> `@router.get("/users/me/notifications")` | Authenticated | None (Backend returns 404 Not Found) | **BACKEND MISSING / MISMATCH & FRONTEND MOCK/FALLBACK** |
| **16** | Password Recovery | `authService.js` -> `resetPassword()` | `POST /api/v1/auth/forgot-password` | `app/api/v1/auth.py` -> `@router.post("/.../password-reset-request")` | Public | None (Backend returns 404 Not Found) | **MISMATCH & FRONTEND MOCK/FALLBACK** |
| **17** | PDF Upload & Download | Not Implemented on Harshini's Frontend | None (`api.js` lacks `FormData` and blob support) | `app/api/v1/attachments.py` -> `@router.post("/.../attachments")` | Project Member | None | **FRONTEND MOCK/FALLBACK / NOT IMPLEMENTED** |

---

## D. PostgreSQL Persistence Evidence

### 1. Database Safety & Identity Verification
- **Verified Target Database:** `finregtech_test` (PostgreSQL 16 on `localhost:5432`) confirmed via `verify_test_db.py` returning `SELECT current_database() == 'finregtech_test'`.
- **Primary Database Status:** `"FinRegTech ShipYard"` strictly isolated; zero automated writes or schema alterations executed against it.
- **Alembic Migration State:** `003_create_password_reset_tokens` confirmed in `alembic_version` table.

### 2. Empirical Persistence Tests
1. **Schema Mismatch Empirical Test (`test_register_schema_mismatch`):**
   - Payload: `{"name": "Audit Tester", "email": "audittester1@example.com", "password": "Password123!", "role": "BUILDER"}`
   - Result: HTTP 422 Unprocessable Entity.
   - Response: `{"detail": "Request payload validation failed", "errors": [{"loc": ["body", "full_name"], "msg": "Field required", "type": "missing"}]}`
   - PostgreSQL DB Query: `SELECT COUNT(*) FROM identity.users WHERE email = 'audittester1@example.com'` returned `0`.
2. **Correct Schema Empirical Test (`test_register_correct_schema`):**
   - Payload: `{"full_name": "Audit Tester", "email": "audittester1@example.com", "password": "Password123!", "role": "BUILDER"}`
   - Result: HTTP 201 Created.
   - PostgreSQL DB Query: User record found in `identity.users` with valid bcrypt hash.
3. **Password Reset Endpoint Mismatch Test:**
   - Payload to `POST /api/v1/auth/forgot-password`: Returns `HTTP 404 Not Found`.
   - Payload to `POST /api/v1/auth/password-reset-request`: Returns `HTTP 200 OK` with truthful status.
4. **User Profile Endpoint Mismatch Test:**
   - Payload to `PUT /api/v1/user/profile`: Returns `HTTP 404 Not Found`.
   - Payload to `PATCH /api/v1/users/me`: Returns `HTTP 200 OK` and updates `identity.users.full_name`.

---

## E. Security Findings on `feature/harshini-frontend`

1. **[CRITICAL] Plaintext Password Storage in Browser Storage (`src/services/authService.js`):**
   When `registerUser()` is called, the user object is constructed with `newUser.password = cleanPassword` and written into browser `localStorage` under `finreg_registered_users`. Any user inspecting browser DevTools or executing script in the browser context can read all registered passwords in plaintext.
2. **[CRITICAL] Synthetic JWT Bearer Token Generation (`src/services/authService.js`):**
   When backend login fails, `loginUser()` searches local browser storage and mints an unverified token: `jwt_token_${matchedUser.id}_${Date.now()}`. This creates an illusion of authentication while the user has zero valid credentials with the backend.
3. **[CRITICAL] Administrator Authentication Bypass (`src/components/LoginForm.jsx`):**
   `LoginForm.jsx` contains an administrative mock dropdown (`"Authorized Admin session"` vs `"Unauthorized Admin session"`). When backend login fails, if `adminResponse === 'Authorized Admin session'`, the form grants full Administrator workspace access without verifying credentials.
4. **[CRITICAL BOLA / IDOR] Project Detail Fallback to `all[0]` (`src/services/projectService.js`):**
   In `getProjectDetails(projectId)`, if the request fails (e.g. HTTP 403 Forbidden because the user is an outsider), the catch block executes: `return all.find((p) => p.id === projectId) || all[0];`. This leaks another user's project details to an unauthorized caller.
5. **[HIGH] Session Eviction on Browser Reload (`src/components/LoginForm.jsx`):**
   `step` is initialized to `'flash'`, ignoring stored auth tokens and forcing the user back to the login screen on every browser refresh.

---

## F. Defect List for Remediation

| Defect Reference | Severity | Layer & Component | Reproduction Steps | Expected Behavior | Actual Behavior | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INT-01** | CRITICAL | Frontend `authService.js` | Register new account from signup form. | Frontend sends `full_name`, receives real JWT, persists to PostgreSQL. | Frontend sends `name`, receives 422, catches error, saves plaintext password to `localStorage`. | Update `registerUser` payload key to `full_name`. Remove plaintext password storage and catch fallback. |
| **INT-02** | CRITICAL | Frontend `authService.js` & `LoginForm.jsx` | Enter invalid credentials or log in with unseeded user. | Login fails with HTTP 401; user is notified of invalid credentials. | Fails backend, catches 401, matches `localStorage`, mints fake `jwt_token_...`. | Remove local credentials fallback and fake token generator. Enforce real backend tokens. |
| **INT-03** | CRITICAL | Frontend `projectService.js` | Request project ID for project belonging to another user. | Backend returns HTTP 403 Forbidden; frontend displays "Access Denied". | Frontend catches error and falls back to `|| all[0]`, displaying another user's project. | Remove `|| all[0]` fallback. Propagate 403 error to UI. |
| **INT-04** | HIGH | Frontend `AdvisorDashboardView.jsx` | Advisor submits advisory review. | Frontend calls `POST /api/v1/projects/{id}/advice`; record persists to PostgreSQL `advice.advice`. | Frontend makes 0 API calls; writes review into `localStorage` string array. | Wire `handleSubmitAdvice` to backend `POST /api/v1/projects/{id}/advice`. |
| **INT-05** | HIGH | Frontend `AdminDashboardView.jsx` | Log in as Administrator and inspect dashboard stats. | Frontend calls `GET /api/v1/admin/stats` and `GET /api/v1/admin/users`. | Frontend makes 0 API calls; reads `getRegisteredUsers()` from `localStorage`. | Wire component to real backend admin routes via `adminService.js`. |
| **INT-06** | MEDIUM | Frontend `userService.js` | Update user profile name. | Frontend calls `PATCH /api/v1/users/me`. | Frontend calls `PUT /user/profile` (404 Not Found); fakes success. | Update URL to `PATCH /users/me` with `{ full_name }` payload. |
| **INT-07** | MEDIUM | Frontend `authService.js` | Request password reset instructions. | Frontend calls `POST /api/v1/auth/password-reset-request`. | Frontend calls `POST /auth/forgot-password` (404 Not Found); fakes success. | Update URL to `POST /auth/password-reset-request`. |
| **INT-08** | MEDIUM | Frontend `api.js` | Upload PDF file attachment. | `apiCall` detects `FormData`, avoids `JSON.stringify`, sends multipart payload. | `apiCall` stringifies `FormData` to `"{}"` and sets JSON content-type. | Add `body instanceof FormData` check in `apiCall`. |

---

## G. Ready-to-Forward Message for Harshini

```text
Hi Harshini,

We conducted an independent integration audit tracing the frontend requests on feature/harshini-frontend directly to the backend routes and PostgreSQL tables. We confirmed that your UI layout, styling, and forms look great, and two read routes (POST /rag/analyze and GET /regulatory-requirements) are communicating properly!

However, we discovered that zero core business actions (registration, login, advice submission, project creation, admin stats) are actually reaching the backend or persisting in PostgreSQL. This is due to a few payload schema mismatches and localStorage fallback catch blocks:

1. [CRITICAL] Registration Field Mismatch & Plaintext Password Storage (src/services/authService.js):
   - In registerUser(), the payload sends 'name', but the backend schema expects 'full_name'.
   - This causes the backend to return HTTP 422 Unprocessable Entity.
   - The catch block currently intercepts this error, writes newUser.password into localStorage under 'finreg_registered_users', and returns { success: true }.
   - Fix: Change payload key from 'name' to 'full_name'. Remove the plaintext password save in localStorage. Do not report success if the backend request fails.

2. [CRITICAL] Fake Token Minting & Admin Session Bypass (src/services/authService.js & LoginForm.jsx):
   - In loginUser(), when the backend returns 401, the catch block matches credentials against localStorage and mints a fake token ('jwt_token_...').
   - In LoginForm.jsx, the dropdown 'Authorized Admin session' allows logging in as Administrator even when the backend is unreachable.
   - Fix: Rely solely on the real JWT token returned by the backend POST /api/v1/auth/login. Remove the synthetic token generator and adminResponse bypass.

3. [CRITICAL BOLA / IDOR] Project Detail Fallback to all[0] (src/services/projectService.js):
   - In getProjectDetails(projectId), if the backend returns 403 Forbidden or 404, it currently falls back to '|| all[0]'. This leaks another user's project in the UI.
   - In getProjects(), if the backend returns [] (valid zero projects for a new user), it falls back to getLocalProjects().
   - Fix: Remove the '|| all[0]' fallback. If the backend returns 403, display an explicit "Access Denied" state. Allow [] to render the clean empty state.

4. [HIGH] Advice Submission & Admin Dashboard Not Calling Backend:
   - In AdvisorDashboardView.jsx, handleSubmitAdvice() writes to localStorage under 'finreg_advisor_reviews' without making an API call.
   - In AdminDashboardView.jsx, users and projects are loaded from localStorage rather than calling GET /api/v1/admin/stats and GET /api/v1/admin/users.
   - Fix: Connect advice submission to POST /api/v1/projects/{projectId}/advice and the admin dashboard to the real admin endpoints.

5. [MEDIUM] Endpoint Route Name Corrections:
   - Profile update: Change from PUT /user/profile to PATCH /api/v1/users/me (payload: { full_name }).
   - Password reset: Change from POST /auth/forgot-password to POST /api/v1/auth/password-reset-request.
   - File upload: In api.js, ensure apiCall() does not call JSON.stringify() if body is an instance of FormData.

Once these five fixes are applied, the frontend will connect seamlessly with the live PostgreSQL database!
```

---

## H. Final Statement & Explicit Answers to the 10 Audit Questions

1. **Does the frontend actually call this backend?**  
   **Partially.** The frontend sends HTTP requests to `http://localhost:8000/api/v1`, but when registration fails with HTTP 422, it abandons live backend communication and switches entirely to local browser storage.
2. **Are the frontend API paths and backend routes compatible?**  
   **No.** Multiple route paths and schemas mismatch: registration (`name` vs `full_name`), profile update (`PUT /user/profile` vs `PATCH /users/me`), password reset (`POST /auth/forgot-password` vs `POST /auth/password-reset-request`), and advice/admin endpoints are completely absent from Harshini's frontend.
3. **Does authentication work end-to-end?**  
   **No.** Due to the registration 422 error, user accounts are never created in PostgreSQL. Login falls back to checking localStorage and generating synthetic bearer tokens (`jwt_token_...`).
4. **Do writes persist in PostgreSQL?**  
   **No.** Zero writes from Harshini's frontend workflows currently persist to the PostgreSQL database.
5. **Do data survive refresh/relogin where applicable?**  
   **No.** Browser reload forces session eviction because `LoginForm.jsx` re-initializes `step` to `'flash'` without restoring active session state.
6. **Are fake datasets or fallback responses still masking errors?**  
   **Yes.** Catch blocks across `authService.js`, `projectService.js`, `advisorService.js`, and `userService.js` actively convert backend 422, 401, 403, and 404 errors into simulated client-side success.
7. **Which workflows are verified end-to-end?**  
   Only **Workflow 8 (Regulatory Requirements)** and **Workflow 10 (Conflict / RAG Analysis)** are verified communicating with backend routes and returning real data.
8. **Which workflows remain unverified or broken?**  
   Workflows 1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, and 17 remain broken or unverified on Harshini's branch due to schema mismatches, missing routes, or mock fallbacks.
9. **Has any frontend file been modified?**  
   **No.** Zero frontend files were modified, staged, committed, or touched during this audit.
10. **Were any Git commits or pushes performed?**  
   **No.** Zero Git commits and zero Git pushes were performed for this audit task. Both repositories remain clean and untouched.
