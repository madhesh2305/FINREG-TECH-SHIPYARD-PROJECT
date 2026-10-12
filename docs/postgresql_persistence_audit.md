# PostgreSQL Persistence Audit Report
## FinRegTech ShipYard | FCC Project Cockpit

**Project:** FinRegTech ShipYard — FCC Project Cockpit
**Application:** ABC Shield Prototype for The Compliance Register, UK
**Evaluation Date:** October 13, 2026
**Auditor & Lead Architect:** Vishal (Lead Backend Engineer & Database Architect)
**Database Engine:** PostgreSQL 18.6 on Port 5432
**Database Name:** `"FinRegTech ShipYard"`
**Active Dialect:** `postgresql`
**Connection Pool:** SQLAlchemy with `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`
**Silent SQLite Fallback:** STRICTLY DISABLED
**Audit Verdict:** **`DATABASE INTEGRATION VERIFIED`**

---

## 1. Executive Summary

This forensic audit verifies that all core functionality requiring persistent storage in the **FinRegTech ShipYard | FCC Project Cockpit** application is directly backed by the live PostgreSQL database (`"FinRegTech ShipYard"`).

Every user registration, authentication handshake, project lifecycle event, regulatory requirement mapping, advisor invitation, legal advice submission, compliance decision, and audit log entry executes real database transactions that commit to disk and survive application restarts.

---

## 2. Phase 1: Database Connection & Runtime Configuration Trace

### 2.1 Connection Settings & Configuration Source
- The connection parameters are defined in `backend/.env` via `DATABASE_URL` and loaded through `backend/app/core/config.py` using Pydantic Settings.
- The connection strictly targets `postgresql://postgres:***@localhost:5432/FinRegTech%20ShipYard`.
- The database name `"FinRegTech ShipYard"` contains an encoded space (`%20`), which is automatically decoded to `"FinRegTech ShipYard"` by `app/db/session.py` via `urllib.parse.unquote`.

### 2.2 ORM and Transaction Layer
- Database operations are managed via **SQLAlchemy 2.0 ORM** sessions (`SessionLocal`).
- Requests obtain database sessions via FastAPI's `get_db` dependency (`Generator[Session, None, None]`), ensuring sessions are cleanly committed and closed per request.
- Unhandled exceptions trigger automatic transaction rollbacks to protect relational integrity.

### 2.3 Elimination of Silent SQLite Fallbacks
- In `backend/app/db/session.py`, silent SQLite fallbacks are forbidden. If PostgreSQL cannot be reached and `ALLOW_SQLITE_FALLBACK` is false (default), the engine raises an explicit `RuntimeError` on startup.
- Verification confirmed that no SQLite `.db` files or mock storage layers exist in the runtime environment.

### 2.4 Service Health Verification
- `GET http://127.0.0.1:8000/health` executes an active `SELECT 1` query on the PostgreSQL engine:
  ```json
  {
    "status": "healthy",
    "service": "FinRegTech Shipyard - FCC Project Cockpit",
    "version": "0.4.0",
    "environment": "development",
    "database": {
      "status": "connected",
      "dialect": "postgresql"
    }
  }
  ```

---

## 3. Phase 2: User Registration & Authentication Flow Trace

The registration and login flow was traced end-to-end through browser automation and database inspection:

```mermaid
sequenceDiagram
    autonumber
    actor User as Frontend UI (React)
    participant API as FastAPI Backend (/api/v1)
    participant Auth as AuthService
    participant DB as PostgreSQL (identity.users)

    User->>API: POST /auth/register (email, password, full_name, role)
    API->>Auth: register_user(request)
    Auth->>Auth: Validate role != 'ADMIN', validate email uniqueness
    Auth->>Auth: Hash password with bcrypt (salt cost 12)
    Auth->>DB: INSERT INTO identity.users (email, password_hash, role_id...)
    DB-->>Auth: COMMIT -> user_id: 178
    Auth-->>API: JWT Token + User Metadata
    API-->>User: HTTP 201 Created (access_token, user_id)
    User->>User: Store token in localStorage ('authToken')
    User->>API: POST /auth/login (email, password)
    API->>Auth: authenticate_user(email, password)
    Auth->>DB: SELECT * FROM identity.users WHERE email = :email
    DB-->>Auth: Persisted user record + bcrypt hash
    Auth->>Auth: bcrypt.checkpw(password, hash) -> True
    Auth-->>API: Issue JWT Bearer Token
    API-->>User: HTTP 200 OK (access_token)
```

