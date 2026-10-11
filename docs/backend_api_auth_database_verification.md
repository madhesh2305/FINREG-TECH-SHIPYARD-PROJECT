# BACKEND API, AUTH & DATABASE VERIFICATION REPORT
**Project:** FinRegTech ShipYard | FCC Project Cockpit  
**Application Scope:** ABC Shield (UK Bribery Act 2010 Adequate Procedures & EU Anti-Corruption Directives)  
**Database Authority:** PostgreSQL 18.6 (`"FinRegTech ShipYard"` on `localhost:5432`)  
**Status:** **AUTHORITATIVE & VERIFIED**  

---

## 1. Database Connection & Schema Verification

### 1.1 Active Database Engine & Dialect
- **Dialect Name:** `postgresql`
- **Host / Port:** `localhost:5432`
- **Database Name:** `"FinRegTech ShipYard"`
- **Driver:** `psycopg2-binary` (native binary PostgreSQL driver)
- **Engine Configuration:**
  - `pool_size`: 10
  - `max_overflow`: 20
  - `pool_pre_ping`: True
  - Silent SQLite fallback: **DISABLED**

### 1.2 Physical Schemas and Table Inventory

| PostgreSQL Schema | Physical Tables | Row Counts / Entities Verified | Invariant Status |
|-------------------|-----------------|--------------------------------|:----------------:|
| `identity` | `roles`, `users` | 3 roles (`ADMIN`, `BUILDER`, `ADVISOR`), 126+ users | **VERIFIED** |
| `project_management` | `projects`, `project_profiles`, `project_members` | 79+ projects, Project 1 sole owner `jun@finregtech.io` | **VERIFIED** |
| `advisory` | `advisor_profiles`, `advice_records` | Expert directory & advice submissions | **VERIFIED** |
| `regulatory` | `regulatory_sources`, `regulatory_requirements` | 27 curated regulatory sources (6 ABC-specific) | **VERIFIED** |
| `decision_governance` | `compliance_decisions` | Ratified human compliance decisions | **VERIFIED** |
| `audit` | `audit_events` | Immutable audit log trail (append-only) | **VERIFIED** |

---

## 2. Authentication & Authorization Test Matrix

Verification was executed via live HTTP calls against the running application to validate security invariants without exposing secret keys:

| Test Scenario | Request Under Test | Supplied Credential | Expected Status | Actual Status | Response Detail / Evidence |
|---------------|-------------------|---------------------|:---------------:|:-------------:|----------------------------|
| **1. Missing Credentials** | `GET /api/v1/projects` | None | `401` | **401** | `{"detail": "Authentication token is missing"}` |
| **2. Malformed Credential** | `GET /api/v1/projects` | `Bearer invalid.malformed.token` | `401` | **401** | `{"detail": "Invalid or expired authentication token"}` |
| **3. Expired Credential** | `GET /api/v1/projects` | Expired JWT (`expires_delta=-60s`) | `401` | **401** | `{"detail": "Invalid or expired authentication token"}` |
| **4. Valid Registered User** | `GET /api/v1/projects` | Valid JWT for `jun@finregtech.io` | `200` | **200** | Returns array of projects owned by or assigned to user |
| **5. Deleted / Non-Existent User** | `GET /api/v1/projects` | JWT referencing non-existent `user_id` | `401` | **401** | `{"detail": "User associated with token no longer exists"}` |
| **6. Deactivated Account** | `POST /api/v1/auth/login` | Valid credentials for deactivated account | `403` | **403** | `{"detail": "Your account has been deactivated..."}` |
| **7. Cross-Project Access (BOLA/IDOR)** | `GET /api/v1/projects/1` | Valid JWT for non-member user | `403` | **403** | `{"detail": "You are not an active member of this project"}` |
| **8. Self-Admin Registration** | `POST /api/v1/auth/register` | Payload with `role: "ADMIN"` | `403` | **403** | `{"detail": "Platform Administrator accounts cannot be self-registered..."}` |
| **9. Non-Admin Accessing Admin** | `GET /api/v1/admin/stats` | Valid JWT for `BUILDER` or `ADVISOR` | `403` | **403** | `{"detail": "Operation requires one of the following platform roles: ADMIN"}` |

---

## 3. Route Matching & API Contract Verification

All 31 API endpoints registered in FastAPI were audited against OpenAPI specifications:

### 3.1 Authentication & User Governance
- `POST /api/v1/auth/register` → 201 Created (403 on admin, 422 on invalid role).
- `POST /api/v1/auth/login` → 200 OK (returns `access_token`, `platform_role`, `email`, `full_name`).
- `GET /api/v1/users/me` → 200 OK (returns current user context and project memberships).
- `PATCH /api/v1/users/me` → 200 OK (persists full_name edits).

### 3.2 Project Management & Workspace Isolation
- `GET /api/v1/projects` → 200 OK (lists user-accessible projects; multi-tenant filtered).
- `GET /api/v1/projects/summary` → 200 OK (returns aggregate counts).
- `POST /api/v1/projects` → 201 Created (provisions project, profile, and sole OWNER membership).
- `GET /api/v1/projects/{projectId}` → 200 OK (resolves both numeric IDs like `1` and alphanumeric codes like `PRJ-ABC-001`).
- `PATCH /api/v1/projects/{projectId}` → 200 OK (restricted to project owner).

### 3.3 Regulatory Intelligence
- `GET /api/v1/regulatory-requirements` → 200 OK (lists global regulatory sources).
- `GET /api/v1/regulatory/sources` → 200 OK (paginated corpus of 27 sources).
- `GET /api/v1/projects/{projectId}/requirements` → 200 OK (project-scoped compliance requirements).
- `POST /api/v1/projects/{projectId}/requirements` → 201 Created (links requirement to project).

### 3.4 Advisory Collaboration & RAG Engine
- `GET /api/v1/advisors` → 200 OK (directory of approved expert advisors).
- `POST /api/v1/projects/{projectId}/advisor-invitations` → 201 Created (issues invitation token).
- `POST /api/v1/projects/{projectId}/advice` → 201 Created (records advisor recommendation).
- `POST /api/v1/rag/analyze` → 200 OK (executes grounded AI retrieval conforming to W4.11 schema).

### 3.5 Decision Governance, Readiness & Audit
- `POST /api/v1/projects/{projectId}/decisions` → 201 Created (ratifies binding human decision).
- `GET /api/v1/projects/{projectId}/readiness` → 200 OK (evaluates 3-pillar dynamic readiness score).
- `GET /api/v1/projects/{projectId}/audit-events` → 200 OK (streams immutable audit log).

### 3.6 Administration Cockpit
- `GET /api/v1/admin/stats` → 200 OK (platform-wide KPIs).
- `GET /api/v1/admin/users` → 200 OK (user governance directory).
- `PATCH /api/v1/admin/users/{userId}/status` → 200 OK (toggles active/suspended state).
