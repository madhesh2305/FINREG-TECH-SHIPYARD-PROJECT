# BACKEND REPAIR LOG: FINREGTECH SHIPYARD
**Project:** FinRegTech ShipYard | FCC Project Cockpit  
**Application Scope:** ABC Shield (UK Bribery Act 2010 Adequate Procedures & EU Anti-Corruption Directives)  
**Execution Mode:** Precise, Root-Cause-Driven Repairs  
**Date:** 11 October 2026  

---

## 1. Summary of Changes

| Change ID | Target File | Component / Area | Why Changed |
|-----------|-------------|------------------|-------------|
| **MOD-01** | `backend/app/db/session.py` | Database Session & Engine | Prevent silent degradation into unseeded SQLite databases and enforce PostgreSQL 18.6 connection. |
| **MOD-02** | `backend/app/services/auth_service.py` | Authentication Service | Eliminate hardcoded credential exceptions and standardize on bcrypt password verification. |
| **MOD-03** | `backend/scripts/seed_data.py` | Database Seeder | Generate authentic password hashes for all seeded accounts directly in PostgreSQL. |
| **MOD-04** | `backend/app/api/v1/projects.py` | Project Router | Allow project resolution by alphanumeric code (`PRJ-ABC-001`) as well as integer ID. |
| **MOD-05** | `backend/app/schemas/user.py` | User Schemas | Add `UserUpdateRequest` schema for user profile modifications. |
| **MOD-06** | `backend/app/api/v1/users.py` | User Router | Implement `PATCH /api/v1/users/me` endpoint to support real user profile updates in PostgreSQL. |
| **MOD-07** | `backend/tests/test_auth.py` | Auth Test Suite | Add regression test `test_patch_current_user_me` to verify profile persistence. |
| **MOD-08** | `frontend/src/services/userService.js` | User API Client | Replace non-existent `PUT /user/profile` with `PATCH /users/me` and eliminate fake fallback. |
| **MOD-09** | `frontend/src/services/toolService.js` | Tools API Client | Eliminate blind calls to non-existent `/tools` endpoint that caused HTTP 404 console errors. |
| **MOD-10** | `frontend/src/services/projectService.js` | Project API Client | Purge `MOCK_PROJECTS` array and ensure real database data is returned. |
| **MOD-11** | `frontend/src/services/advisorService.js` | Advisor API Client | Purge `MOCK_ADVISORS`, `MOCK_TEAM_MEMBERS`, and simulated invitation tokens. |
| **MOD-12** | `frontend/src/services/ragService.js` | RAG API Client | Purge `MOCK_RAG_RESPONSE` and return authoritative backend RAG engine responses. |
| **MOD-13** | `frontend/src/services/regulatoryService.js` | Regulatory API Client | Purge `MOCK_REQUIREMENTS` and query live PostgreSQL regulatory corpus. |
| **MOD-14** | `frontend/src/services/auditService.js` | Audit API Client | Purge `MOCK_AUDIT_EVENTS` and stream real audit trail from PostgreSQL. |
| **MOD-15** | `frontend/src/components/DashboardView.jsx` | Builder Dashboard UI | Purge hardcoded identities, eliminate fake project fabrication on error, and add empty states. |
| **MOD-16** | `frontend/src/components/AdvisorDashboardView.jsx` | Advisor Dashboard UI | Purge hardcoded identity and display authentic server error toasts on submission failure. |
| **MOD-17** | `frontend/src/components/SettingsView.jsx` | Settings UI | Bind profile settings to authenticated user and persist via `PATCH /api/v1/users/me`. |

---

## 2. Detailed File Modification Records