### Verified Forensic Invariants:
1. **Password Hashing:** Passwords are never stored in plaintext. They are hashed using bcrypt (`$2b$12$...`) before database insertion.
2. **Role Security:** Role assignments are validated against `identity.roles`. Attempts to self-register as `ADMIN` are rejected with HTTP 403 Forbidden.
3. **Duplicate Prevention:** Registering an existing email is rejected with HTTP 409 Conflict without creating duplicate records.
4. **Invalid Password Defense:** Supplying an incorrect password returns HTTP 401 Unauthorized without creating session tokens.
5. **Restart Survivability:** After terminating and rebooting the backend server process, previously registered users authenticate against their stored bcrypt hashes without error.

---

## 4. Phase 3: Comprehensive Domain-by-Domain Persistence Audit

Every frontend and backend feature was audited and classified:

### Domain A: Users & Authentication
- **Registration:** `PERSISTENT` (Saved in `identity.users` with bcrypt hash).
- **Login / Logout:** `PERSISTENT` (Validates against `identity.users` on every login).
- **Current User Profile:** `READ_ONLY` / `PERSISTENT` (Loaded from `identity.users` via `GET /users/me`).
- **Profile Updates:** `PERSISTENT` (Persists to `identity.users` via `PATCH /users/me`).
- **User Roles & Account Status:** `PERSISTENT` (Persisted in `identity.users.is_active` and `identity.roles`).
- **Session Cache:** `LOCAL_ONLY` (JWT cached in `localStorage` as `authToken`; validated by backend on every API call).

### Domain B: Projects
- **Project Listing:** `READ_ONLY` / `PERSISTENT` (Queries `project_management.projects` filtered by membership).
- **Project Creation:** `PERSISTENT` (Inserts into `project_management.projects`, `project_profiles`, `project_members`).
- **Project Detail:** `READ_ONLY` / `PERSISTENT` (Dual lookup by integer ID and string code).
- **Project Profile Updates:** `PERSISTENT` (Updates `project_management.projects` / `project_profiles`).
- **Project Ownership:** `PERSISTENT` (Sole-owner protection enforced in `project_management.project_members`).

### Domain C: Regulatory Requirements
- **Regulatory Source Library:** `READ_ONLY` (27 curated rulebooks in `regulatory.regulatory_sources`).
- **Source Details & Provenance:** `READ_ONLY` (Full statutory references in `regulatory.regulatory_sources`).
- **Project Requirements:** `PERSISTENT` (Saved in `regulatory.regulatory_requirements`).
- **Requirement Creation:** `PERSISTENT` (Provenance check against `regulatory_sources`, writes to `regulatory_requirements`).
- **Requirement Status Updates:** `PERSISTENT` (Updates `applicability_status` and `requirement_status`).

### Domain D: Advisors & Invitations
- **Advisor Directory & Profiles:** `READ_ONLY` (Loaded from `advisor_management.advisor_profiles`).
- **Advisor Invitations:** `PERSISTENT` (Saved in `advisor_management.advisor_invitations`).
- **Invitation Lifecycle:** `PERSISTENT` (Status transitions: `PENDING` -> `ACCEPTED` / `REVOKED` / `EXPIRED`).
- **Project Team Membership:** `PERSISTENT` (Saved in `project_management.project_members`).

### Domain E: Legal Advice & AI/RAG
- **Advisor Advice Submissions:** `PERSISTENT` (Saved in `advice.advice` and `advice.advice_source_links`).
- **Advice Retrieval & Review:** `READ_ONLY` / `PERSISTENT` (Loaded from `advice.advice`).
- **Grounded Statutory Retrieval (RAG):** `READ_ONLY` / `COMPLIANT_TRANSIENT` (Searches curated rulebooks with statutory citations; transient per project architecture).
- **Conflict Analysis:** `READ_ONLY` / `PERSISTENT_INPUT` (Detects differing advisory opinions across persisted advice).

