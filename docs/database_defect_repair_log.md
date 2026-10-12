# Database Defect and Repair Log
## FinRegTech ShipYard | FCC Project Cockpit

**Project:** FinRegTech ShipYard — FCC Project Cockpit
**Application Prototype:** ABC Shield for The Compliance Register, UK
**Evaluation Date:** October 13, 2026
**Auditor & Lead Architect:** Vishal (Backend Lead & Database Architect)
**Database Target:** PostgreSQL 18.6 (`"FinRegTech ShipYard"`)
**Resolution Status:** **`100% DEFECTS RESOLVED & VERIFIED`**

---

## 1. Executive Defect Summary

During the comprehensive forensic audit of real PostgreSQL persistence and frontend-backend integration, a total of 8 defects were discovered, diagnosed to root causes, repaired, and rigorously verified.

```
Total Defects Logged:       8
Defects Remediated:         8 (100%)
Unresolved / Blocked:       0 (0%)
Regression Test Result:     66/66 PASSED in Pytest, 10/10 E2E Workflows, 8/8 Real Browser Stages
```

---

## 2. Itemized Defect Inventory

| Defect ID | Severity | Subsystem | Description | Status |
|---|---|---|---|---|
| **DB-DEF-001** | CRITICAL | Backend Routing | Root origin `http://127.0.0.1:8000/` returned HTTP 404 `{"detail":"Not Found"}` | **RESOLVED & VERIFIED** |
| **DB-DEF-002** | HIGH | Health Diagnostics | `/health` endpoint returned static dictionary without verifying PostgreSQL connection | **RESOLVED & VERIFIED** |
| **DB-DEF-003** | HIGH | Database Engine | Silent SQLite fallback in `app/db/session.py` caused potential split-brain storage | **RESOLVED & VERIFIED** |
| **DB-DEF-004** | MEDIUM | Schema Serialization | `ProjectResponse` omitted `code` computed alias, returning `None` in project responses | **RESOLVED & VERIFIED** |
| **DB-DEF-005** | MEDIUM | Route Alignment | Audit log endpoint route naming mismatch (`/audit-trail` vs `/audit-events`) | **RESOLVED & VERIFIED** |
| **DB-DEF-006** | HIGH | Project Governance | Sole-owner member removal/demotion allowed, risking orphaned projects | **RESOLVED & VERIFIED** |
| **DB-DEF-007** | HIGH | Security / RBAC | Public registration endpoint accepted `role: ADMIN` without validation | **RESOLVED & VERIFIED** |
| **DB-DEF-008** | HIGH | Security / BOLA | Incomplete project isolation on sub-endpoints allowed potential cross-project access | **RESOLVED & VERIFIED** |

---

## 3. Forensic Repair Breakdown

### DB-DEF-001: Root Endpoint HTTP 404 (Screenshot Defect)
- **Severity:** CRITICAL
- **Component:** `backend/app/main.py`
- **Symptom:** Opening `http://127.0.0.1:8000` in the browser resulted in a blank page displaying `{"detail":"Not Found"}` with status code 404.
- **Root Cause:** FastAPI route dispatch is explicit. Sub-routers were mounted under `/api/v1` and OpenAPI docs at `/docs` and `/redoc`. The root path `"/"` had no handler registered, causing Starlette to emit a default 404 response.
- **Remediation:** Added `@app.get("/", tags=["System"])` route handler returning complete service metadata, status, version, documentation links, and the API v1 base.
- **Verification:** Verified with HTTP client; returns HTTP 200 OK with service metadata and online status.

---

### DB-DEF-002: Static Health Check Masking Database Outages
- **Severity:** HIGH
- **Component:** `backend/app/main.py`
- **Symptom:** `GET /health` returned `"database": "connected"` even when database credentials were wrong or the service was disconnected.
- **Root Cause:** The endpoint returned a hardcoded response dictionary without performing an actual database query.
- **Remediation:** Upgraded `/health` to execute `SELECT 1` via SQLAlchemy `engine.connect()` and report dynamic connection status and active engine dialect.
- **Verification:** Live test confirmed `/health` returns `"dialect": "postgresql"`, `"status": "connected"`.

---

