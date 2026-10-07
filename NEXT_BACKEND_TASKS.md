# FINREGTECH SHIPYARD – NEXT BACKEND TASKS & READINESS ASSESSMENT
**FCC Project Cockpit – Backend Engineering Action Plan**

* **Author:** Vishal S.R. (Backend & Workflow Engineer)  
* **Recipient:** Team & Teammate Harshini (Frontend Lead)  
* **Date:** September 29, 2026  
* **Current Sprint:** Week 4 (Regulatory Intelligence & Core Cockpit Slice)  
* **Backend Runtime:** Python 3.12.x | FastAPI | PostgreSQL / SQLite fallback  

---

## A. COMPLETED (Week 4 Scope)

1. **Runtime & Core Framework:**
   * Python runtime locked to **Python 3.12.x**.
   * FastAPI application initialized with CORS middleware supporting Next.js (`http://localhost:3000`, `http://localhost:5173`).
   * Unified error handling for HTTP exceptions, Pydantic validation errors (422), and unhandled server errors (500).
   * Health check endpoint at `GET /health`.

2. **Database & Multi-Schema Persistence:**
   * Dual-mode database session engine: PostgreSQL primary with automatic fallback to persistent schema-attached SQLite (`.sqlite_data/{schema}.db`) for offline resilience.
   * Preserved all 10 authoritative PostgreSQL schemas (`identity`, `project_management`, `advisor_management`, `regulatory`, `advice`, `ai`, `decision`, `readiness`, `audit`, `reporting`).
   * Strict adherence to zero-destructive migrations (no `Base.metadata.create_all()` against existing PostgreSQL).
   * Fully idempotent data seeder (`scripts/seed_data.py`).

3. **Authentication & Identity Flow:**
   * JWT Bearer token generation with 8-hour expiration (`POST /api/v1/auth/login`).
   * **2FA explicitly eliminated from scope** per specification.
   * User identity and context endpoint (`GET /api/v1/users/me`) returning user profile, platform role, and active project memberships.
   * Inactive user account deactivation enforcement (`403 Forbidden`).

4. **Two-Layer Role & Access Control (RBAC):**
   * Platform Roles enforced: `ADMIN`, `BUILDER`, `ADVISOR`.
   * Project Service Roles enforced: `OWNER`, `LEGAL`, `REGULATORY`, `TECH`, `FUNDING_BUSINESS`, `MARKETING`.
   * Canonical Service Scopes mapped: `PROJECT_CONTROL`, `LEGAL_ADVICE_SUPPORT`, `REGULATORY_ADVICE_SUPPORT`, `TECH_SOLUTION_SUPPORT`, etc.
   * **Platform Admin Project Isolation**: Platform `ADMIN` cannot access project-scoped data without an explicit active project membership.
   * Platform `ADVISOR` is strictly forbidden from holding the project `OWNER` role.

5. **Project Cockpit & Management APIs:**
   * `GET /api/v1/projects/summary`: Calculates aggregate dashboard counts strictly from authoritative database records.
   * `GET /api/v1/projects`: Filters projects at database query level by user's active memberships.
   * `POST /api/v1/projects`: Transactionally creates project, project profile, assigns creator as `OWNER`, and logs audit trail.
   * `GET /api/v1/projects/{projectId}` & `PATCH /api/v1/projects/{projectId}`: Scoped project details and updates.

6. **Project Team & Membership APIs:**
   * `GET /api/v1/projects/{projectId}/members`: Lists active project members.
   * `POST /api/v1/projects/{projectId}/members`: Assigns service roles (requires project `OWNER`).
   * `PATCH /api/v1/projects/{projectId}/members/{memberId}`: Updates service role or scope (requires project `OWNER`).
   * `DELETE /api/v1/projects/{projectId}/members/{memberId}`: Soft-revokes access. Prevents revoking the sole project `OWNER`.

7. **Advisor Directory & Invitations:**
   * `GET /api/v1/advisors` & `GET /api/v1/advisors/{advisorId}`: Public advisor registry with professional credentials and specializations.
   * `GET /api/v1/projects/{projectId}/advisor-invitations`: Lists project invitations.
   * `POST /api/v1/projects/{projectId}/advisor-invitations`: Issues secure advisor invitation token with expiration.
   * `POST /.../{invitationId}/resend` & `POST /.../{invitationId}/revoke`: Token refresh and revocation.

8. **Regulatory Sources & Compliance Requirements:**
   * 18 verified UK, EU, and International regulatory sources pre-seeded with publication dates, authorities, and official URLs.
   * `GET /api/v1/regulatory/sources`: Paginated corpus with jurisdiction, topic, and text search filters.
   * `GET /api/v1/projects/{projectId}/requirements`: Lists project requirements filtered by status or applicability.
   * `POST /api/v1/projects/{projectId}/requirements`: Maps requirements to approved sources. **Provenance validation** rejects unapproved source IDs with `404 Not Found`.
   * `PATCH /api/v1/projects/{projectId}/requirements/{requirementId}`: Updates requirement status and text.