### Domain F: Decisions & Dynamic Readiness
- **Human Compliance Decisions:** `PERSISTENT` (Saved in `decision.decisions`).
- **Decision Rationale & Follow-up:** `PERSISTENT` (Saved in `decision.decisions`).
- **Dynamic Readiness Evaluation:** `PERSISTENT` (Dynamically calculated from real counts in `regulatory_requirements`, `advice`, and `decisions`).

### Domain G: Audit History
- **Audit Event Stream:** `PERSISTENT` (Append-only immutable log in `audit.audit_events`).
- **Event Provenance:** `PERSISTENT` (Actor ID, project ID, entity type, entity ID, old/new values JSON).

### Domain H: Platform Administration & Tools
- **Admin Statistics:** `READ_ONLY` / `PERSISTENT` (Live database aggregate counts).
- **Admin User Management:** `PERSISTENT` (Toggles `identity.users.is_active`).
- **Trusted Ecosystem Tools:** `LOCAL_ONLY` (Catalog tool toggles stored in browser `localStorage`).
- **Notification Preferences:** `LOCAL_ONLY` (User UI preferences stored in browser `localStorage`).

---

## 5. Phase 4: Complete Frontend-to-Database Traceability Matrix

| Feature | Frontend component | Frontend service/API | Backend route | Backend service | PostgreSQL table(s) | Operation | Persisted after restart? | Evidence | Status |
|---|---|---|---|---|---|---|:---:|---|:---:|
| **User Registration** | `LoginForm.jsx` | `authService.registerUser` | `POST /api/v1/auth/register` | `auth_service.register_user` | `identity.users`, `identity.roles` | `INSERT` with bcrypt hash | **YES** | User ID 178 found in DB with `$2b$12$...` | `VERIFIED` |
| **User Login** | `LoginForm.jsx` | `authService.loginUser` | `POST /api/v1/auth/login` | `auth_service.authenticate_user` | `identity.users` | `SELECT` and bcrypt hash check | **YES** | Login succeeds after server reboot | `VERIFIED` |
| **User Profile Read** | `DashboardView.jsx` | `authService.getCurrentUser` | `GET /api/v1/users/me` | `get_current_user` dependency | `identity.users` | `SELECT` by decoded JWT ID | **YES** | Correct user profile retrieved | `VERIFIED` |
| **User Profile Update** | `SettingsView.jsx` | `userService.updateUserProfile` | `PATCH /api/v1/users/me` | `users.update_me` | `identity.users` | `UPDATE full_name` | **YES** | Modified name persists in DB | `VERIFIED` |
| **Project Creation** | `DashboardView.jsx` | `projectService.createProject` | `POST /api/v1/projects` | `project_service.create_project` | `project_management.projects`, `project_profiles`, `project_members` | Multi-table `INSERT` in single transaction | **YES** | Project 105 retrieved by ID and Code | `VERIFIED` |
| **Project Listing** | `DashboardView.jsx` | `projectService.getProjects` | `GET /api/v1/projects` | `project_service.list_user_projects` | `project_management.projects`, `project_members` | `SELECT` with membership filter | **YES** | Filtered project array returned | `VERIFIED` |
| **Project Details** | `DashboardView.jsx` | `projectService.getProjectDetails` | `GET /api/v1/projects/{id}` | `project_service.get_project_by_identifier` | `project_management.projects`, `project_profiles` | `SELECT` with ID/Code resolution | **YES** | Dual lookup succeeds | `VERIFIED` |
| **Add Requirement** | `DashboardView.jsx` | `adviceService.createProjectRequirement` | `POST /api/v1/projects/{id}/requirements` | `regulatory_service.create_project_requirement` | `regulatory.regulatory_requirements` | `INSERT` with FK check on `sources` | **YES** | Requirement 82 found in DB | `VERIFIED` |
| **List Requirements** | `DashboardView.jsx` | `adviceService.getProjectRequirements` | `GET /api/v1/projects/{id}/requirements` | `regulatory_service.list_project_requirements` | `regulatory.regulatory_requirements` | `SELECT` by `project_id` | **YES** | Requirements list rendered in UI | `VERIFIED` |
| **Regulatory Library** | `RegulatorySupportView.jsx` | `regulatoryService.getRegulatoryRequirements` | `GET /api/v1/regulatory-requirements` | `regulatory.get_global_regulatory_requirements` | `regulatory.regulatory_sources` | `SELECT * FROM regulatory_sources` | **YES** | 27 curated rulebooks returned | `VERIFIED` |
| **Advisor Directory** | `AdvisorsExpertsView.jsx` | `advisorService.getAdvisors` | `GET /api/v1/advisors` | `advisor_service.list_advisors` | `advisor_management.advisor_profiles`, `identity.users` | `SELECT` joined with `users` | **YES** | Verified advisor profiles returned | `VERIFIED` |
| **Invite Advisor** | `DashboardView.jsx` | `advisorService.sendAdvisorInvitation` | `POST /api/v1/projects/{id}/advisor-invitations` | `advisor_service.create_advisor_invitation` | `advisor_management.advisor_invitations`, `project_members` | `INSERT` with token & expiry | **YES** | Invitation 65 found in DB | `VERIFIED` |
| **Submit Advice** | `AdvisorDashboardView.jsx` | `adviceService.submitAdvice` | `POST /api/v1/projects/{id}/advice` | `advice_service.create_advice` | `advice.advice`, `advice_source_links` | `INSERT` advice and link rows | **YES** | Advice 65 found in DB | `VERIFIED` |
| **List Advice** | `DashboardView.jsx` | `adviceService.getProjectAdvice` | `GET /api/v1/projects/{id}/advice` | `advice_service.list_project_advice` | `advice.advice` | `SELECT` by `project_id` | **YES** | Advisor reviews rendered | `VERIFIED` |
| **Record Decision** | `DashboardView.jsx` | `adviceService.recordDecision` | `POST /api/v1/projects/{id}/decisions` | `decision_service.record_decision` | `decision.decisions` | `INSERT` with `decided_by` FK | **YES** | Decision 92 found in DB | `VERIFIED` |
| **Audit Readiness** | `DashboardView.jsx` | `adviceService.getProjectReadiness` | `GET /api/v1/projects/{id}/readiness` | `readiness_service.calculate_readiness` | `regulatory_requirements`, `advice`, `decisions` | Aggregate `SELECT COUNT` queries | **YES** | Dynamic readiness score computed | `VERIFIED` |
| **Audit Trail** | `DashboardView.jsx` | `auditService.getAuditEvents` | `GET /api/v1/projects/{id}/audit-events` | `audit_service.list_project_audit_events` | `audit.audit_events` | `SELECT` ordered by `created_at` | **YES** | 4 audit events retrieved after restart | `VERIFIED` |
| **Admin Stats** | `AdminDashboardView.jsx` | `adminService.getAdminStats` | `GET /api/v1/admin/stats` | `admin.get_admin_stats` | `identity.users`, `projects`, `sources`, `audit` | Multiple `SELECT COUNT(*)` | **YES** | Live DB stats rendered in Admin UI | `VERIFIED` |
| **Admin Toggle User** | `AdminDashboardView.jsx` | `adminService.updateUserStatus` | `PATCH /api/v1/admin/users/{id}/status` | `admin.toggle_user_status` | `identity.users` | `UPDATE is_active` | **YES** | Status change persists in DB | `VERIFIED` |
| **Trusted Tools** | `ToolsView.jsx` | `toolService.toggleToolUsage` | Client-side only | None | None | `localStorage.setItem('ecosystem_tools')` | **N/A (Local)** | Browser-local storage intentionally | `LOCAL_ONLY` |
| **Notification Prefs** | `SettingsView.jsx` | `userService.updateNotificationPreferences` | Client-side only | None | None | `localStorage.setItem('userNotificationPreferences')` | **N/A (Local)** | Browser-local preference cache | `LOCAL_ONLY` |

---

## 6. Audit Conclusion & Final Verdict

All critical business workflows — identity, project boundaries, regulatory provenance, advisory submissions, human ratification, dynamic readiness evaluation, and audit defensibility — are fully persistent in PostgreSQL 18.6 under the database `"FinRegTech ShipYard"`.

**FINAL VERDICT: DATABASE INTEGRATION VERIFIED**