### DB-DEF-003: Silent SQLite Fallback Risk
- **Severity:** HIGH
- **Component:** `backend/app/db/session.py`
- **Symptom:** If PostgreSQL initialization lagged or environment variables fluctuated, the backend fell back to a local SQLite database, resulting in data desynchronization.
- **Root Cause:** `create_db_engine` caught connection errors and silently switched to SQLite without requiring explicit configuration.
- **Remediation:** Enforced strict PostgreSQL connection. If connection fails and `ALLOW_SQLITE_FALLBACK` is false (default), the engine raises an immediate `RuntimeError`.
- **Verification:** Pytest test `test_db_dialect_is_strictly_postgresql` confirms active dialect is `postgresql`.

---

### DB-DEF-004: Missing `code` Alias in Project Serialization
- **Severity:** MEDIUM
- **Component:** `backend/app/schemas/project.py`
- **Symptom:** In serialized JSON responses, `project.code` was absent or null, even though `project_code` was populated in PostgreSQL.
- **Root Cause:** `ProjectResponse` defined `@computed_field` for `id`, `name`, and `type`, but lacked `@computed_field` for `code`.
- **Remediation:** Added computed property:
  ```python
  @computed_field
  @property
  def code(self) -> str:
      return self.project_code
  ```
- **Verification:** `scripts/test_restart_persistence.py` confirmed `code` is populated as `"PRJ-AUDIT-54842"`.

---

### DB-DEF-005: Audit Log Route Alignment
- **Severity:** MEDIUM
- **Component:** `backend/app/api/v1/audit.py`, `frontend/src/services/auditService.js`
- **Symptom:** Out-of-spec test callers requested `GET /projects/{id}/audit-trail` and received HTTP 404.
- **Root Cause:** The backend router was configured with prefix `/projects/{projectId}/audit-events`, matching `auditService.js`.
- **Remediation:** Standardized and verified contract alignment across all client callers and verification harnesses to target `/projects/{projectId}/audit-events`.
- **Verification:** Verified in Pytest `test_audit_events_retrieval` and `scripts/verify_postgres_persistence_e2e.py`.

---

### DB-DEF-006: Sole-Owner Revocation Invariant Violation
- **Severity:** HIGH
- **Component:** `backend/app/api/v1/project_members.py`
- **Symptom:** Project owners could remove themselves or downgrade their roles, leaving orphan projects without an owner.
- **Root Cause:** Member update and delete endpoints lacked an invariant check ensuring at least one owner remains.
- **Remediation:** Added sole-owner protection guard raising HTTP 400 Bad Request if the sole owner is targeted for removal or demotion.
- **Verification:** Pytest `test_sole_owner_cannot_be_revoked` passed.

---

### DB-DEF-007: Public Admin Self-Registration Vulnerability
- **Severity:** HIGH
- **Component:** `backend/app/services/auth_service.py`
- **Symptom:** A user registering via `POST /api/v1/auth/register` could supply `"role": "ADMIN"` and gain platform administrator privileges.
- **Root Cause:** Registration service accepted arbitrary role names from the request body.
- **Remediation:** Added strict role validation restricting self-registration to `BUILDER` and `ADVISOR`. Supplying `ADMIN` triggers an explicit `HTTP 403 Forbidden` response.
- **Verification:** Pytest `test_register_admin_forbidden` passed.

---

### DB-DEF-008: BOLA / IDOR Project Boundary Defense
- **Severity:** HIGH
- **Component:** `backend/app/security/authorization.py`
- **Symptom:** Authenticated users from Project A could potentially access or modify data in Project B.
- **Root Cause:** Inconsistent application of the `require_project_member` dependency across nested sub-resources.
- **Remediation:** Applied `require_project_member` and `require_project_owner` dependencies across all project-scoped routes.
- **Verification:** Automated tests confirmed that cross-project access attempts return HTTP 403 Forbidden with zero database alterations.

---

## 4. Regression Testing Summary

Following all remediations, the full regression suite was executed:
- **Pytest Suite:** 66/66 PASSED in 20.98s (exit code 0).
- **10-Workflow Audit:** 10/10 WORKFLOWS PASSED in 6.4s (exit code 0).
- **Real Browser CDP Test:** 8/8 STAGES PASSED in Headless Chrome 154 (exit code 0).
- **Frontend Production Build:** Built in 1.73s (exit code 0).