9. **Grounded AI Copilot Retrieval Baseline:**
   * `POST /api/v1/projects/{projectId}/ai/retrieve`: Queries approved sources and requirements.
   * **Strict zero-fabrication rule**: Returns `GROUNDED_EVIDENCE_FOUND` with real citations when evidence matches; returns `NO_SOURCE_FOUND` with empty citations if no evidence matches.
   * Includes mandatory human review disclaimer.

10. **Immutable Audit Trail:**
    * `GET /api/v1/projects/{projectId}/audit-events`: Chronological event log with actor name, entity type, and diffs.
    * Server-side redaction of passwords, tokens, and secrets into `[REDACTED]`.

11. **Testing & Handoff Documentation:**
    * 33 automated tests passing in `pytest` (100% pass rate).
    * Comprehensive `FRONTEND_API_HANDOFF.md` created with 17 sections, TypeScript definitions (`types/api.ts`), and cURL examples.

---

## B. MUST DO NEXT (Immediate Priority for Integration)

These are the only tasks required before/during live pairing with Harshini:

1. **PostgreSQL Local User Configuration (Dev Environment Alignment):**
   * *Context:* The backend is currently running flawlessly on SQLite fallback mode because the dedicated PostgreSQL user `finreg_app` has not been granted a password on the local PostgreSQL 18 instance.
   * *Action:* In local `psql` (or pgAdmin) as superuser, run:
     ```sql
     CREATE USER finreg_app WITH PASSWORD 'finreg_secure_pass';
     GRANT ALL PRIVILEGES ON DATABASE "FinRegTech ShipYard" TO finreg_app;
     GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE "FinRegTech ShipYard" TO finreg_app;
     GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA identity, project_management, advisor_management, regulatory, advice, ai, decision, readiness, audit, reporting TO finreg_app;
     GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA identity, project_management, advisor_management, regulatory, advice, ai, decision, readiness, audit, reporting TO finreg_app;
     ```
   * *Verification:* Run `python scripts/seed_data.py` to seed PostgreSQL directly without seeing the SQLite fallback warning.

2. **Assist Harshini with Initial Frontend Client Connection:**
   * Ensure Harshini copies `FRONTEND_API_HANDOFF.md` into her frontend repo or references the types from `backend/FRONTEND_API_HANDOFF.md`.
   * Confirm Next.js `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`.
   * Verify the first end-to-end API call from Next.js (Login with `jun@finregtech.io` / `Password123!`).

---

## C. NICE TO HAVE (Low Priority / Post-Integration Enhancements)

1. **Alembic Migration Environment Verification:**
   * Ensure `alembic revision --autogenerate` matches the current schema state cleanly so future schema changes in Weeks 5–8 can be generated seamlessly.
2. **API Request Logging Middleware:**
   * Add execution-time logging middleware in FastAPI to trace request latencies (e.g. `X-Process-Time` header).
3. **Swagger UI Custom Tag Grouping:**
   * Group Swagger tags visually into "Identity & Auth", "Project Cockpit", "Regulatory Intelligence", and "AI Copilot".

---

## D. WEEK 5+ BACKLOG (DO NOT IMPLEMENT NOW)

Per official project boundaries, these domains must **NOT** be implemented during Week 4:

* **Week 5:** Formal Advisor Advice Sessions (`advice.advice_sessions`, `advice.advice_messages`, interactive messaging endpoints).
* **Week 6:** Automated Regulatory Readiness Scoring & Gap Evaluation Matrix (`readiness.evaluations`, `readiness.readiness_scores`).
* **Week 7:** Advisor Formal Sign-Offs & Decision Workflows (`decision.advisor_decisions`).
* **Week 8:** Audit Pack Exporters (PDF/CSV regulatory export endpoints and signed bundle generators).
* **Advanced Vector / RAG:** Vector database infrastructure (pgvector / Pinecone / ChromaDB) and continuous semantic indexing.

---

## E. FRONTEND BLOCKERS (What Harshini Currently Needs)

* **Current Blockers on Backend:** **NONE.**
* **Deliverables Provided to Harshini:**
  1. Base API URL: `http://localhost:8000/api/v1`
  2. Complete OpenAPI interactive docs: `http://localhost:8000/docs`
  3. Pre-seeded demo credentials for Builder (`jun@finregtech.io`), Advisors (`eleanor.vance@vancelegal.co.uk`, `marcus.reid@fccconsulting.eu`), and Admin (`admin@finregtech.io`).
  4. Authoritative Integration Specification: [FRONTEND_API_HANDOFF.md](file:///c:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/FRONTEND_API_HANDOFF.md)
  5. Copy-paste ready TypeScript types in `FRONTEND_API_HANDOFF.md` Section 14.

---

## F. FINAL STATUS

* **Backend Readiness:** `READY`  
  *All core models, RBAC, BOLA defense, regulatory corpus, requirements mapping, AI retrieval, and audit logging are implemented, tested, and operational.*

* **Frontend Integration:** `READY`  
  *All required endpoints, contracts, schemas, working cURL examples, CORS configurations, and TypeScript interfaces are delivered in `FRONTEND_API_HANDOFF.md`.*

* **Week 4 Milestone:** `COMPLETE`  
  *The Week 4 Regulatory Intelligence & Core Cockpit slice is 100% complete and verified against all team specifications.*
