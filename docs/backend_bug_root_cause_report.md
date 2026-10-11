# BACKEND BUG ROOT-CAUSE REPORT: FINREGTECH SHIPYARD
**Project:** FinRegTech ShipYard | FCC Project Cockpit  
**Application Scope:** ABC Shield (UK Bribery Act 2010 Adequate Procedures & EU Anti-Corruption Directives)  
**Database Authority:** Local PostgreSQL 18.6 (`"FinRegTech ShipYard"` on `localhost:5432`)  
**Investigation Date:** 11 October 2026  
**Auditor / Lead Engineer:** Vishal S.R.  

---

## Executive Summary of Findings

| # | Reported Issue / Symptom | Status | Root Cause Category | Primary Files Involved |
|---|--------------------------|:------:|---------------------|------------------------|
| **1** | `sqlite3.OperationalError: no such table: identity_users` (`FROM identity.users AS identity_users`) | **FIXED AND VERIFIED** | Unintended SQLite Fallback & Schema-Qualification Incompatibility | `backend/app/db/session.py`, `backend/app/core/config.py`, `backend/.env` |
| **2** | Repeated `401 Unauthorized` responses from `GET /api/v1/projects` | **FIXED AND VERIFIED** | Missing/Malformed Bearer Token Transmission & Session Cache Expiration | `backend/app/security/authentication.py`, `frontend/src/services/api.js`, `frontend/src/services/authService.js` |
| **3** | FastAPI `404 Not Found` response: `{"detail":"Not Found"}` | **FIXED AND VERIFIED** | Path Type Restriction on String Project Codes, Mismatched `/user/profile` Route, and Frontend Unregistered `/tools` Invocations | `backend/app/api/v1/projects.py`, `backend/app/api/v1/users.py`, `frontend/src/services/toolService.js` |

---

## Issue 1: SQLite Schema Error (`sqlite3.OperationalError: no such table: identity_users`)

### 1.1 Original Symptom
- **Observed Error:** `sqlite3.OperationalError: no such table: identity_users`
- **Observed SQL:** `SELECT ... FROM identity.users AS identity_users`
- **Context:** The application or test runtime was unexpectedly executing against SQLite instead of PostgreSQL, and SQLAlchemy failed to resolve the schema-qualified table `identity.users`.

### 1.2 Reproduction Evidence
1. **Engine Dialect Isolation:**
   When an in-memory or file-based SQLite engine was connected with SQLAlchemy models configured with `__table_args__ = {"schema": "identity"}`:
   ```python
   engine = create_engine('sqlite:///:memory:')
   s = sessionmaker(bind=engine)()
   s.query(User).first()
   ```
   **Output:**
   ```text
   (sqlite3.OperationalError) no such table: identity.users
   [SQL: SELECT identity.users.user_id AS identity_users_user_id ... FROM identity.users AS identity_users]
   ```
   SQLAlchemy automatically names the table alias `identity_users` by concatenating `<schema>_<tablename>`.
2. **PostgreSQL Fallback Leak:**
   In `backend/app/db/session.py`, the previous configuration allowed a silent fallback to `SQLITE_FALLBACK_URL = "sqlite:///./finregtech_dev.db"` whenever the connection to PostgreSQL failed (e.g. invalid password, missing binary drivers `psycopg2-binary`, or host unreachable).
   Once fallen back to SQLite, the attached databases in SQLite (`ATTACH DATABASE ':memory:' AS identity`) lacked physical tables, resulting in immediate `no such table: identity_users` exceptions.

### 1.3 Confirmed Root Cause
1. **The application was never designed to use SQLite in production.** It is an enterprise multi-tenant system structured into PostgreSQL schemas (`identity`, `project_management`, `advisory`, `regulatory`, `audit`, `decision_governance`).
2. Prior to driver and credential synchronization, the backend failed to establish connection to PostgreSQL and fell back silently to SQLite.
3. SQLite does not have native multi-schema DDL support without custom schema translation maps, causing all queries targeting `identity.users` to fail.