### MOD-01: `backend/app/db/session.py`
- **File Changed:** [`backend/app/db/session.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/db/session.py#L42-L78)
- **Why Changed:** The application silently fell back to SQLite when PostgreSQL was temporarily unreachable, resulting in `sqlite3.OperationalError: no such table: identity_users`.
- **Previous Behavior:** Caught PostgreSQL connection exceptions and created an SQLite engine using `finregtech_dev.db` with in-memory attached databases.
- **New Behavior:** Enforces strict PostgreSQL connection to `"FinRegTech ShipYard"`. If connection fails and `ALLOW_SQLITE_FALLBACK` is not explicitly set to true, raises a fatal `RuntimeError` preventing silent degradation.
- **Related Test:** `tests/test_verify_live.py` (verifies dialect is PostgreSQL).
- **Test Result:** **PASSED** (Dialect verified as `postgresql`).

---

### MOD-02: `backend/app/services/auth_service.py`
- **File Changed:** [`backend/app/services/auth_service.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/services/auth_service.py#L20-L36)
- **Why Changed:** Code contained hardcoded password bypasses (`builder@gmail.com` with `builder`, `advisor@gmail.com` with `advisor`) which violated security rules and masked database hash mismatches.
- **Previous Behavior:** Checked specific hardcoded email and password literals before checking password hash.
- **New Behavior:** Standardized pure password hash verification: `verify_password(request.password, user.password_hash)`.
- **Related Test:** `tests/test_auth.py`, `tests/test_register.py::test_login_with_demo_credentials`.
- **Test Result:** **PASSED** (60/60 tests passed).

---

### MOD-03: `backend/scripts/seed_data.py`
- **File Changed:** [`backend/scripts/seed_data.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/scripts/seed_data.py#L88-L106)
- **Why Changed:** Demo accounts were previously seeded with a single generic hash for `Password123!`, causing logins with documented demo credentials (`builder`, `advisor`) to fail without hardcoded code bypasses.
- **Previous Behavior:** Assigned identical password hash to all users regardless of role.
- **New Behavior:** Accurately computes bcrypt hashes per user (`builder` for demo builder, `advisor` for demo advisor, `Password123!` for platform accounts) during seeding.
- **Related Test:** `tests/test_register.py::test_login_with_demo_credentials`.
- **Test Result:** **PASSED**.

---

### MOD-04: `backend/app/api/v1/projects.py`
- **File Changed:** [`backend/app/api/v1/projects.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/api/v1/projects.py#L78-L100)
- **Why Changed:** Frontend requests passed alphanumeric project codes (e.g. `PRJ-ABC-001`), but the backend route had path converter `:int`, returning `404 Not Found`.
- **Previous Behavior:** `@router.get("/{projectId:int}")` rejected string codes.
- **New Behavior:** `@router.get("/{projectId}")` accepts string `projectId`. If numeric, resolves by `project_id`; if alphanumeric, resolves by `project_code`.
- **Related Test:** `tests/test_projects.py`, `tests/test_verify_live.py` (Stage 4 resolves `PRJ-795C46`).
- **Test Result:** **PASSED**.

---

### MOD-05 & MOD-06: `backend/app/schemas/user.py` & `backend/app/api/v1/users.py`
- **Files Changed:** 
  - [`backend/app/schemas/user.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/schemas/user.py#L5-L7)
  - [`backend/app/api/v1/users.py`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/api/v1/users.py#L48-L65)
- **Why Changed:** Frontend needed to update user profiles, but backend lacked `PATCH /api/v1/users/me`, causing frontend to call non-existent `PUT /user/profile` and receive 404.
- **Previous Behavior:** Only `GET /api/v1/users/me` existed; profile edits were impossible.
- **New Behavior:** Added `UserUpdateRequest` schema and implemented `PATCH /api/v1/users/me` with SQLAlchemy update on `identity.users.full_name`.
- **Related Test:** `tests/test_auth.py::test_patch_current_user_me`.
- **Test Result:** **PASSED**.

---

### MOD-08: `frontend/src/services/userService.js`
- **File Changed:** [`frontend/src/services/userService.js`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/userService.js#L5-L25)
- **Why Changed:** Called non-existent `PUT /user/profile` and returned fake `{ success: true, ...DEFAULT_PROFILE }`.
- **Previous Behavior:** Attempted `PUT /user/profile` and returned mock user profile on 404.
- **New Behavior:** Calls `PATCH /users/me` with `{ full_name }` and re-throws errors so the UI displays authentic state.
- **Related Test:** Frontend production build (`npm run build`).
- **Test Result:** **PASSED**.

---

### MOD-09: `frontend/src/services/toolService.js`
- **File Changed:** [`frontend/src/services/toolService.js`](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/toolService.js#L50-L75)
- **Why Changed:** Called non-existent `GET /tools` and `POST /tools/{toolId}/use`, causing 404 network errors in browser console.
- **Previous Behavior:** Fired blind HTTP requests to `/tools`, caught 404s, and logged warnings.
- **New Behavior:** Serves curated ecosystem tools directly from platform catalog and persists toggle state in `localStorage` without triggering 404 network errors.
- **Related Test:** Frontend production build (`npm run build`).
- **Test Result:** **PASSED**.

---

### MOD-10 through MOD-14: Frontend Services Purging Mock Fallbacks
- **Files Changed:**
  - `projectService.js`: Purged `MOCK_PROJECTS` array.
  - `advisorService.js`: Purged `MOCK_ADVISORS`, `MOCK_TEAM_MEMBERS`, and simulated invitation tokens.
  - `ragService.js`: Purged `MOCK_RAG_RESPONSE`.
  - `regulatoryService.js`: Purged `MOCK_REQUIREMENTS`.
  - `auditService.js`: Purged `MOCK_AUDIT_EVENTS`.
- **Why Changed:** Ensure the UI always renders authentic database state and never fabricates mock fallbacks or fake successes.
- **Test Result:** **PASSED** (all services verified with live API calls).

---

### MOD-15 through MOD-17: UI Components Dynamic Identity & Error Handling
- **Files Changed:**
  - `DashboardView.jsx`: Dynamically binds header user initials, name, email, and role from `currentUser`. Replaced fake project fabrication on error with real error toast. Added empty states.
  - `AdvisorDashboardView.jsx`: Dynamically binds header identity from `currentUser`. Shows authentic error toast on submission error.
  - `SettingsView.jsx`: Populates form with `currentUser` and updates database via `PATCH /api/v1/users/me`.
- **Test Result:** **PASSED** (`npm run build` completed with 0 errors).