### 1.4 Repair Applied
1. **Disabled Silent SQLite Fallback:**
   In [`backend/app/db/session.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/db/session.py#L56-L78), removed silent SQLite fallback. The engine now connects exclusively to PostgreSQL 18.6 (`"FinRegTech ShipYard"`). If PostgreSQL is unreachable, it raises a fatal runtime error rather than silently degrading into an empty SQLite database.
2. **Synchronized Authoritative Database:**
   Verified and configured native PostgreSQL binary drivers (`psycopg2-binary` and `psycopg[binary]`) and confirmed authoritative connection to `postgresql://postgres:***@localhost:5432/FinRegTech ShipYard`.
3. **Database Verification:**
   Verified that all schemas (`identity`, `project_management`, `regulatory`, `audit`) and tables exist in PostgreSQL. SQLAlchemy queries execute with native schema support without error.

### 1.5 Security & Data-Integrity Implications
Eliminates data loss risks where user registrations were written to ephemeral or disconnected SQLite databases. All data is reliably persisted in PostgreSQL 18.6 with ACID guarantees.

---

## Issue 2: Repeated `401 Unauthorized` Responses from `GET /api/v1/projects`

### 1.1 Original Symptom
- **Observed Request:** `GET /api/v1/projects`
- **Observed Response:** `401 Unauthorized` (`{"detail": "Authentication token is missing"}` or `{"detail": "Invalid or expired authentication token"}`)

### 1.2 Reproduction Evidence
Executed systematic test matrix across all 6 possible authentication states:
1. **Missing Token:** `GET /api/v1/projects` with no headers → `401 Unauthorized` (`detail: Authentication token is missing`).
2. **Malformed Token:** `GET /api/v1/projects` with `Authorization: Bearer invalid.token` → `401 Unauthorized` (`detail: Invalid or expired authentication token`).
3. **Expired Token:** `GET /api/v1/projects` with expired JWT → `401 Unauthorized` (`detail: Invalid or expired authentication token`).
4. **Authorized Project Owner:** `GET /api/v1/projects` with valid JWT for `jun@finregtech.io` → `200 OK`, returning authorized projects list.
5. **Non-Existent User ID in Token:** Validly signed JWT referencing deleted or non-existent `user_id=999999` → `401 Unauthorized` (`detail: User associated with token no longer exists`).
6. **Cross-Project Access (BOLA/IDOR):** Authorized user accessing a project they do not belong to → `403 Forbidden` (`detail: You are not an active member of this project`).

### 1.3 Confirmed Root Cause
1. **Frontend Request Lifecycle Disconnect:**
   When the user refreshed the browser or navigated from a non-authenticated state, `authToken` in `localStorage` was either absent or expired (`ACCESS_TOKEN_EXPIRE_MINUTES = 480`).
   `DashboardView.jsx` mounted and immediately called `getProjects()` on mount via `useEffect`. If `getToken()` returned `null`, the request was sent without an `Authorization` header, triggering a 401.
2. **Hardcoded Demo Credentials Exceptions:**
   In [`backend/app/services/auth_service.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/services/auth_service.py), legacy code contained hardcoded password bypasses (`builder@gmail.com` with `builder`, `advisor@gmail.com` with `advisor`) rather than standard password hashing. When users attempted authentic logins, password mismatch occurred.

### 1.4 Repair Applied
1. **Standardized Password Verification:**
   Removed all hardcoded credential bypasses from [`authenticate_user()`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/services/auth_service.py#L20-L28). Standardized on `verify_password(request.password, user.password_hash)`.
2. **Synchronized Password Hashes in Database:**
   Updated database records so all demo accounts have authentic bcrypt password hashes in PostgreSQL matching their documented passwords.
3. **Frontend Token Injection & State Guarding:**
   Verified that [`api.js`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/api.js) automatically injects `Authorization: Bearer <token>` for all authenticated calls.
   In [`DashboardView.jsx`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/components/DashboardView.jsx), handled token expiration cleanly: on 401, session clears and redirects to login rather than silently failing.

### 1.5 Security Implications
Preserved strict JWT validation. No endpoints were made public. 401 is strictly enforced for unauthenticated requests, and 403 is enforced for unauthorized project access (BOLA/IDOR protection).

---

## Issue 3: FastAPI `404 Not Found` Response (`{"detail":"Not Found"}`)

### 1.1 Original Symptom
- **Observed Response:** `{"detail": "Not Found"}` (HTTP 404)
- **Problem:** The specific endpoint and method were unidentified in initial logs.

### 1.2 Forensic Inspection & Route Audit
Conducted full audit of all 31 registered FastAPI routes in `app.openapi()` and cross-referenced with all `apiCall()` invocations across frontend services:
1. **Candidate 1: String Project Code Resolution (`GET /api/v1/projects/PRJ-ABC-001`)**
   - **Previous Route:** `@router.get("/{projectId:int}")`
   - **Frontend Call:** When opening a project from the dashboard, frontend passed string project code `PRJ-ABC-001`.
   - **Outcome:** FastAPI's path converter rejected string `"PRJ-ABC-001"` against `:int`, returning `404 Not Found`.
2. **Candidate 2: User Profile Update (`PUT /api/v1/user/profile`)**
   - **Frontend Call:** In `userService.js`, `updateUserProfile()` requested `PUT /user/profile`.
   - **Backend Status:** Route did not exist. Backend route was `GET /api/v1/users/me`.
   - **Outcome:** Returned `404 Not Found`.
3. **Candidate 3: Ecosystem Tools Directory (`GET /api/v1/tools` & `POST /api/v1/tools/{id}/use`)**
   - **Frontend Call:** In `toolService.js`, `getTools()` requested `GET /tools`.
   - **Backend Status:** No `/tools` router was registered in FastAPI.
   - **Outcome:** Returned `404 Not Found`.
4. **Candidate 4: Missing `/api/v1` Prefix (`GET /projects`)**
   - **Direct Call:** Testing against root `/projects` instead of `/api/v1/projects` returned `404 Not Found`.

### 1.3 Confirmed Root Causes
The reported `{"detail":"Not Found"}` was generated by three distinct mismatched routes:
1. `GET /api/v1/projects/PRJ-ABC-001` failed because `projectId` was constrained to integer type.
2. `PUT /api/v1/user/profile` failed because the endpoint did not exist in backend.
3. `GET /api/v1/tools` failed because `toolService.js` fired blind network requests to a non-existent backend path.

### 1.4 Repair Applied
1. **Alphanumeric Project Code Resolution:**
   In [`backend/app/api/v1/projects.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/api/v1/projects.py#L78-L100), updated `projectId: str`. The endpoint now resolves both integer IDs (`1`, `2`) and alphanumeric project codes (`PRJ-ABC-001`, `PRJ-795C46`).
2. **Implemented `PATCH /api/v1/users/me`:**
   Added `PATCH /api/v1/users/me` to [`backend/app/api/v1/users.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/api/v1/users.py#L48-L65) and updated [`frontend/src/services/userService.js`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/userService.js#L5-L16) to call `PATCH /users/me`.
3. **Repaired `toolService.js`:**
   In [`frontend/src/services/toolService.js`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/toolService.js), eliminated blind calls to `/tools`. Serves curated ecosystem tools directly from platform catalog and persists toggle state in `localStorage` without triggering 404 network errors.

### 1.5 Verification Outcome
- `GET /api/v1/projects/PRJ-ABC-001` → **200 OK**
- `PATCH /api/v1/users/me` → **200 OK**
- `ToolsView` browsing → **0 Network Errors**
- All 31 registered API endpoints verified against `openapi.json`.
