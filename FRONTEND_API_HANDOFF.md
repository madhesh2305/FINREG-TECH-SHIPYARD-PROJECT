# FINREGTECH SHIPYARD – FRONTEND API INTEGRATION HANDOFF
**FCC Project Cockpit – Backend Integration Contract (Week 4 MVP)**

* **To:** Harshini (Frontend Lead – Next.js / React / TypeScript)  
* **From:** Vishal S.R. (Backend & Workflow Engineer)  
* **Project:** FinRegTech Shipyard – FCC Project Cockpit  
* **Backend Version:** `0.4.0` (Week 4 Integration & Regulatory Intelligence Slice)  
* **Runtime:** Python 3.12.x | FastAPI | PostgreSQL multi-schema / SQLite fallback  
* **Date:** September 2026  

---

## 1. Executive Summary & Architecture Overview

Harshini, this document serves as your complete, authoritative integration specification for connecting the existing Next.js frontend to the implemented FastAPI backend.

### Key Rules & Constraints Enforced:
1. **Zero Fabrication**: Every endpoint, schema, parameter, and response documented here is fully implemented, verified, and backed by a 100% passing automated test suite (`pytest`).
2. **Two-Layer Role Enforcement**:
   * **Platform Roles** (`ADMIN`, `BUILDER`, `ADVISOR`): Determine platform-wide access capabilities.
   * **Project Service Roles** (`OWNER`, `LEGAL`, `REGULATORY`, `TECH`, `FUNDING_BUSINESS`, `MARKETING`): Enforce access control within specific projects.
   * **Platform `ADMIN` does NOT bypass project-level isolation**: Platform admins cannot access project data unless they are actively assigned as a member of that project.
3. **Authentication**: Uses standard HTTP Bearer JWT tokens. **2FA is explicitly OUT OF SCOPE** and must not be rendered or called in your auth flows.
4. **BOLA / IDOR Defense**: All nested routes (requirements, members, invitations, audit logs) validate that the child object belongs to the `{projectId}` specified in the URL path.
5. **Grounded AI Intelligence**: Citations strictly reference approved regulatory sources with official publication URLs. If no evidence matches a query, the backend returns status `NO_SOURCE_FOUND` with an empty citation list.

---

## 2. Server Configuration & Local Environment

| Parameter | Configuration / Value |
| :--- | :--- |
| **Base API URL** | `http://localhost:8000/api/v1` |
| **Health Check** | `GET http://localhost:8000/health` |
| **Interactive Docs (Swagger UI)** | `http://localhost:8000/docs` |
| **Alternative Docs (ReDoc)** | `http://localhost:8000/redoc` |
| **OpenAPI Schema (JSON)** | `http://localhost:8000/openapi.json` |
| **Allowed CORS Origins** | `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`, `http://127.0.0.1:5173` |
| **CORS Credentials** | `true` (`allow_credentials=True`) |

### Frontend `.env.local` Configuration:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 3. Seeded Demo Accounts (Ready to Test)

The database seed script (`scripts/seed_data.py`) prepares the following accounts:

| Full Name | Email | Password | Platform Role | Initial Context |
| :--- | :--- | :--- | :--- | :--- |
| Full Name | Email | Password | Platform Role | Initial Context |
| :--- | :--- | :--- | :--- | :--- |
| **Jun Chen** | `jun@finregtech.io` | `Builder@123` or `Password123!` | `BUILDER` | Owner of **ABC Shield Compliance Infrastructure** (`PRJ-ABC-001`) |
| **Demo Builder** | `builder@gmail.com` | `builder` | `BUILDER` | Demo Builder profile matching `LoginForm.jsx` |
| **Demo Advisor** | `advisor@gmail.com` | `advisor` | `ADVISOR` | Demo Advisor profile matching `LoginForm.jsx` |
| **Eleanor Vance** | `eleanor.vance@vancelegal.co.uk` | `Password123!` | `ADVISOR` | Legal Advisor Profile (`Vance Legal LLP`), Head of Regulatory Practice |
| **Marcus Reid** | `marcus.reid@fccconsulting.eu` | `Password123!` | `ADVISOR` | FCC Advisor Profile (`FCC Consulting Europe`), Transaction Monitoring specialist |
| **Admin User** | `admin@finregtech.io` | `Password123!` | `ADMIN` | Platform Administrator |

---

## 4. Authentication & Identity Flow

Authentication uses JWT Bearer tokens with an 8-hour lifetime (`480 minutes`).

### 4.1 Login
* **Method & Path:** `POST /api/v1/auth/login`
* **Access:** Public (No authentication required)
* **Request Body:**
```json
{
  "email": "jun@finregtech.io",
  "password": "Builder@123"
}
```
* **Success Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user_id": 1,
  "full_name": "Jun Chen",
  "email": "jun@finregtech.io",
  "platform_role": "BUILDER"
}
```
* **Error Responses:**
  * `401 Unauthorized`: Invalid email or password.
  * `403 Forbidden`: Account is deactivated (`is_active: false`).
  * `422 Unprocessable Entity`: Invalid email format or password under 4 characters.

### 4.2 User Registration
* **Method & Path:** `POST /api/v1/auth/register`
* **Access:** Public (No authentication required)
* **Request Body:**
```json
{
  "email": "founder@payflow.io",
  "password": "SecurePassword123!",
  "full_name": "Sarah Connor",
  "role": "Builder",
  "organization": "PayFlow Technologies"
}
```
* **Success Response (`201 Created`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user_id": 8,
  "full_name": "Sarah Connor",
  "email": "founder@payflow.io",
  "platform_role": "BUILDER"
}
```
* **Error Responses:**
  * `409 Conflict`: User with email already exists.
  * `422 Unprocessable Entity`: Invalid role or malformed payload.

### 4.3 Current User Context
* **Method & Path:** `GET /api/v1/users/me`
* **Headers:** `Authorization: Bearer <access_token>`
* **Success Response (`200 OK`):**
```json
{
  "user_id": 1,
  "full_name": "Jun Chen",
  "email": "jun@finregtech.io",
  "is_active": true,
  "platform_role": "BUILDER",
  "memberships": [
    {
      "project_id": 1,
      "project_name": "ABC Shield Compliance Infrastructure",
      "project_code": "PRJ-ABC-001",
      "service_role": "OWNER",
      "service_scope": "PROJECT_CONTROL",
      "member_status": "ACTIVE"
    }
  ]
}
```

---

## 5. Role & Permission Matrix

### Platform Roles (Global)
* **`ADMIN`**: Platform monitoring, regulatory source curation. Cannot access projects without explicit project membership.
* **`BUILDER`**: Creates projects, manages teams, initiates advisor invitations, configures compliance requirements.
* **`ADVISOR`**: Subject matter expert. Accepts invitations, reviews requirements. Cannot create projects or hold project `OWNER` role.

### Project Service Roles (Project-Scoped)
Every member in a project holds an active service role:

| Project Service Role | Canonical Service Scope | Allowed Platform Roles | Capabilities |
| :--- | :--- | :--- | :--- |
| **`OWNER`** | `PROJECT_CONTROL` | `BUILDER`, `ADMIN` | Full project control: update profile, add/revoke members, issue/revoke advisor invitations. |
| **`LEGAL`** | `LEGAL_ADVICE_SUPPORT` | `BUILDER`, `ADVISOR` | Review legal requirements, provide regulatory interpretations. |
| **`REGULATORY`** | `REGULATORY_ADVICE_SUPPORT` | `BUILDER`, `ADVISOR` | Map requirements to regulatory sources, evaluate compliance criteria. |
| **`TECH`** | `TECH_SOLUTION_SUPPORT` | `BUILDER`, `ADVISOR` | Architect monitoring rules, travel rule APIs, data pipelines. |
| **`FUNDING_BUSINESS`** | `FUNDING_BUSINESS_SUPPORT` | `BUILDER`, `ADVISOR` | Commercial viability, investor compliance assurances. |
| **`MARKETING`** | `MARKETING_SUPPORT` | `BUILDER`, `ADVISOR` | External disclosures, consumer protection messaging. |

---

## 6. Project Cockpit APIs

Base Path: `/api/v1/projects`

### 6.1 Builder Dashboard Summary Metrics
* **Method & Path:** `GET /api/v1/projects/summary`
* **Access:** Authenticated User
* **Description:** Returns aggregate metrics calculated strictly from real database records across projects where the caller holds active membership.
* **Success Response (`200 OK`):**
```json
{
  "total_projects": 1,
  "active_projects": 1,
  "archived_projects": 0,
  "total_requirements": 8,
  "total_members": 1,
  "open_requirements": 3,
  "completed_requirements": 3
}
```

### 6.2 List Authorized Projects
* **Method & Path:** `GET /api/v1/projects`
* **Query Parameters:**
  * `status` (optional): `ACTIVE` or `ARCHIVED`
  * `search` (optional): Search string for project name or project code
* **Success Response (`200 OK`):**
```json
[
  {
    "project_id": 1,
    "project_name": "ABC Shield Compliance Infrastructure",
    "project_code": "PRJ-ABC-001",
    "status": "ACTIVE",
    "created_by": 1,
    "owner_name": "Jun Chen",
    "created_at": "2026-09-28T16:50:24.000Z",
    "updated_at": "2026-09-28T16:50:24.000Z",
    "profile": {
      "project_profile_id": 1,
      "project_id": 1,
      "description": "ABC Shield Compliance Infrastructure for UK Payment Institutions and E-Money Issuers.",
      "jurisdiction": "UK",
      "regulatory_scope": "UK Money Laundering Regulations 2017 (MLR 2017), FCA Senior Management Arrangements, Systems and Controls (SYSC), Proceeds of Crime Act 2002 (POCA)",
      "objectives": "Deliver an integrated AML transaction monitoring, KYC identity verification, and regulatory reporting cockpit.",
      "created_at": "2026-09-28T16:50:24.000Z",
      "updated_at": "2026-09-28T16:50:24.000Z"
    }
  }
]
```

### 6.3 Create Project
* **Method & Path:** `POST /api/v1/projects`
* **Access:** Restricted to `BUILDER` or `ADMIN`
* **Request Body:**
```json
{
  "project_name": "NextGen PayTech Compliance",
  "project_code": "PRJ-NGP-001",
  "description": "Pan-European payment orchestration and compliance hub.",
  "jurisdiction": "UK / EU",
  "regulatory_scope": "MLR 2017, 5AMLD, PSR 2017",
  "objectives": "Attain FCA authorized payment institution status."
}
```
* **Success Response (`201 Created`):** Returns the created `ProjectResponse` object. The creator is automatically registered as project `OWNER` with `PROJECT_CONTROL` scope, and an audit event is logged.

### 6.4 Get Project Details
* **Method & Path:** `GET /api/v1/projects/{projectId}`
* **Access:** Requires active membership in `{projectId}` (`403 Forbidden` if non-member)

### 6.5 Update Project
* **Method & Path:** `PATCH /api/v1/projects/{projectId}`
* **Access:** Requires project `OWNER` role (`403 Forbidden` if non-owner)
* **Request Body (all fields optional):**
```json
{
  "project_name": "Updated Project Name",
  "status": "ACTIVE",
  "description": "Updated description",
  "jurisdiction": "UK",
  "regulatory_scope": "Updated scope",
  "objectives": "Updated objectives"
}
```

---

## 7. Project Membership & Team Management APIs

Base Path: `/api/v1/projects/{projectId}/members`

### 7.1 List Project Members
* **Method & Path:** `GET /api/v1/projects/{projectId}/members`
* **Access:** Active project member
* **Success Response (`200 OK`):**
```json
[
  {
    "project_member_id": 1,
    "project_id": 1,
    "user_id": 1,
    "full_name": "Jun Chen",
    "email": "jun@finregtech.io",
    "platform_role": "BUILDER",
    "service_role": "OWNER",
    "service_scope": "PROJECT_CONTROL",
    "member_status": "ACTIVE",
    "joined_at": "2026-09-28T16:50:24.000Z"
  }
]
```

### 7.2 Add Project Member
* **Method & Path:** `POST /api/v1/projects/{projectId}/members`
* **Access:** Project `OWNER`
* **Request Body:**
```json
{
  "user_id": 2,
  "service_role": "LEGAL",
  "service_scope": "LEGAL_ADVICE_SUPPORT"
}
```
* **Validation Rules:**
  * Target user must exist (`404 Not Found`).
  * If user is already an active member, returns `409 Conflict`.
  * If user was previously `REVOKED`, status is updated back to `ACTIVE`.
  * Platform `ADVISOR` cannot be given `OWNER` service role (`403 Forbidden`).

### 7.3 Update Member
* **Method & Path:** `PATCH /api/v1/projects/{projectId}/members/{memberId}`
* **Access:** Project `OWNER`
* **Request Body:**
```json
{
  "service_role": "REGULATORY",
  "service_scope": "REGULATORY_ADVICE_SUPPORT",
  "member_status": "ACTIVE"
}
```

### 7.4 Revoke Member
* **Method & Path:** `DELETE /api/v1/projects/{projectId}/members/{memberId}`
* **Access:** Project `OWNER`
* **Rule:** Soft-revokes access (`member_status` set to `REVOKED`). The sole project `OWNER` cannot be revoked (`403 Forbidden`).

---

## 8. Advisor Directory & Project Advisor Invitations

### 8.1 Global Advisor Directory
* **Method & Path:** `GET /api/v1/advisors`
* **Access:** Authenticated User
* **Success Response (`200 OK`):**
```json
[
  {
    "advisor_profile_id": 1,
    "user_id": 2,
    "full_name": "Eleanor Vance",
    "email": "eleanor.vance@vancelegal.co.uk",
    "organization_name": "Vance Legal LLP",
    "professional_title": "Partner & Head of Financial Regulatory Practice",
    "specialization": "UK & EU Anti-Money Laundering, Senior Managers & Certification Regime (SM&CR), FinTech Licensing",
    "bio": "Senior regulatory counsel with over 16 years advising tier-1 UK and European payments firms...",
    "created_at": "2026-09-28T16:50:24.000Z",
    "updated_at": "2026-09-28T16:50:24.000Z"
  }
]
```

### 8.2 Get Advisor Profile
* **Method & Path:** `GET /api/v1/advisors/{advisorId}`

### 8.3 List Project Advisor Invitations
* **Method & Path:** `GET /api/v1/projects/{projectId}/advisor-invitations`
* **Access:** Active project member

### 8.4 Invite Advisor to Project
* **Method & Path:** `POST /api/v1/projects/{projectId}/advisor-invitations`
* **Access:** Project `OWNER`
* **Request Body:**
```json
{
  "advisor_email": "eleanor.vance@vancelegal.co.uk",
  "access_level": "LEGAL",
  "expiry_days": 14
}
```
* **Success Response (`201 Created`):**
```json
{
  "invitation_id": 1,
  "project_id": 1,
  "invited_by": 1,
  "advisor_email": "eleanor.vance@vancelegal.co.uk",
  "access_level": "LEGAL",
  "invitation_status": "PENDING",
  "invitation_token": "j9s8d7f6a5s4d3f2...",
  "expires_at": "2026-10-12T16:50:24.000Z",
  "accepted_at": null,
  "revoked_at": null,
  "created_at": "2026-09-28T16:50:24.000Z"
}
```

### 8.5 Resend / Refresh Invitation
* **Method & Path:** `POST /api/v1/projects/{projectId}/advisor-invitations/{invitationId}/resend`
* **Access:** Project `OWNER`

### 8.6 Revoke Invitation
* **Method & Path:** `POST /api/v1/projects/{projectId}/advisor-invitations/{invitationId}/revoke`
* **Access:** Project `OWNER`

---

## 9. Regulatory Intelligence & Sources APIs

### 9.1 Global Regulatory Sources Corpus (18 Verified Sources Pre-Seeded)
* **Method & Path:** `GET /api/v1/regulatory/sources`
* **Query Parameters:**
  * `jurisdiction`: e.g. `UK`, `EU`, `International`
  * `topic`: e.g. `AML`, `Sanctions`, `Travel Rule`
  * `search`: Free text search across title, authority, and relevance
  * `page`: Default `1`
  * `page_size`: Default `20` (max 100)
* **Success Response (`200 OK`):**
```json
{
  "items": [
    {
      "source_id": 1,
      "source_title": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
      "issuing_authority": "HM Treasury / UK Parliament",
      "jurisdiction": "UK",
      "source_url": "https://www.legislation.gov.uk/uksi/2017/692/contents/made",
      "version_label": "SI 2017/692 as amended",
      "publication_date": "2017-06-22",
      "validation_status": "VALIDATED",
      "topic": "AML / Customer Due Diligence (CDD)",
      "relevance": "Primary UK statutory framework establishing mandatory policies, controls, risk assessments...",
      "applicability_rationale": "Mandatory statutory compliance baseline for all UK credit and financial institutions...",
      "retrieved_at": "2026-09-28T16:50:24.000Z",
      "created_at": "2026-09-28T16:50:24.000Z",
      "updated_at": "2026-09-28T16:50:24.000Z"
    }
  ],
  "total": 18,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### 9.2 Get Single Regulatory Source
* **Method & Path:** `GET /api/v1/regulatory/sources/{sourceId}`

### 9.3 Register New Regulatory Source
* **Method & Path:** `POST /api/v1/regulatory/sources`
* **Access:** Restricted to `ADMIN` or `BUILDER`

### 9.4 List Project Regulatory Requirements
* **Method & Path:** `GET /api/v1/projects/{projectId}/requirements`
* **Access:** Active project member
* **Query Parameters:**
  * `status`: `OPEN`, `IN_REVIEW`, `COMPLETED`, `BLOCKED`
  * `applicability`: `APPLICABLE`, `NOT_APPLICABLE`, `UNDER_REVIEW`
* **Success Response (`200 OK`):**
```json
[
  {
    "requirement_id": 1,
    "project_id": 1,
    "source_id": 1,
    "requirement_code": "REQ-ABC-001",
    "requirement_title": "Customer Due Diligence (CDD) Verification Before Account Activation",
    "requirement_text": "The platform must verify the customer's identity before establishing a business relationship...",
    "applicability_status": "APPLICABLE",
    "requirement_status": "COMPLETED",
    "created_at": "2026-09-28T16:50:24.000Z",
    "updated_at": "2026-09-28T16:50:24.000Z",
    "source": {
      "source_id": 1,
      "source_title": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
      "issuing_authority": "HM Treasury / UK Parliament",
      "jurisdiction": "UK",
      "source_url": "https://www.legislation.gov.uk/uksi/2017/692/contents/made",
      "version_label": "SI 2017/692 as amended",
      "publication_date": "2017-06-22",
      "validation_status": "VALIDATED",
      "topic": "AML / Customer Due Diligence (CDD)",
      "relevance": "Primary UK statutory framework...",
      "applicability_rationale": "Mandatory statutory compliance baseline...",
      "retrieved_at": "2026-09-28T16:50:24.000Z",
      "created_at": "2026-09-28T16:50:24.000Z",
      "updated_at": "2026-09-28T16:50:24.000Z"
    }
  }
]
```

### 9.5 Map New Project Requirement
* **Method & Path:** `POST /api/v1/projects/{projectId}/requirements`
* **Access:** Active project member
* **Request Body:**
```json
{
  "source_id": 1,
  "requirement_code": "REQ-ABC-009",
  "requirement_title": "Automated PEP Screening Hook",
  "requirement_text": "Integrate PEP database webhook for onboarding check.",
  "applicability_status": "APPLICABLE",
  "requirement_status": "OPEN"
}
```
* **Provenance Verification:** If `source_id` does not match an existing validated source, the backend rejects the request with `404 Not Found` (`Approved Regulatory Source with ID X does not exist`).

### 9.6 Update Project Requirement
* **Method & Path:** `PATCH /api/v1/projects/{projectId}/requirements/{requirementId}`
* **Access:** Active project member
* **Request Body (all optional):**
```json
{
  "requirement_title": "Updated Title",
  "requirement_text": "Updated text",
  "applicability_status": "APPLICABLE",
  "requirement_status": "COMPLETED"
}
```

---

## 10. Grounded AI Copilot Retrieval Endpoint

* **Method & Path:** `POST /api/v1/projects/{projectId}/ai/retrieve`
* **Access:** Active project member
* **Request Body:**
```json
{
  "query": "transaction monitoring velocity rules",
  "top_k": 3
}
```

### When Grounded Evidence Exists:
```json
{
  "query": "transaction monitoring velocity rules",
  "status": "GROUNDED_EVIDENCE_FOUND",
  "citations": [
    {
      "source_id": 3,
      "source_title": "FCA Handbook: SYSC 6.1 & 6.3 Financial Crime Systems and Controls",
      "issuing_authority": "Financial Conduct Authority (FCA)",
      "jurisdiction": "UK",
      "source_url": "https://www.handbook.fca.org.uk/handbook/SYSC/6/3.html",
      "topic": "Systems & Controls / MLRO Oversight",
      "applicability_rationale": "Core regulatory requirement for authorized UK FinTechs and payment institutions under FCA supervision.",
      "relevance_summary": "Requires regulated firms to establish and maintain effective systems and controls to counter the risk that they might be used to further financial crime..."
    }
  ],
  "disclaimer": "AI retrieval provides source citations for human review. It does not provide legal advice or regulatory certification."
}
```

### When No Evidence Exists (Zero Fabrication Guarantee):
```json
{
  "query": "quantum mechanical propulsion orbital mechanics",
  "status": "NO_SOURCE_FOUND",
  "citations": [],
  "disclaimer": "AI retrieval provides source citations for human review. It does not provide legal advice or regulatory certification."
}
```
* **Frontend Implementation Note:** Render the `disclaimer` prominently next to AI responses. Do not claim zero hallucinations or legal certification.

---

## 11. Immutable Audit Trail APIs

* **Method & Path:** `GET /api/v1/projects/{projectId}/audit-events`
* **Access:** Active project member
* **Query Parameters:**
  * `event_type`: Filter by type (e.g. `PROJECT_CREATED`, `MEMBER_ADDED`, `REQUIREMENT_CREATED`)
  * `limit`: Max records to return (default `100`, max `500`)
* **Success Response (`200 OK`):**
```json
[
  {
    "audit_event_id": 1,
    "project_id": 1,
    "actor_user_id": 1,
    "actor_name": "Jun Chen",
    "event_type": "PROJECT_CREATED",
    "entity_type": "PROJECT",
    "entity_id": 1,
    "old_values": {},
    "new_values": {
      "project_name": "ABC Shield Compliance Infrastructure",
      "project_code": "PRJ-ABC-001",
      "status": "ACTIVE",
      "created_by": 1
    },
    "event_description": "Project 'ABC Shield Compliance Infrastructure' created with code 'PRJ-ABC-001'",
    "created_at": "2026-09-28T16:50:24.000Z"
  }
]
```
* **Security Redaction:** Passwords, tokens, and secret parameters are automatically scrubbed into `[REDACTED]` server-side before persisting in the audit ledger.

---

---

## 12. Project Advisory Opinions & Review Lifecycle (Week 5)

Advisors provide formal opinions with citations to approved regulatory sources, and project owners can review, accept, or request clarification.

### 12.1 Submit Advisory Review
* **Method & Path:** `POST /api/v1/projects/{projectId}/advice`
* **Access:** Project member with `ADVISOR` platform role (or advisory profile)
* **Request Body:**
```json
{
  "title": "Customer Due Diligence (CDD) Control Design Review",
  "advice_text": "The control design covers standard CDD, but EDD triggers must be explicit for complex ownership structures.",
  "recommendation": "Implement additional verification steps for high-risk corporate customers with beneficial ownership above 25%.",
  "assumptions": "Based on UK MLR 2017 Regulation 33 guidance.",
  "advice_status": "SUBMITTED",
  "source_links": [
    {
      "source_id": 1,
      "reference_note": "MLR 2017 Regulation 33 enhanced customer due diligence obligations"
    }
  ]
}
```
* **Success Response (`201 Created`):**
```json
{
  "advice_id": 1,
  "project_id": 1,
  "advisor_profile_id": 1,
  "advisor_name": "Eleanor Vance",
  "advisor_organization": "Vance Legal LLP",
  "title": "Customer Due Diligence (CDD) Control Design Review",
  "advice_text": "The control design covers standard CDD, but EDD triggers must be explicit for complex ownership structures.",
  "recommendation": "Implement additional verification steps for high-risk corporate customers with beneficial ownership above 25%.",
  "assumptions": "Based on UK MLR 2017 Regulation 33 guidance.",
  "advice_status": "SUBMITTED",
  "display_status": "Pending Review",
  "submitted_at": "2026-10-07T17:15:00.000Z",
  "updated_at": "2026-10-07T17:15:00.000Z",
  "source_links": [
    {
      "advice_source_link_id": 1,
      "source_id": 1,
      "reference_note": "MLR 2017 Regulation 33 enhanced customer due diligence obligations",
      "source_title": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
      "citation_reference": "SI 2017/692",
      "created_at": "2026-10-07T17:15:00.000Z"
    }
  ]
}
```

### 12.2 List Project Advisory Reviews
* **Method & Path:** `GET /api/v1/projects/{projectId}/advice`
* **Access:** Project member
* **Query Parameters:** `status` (`DRAFT`, `SUBMITTED`, `REVIEWED`, `ARCHIVED`)
* **Success Response (`200 OK`):** Array of `AdviceResponse` objects.

### 12.3 Update Advice / Review Status Transition
* **Method & Path:** `PATCH /api/v1/projects/{projectId}/advice/{adviceId}`
* **Access:** Project member (Owner can accept/review; author can edit)
* **Request Body:**
```json
{
  "advice_status": "REVIEWED"
}
```
* Status values automatically map to frontend labels:
  * `SUBMITTED` -> `"Pending Review"`
  * `REVIEWED` -> `"Accepted"`
  * `DRAFT` -> `"Needs Clarification"`

---

## 13. Project Owner Compliance Decisions (Week 5)

Project owners record binding compliance decisions with executive rationale and operational follow-ups. Every decision generates an immutable entry in the audit trail.

### 13.1 Record Compliance Decision
* **Method & Path:** `POST /api/v1/projects/{projectId}/decisions`
* **Access:** Project `OWNER` only
* **Request Body:**
```json
{
  "decision_type": "ACCEPT",
  "decision_rationale": "Accepted advisor recommendation to enforce mandatory EDD for beneficial ownership exceeding 25%.",
  "follow_up_action": "Incorporate enhanced threshold checks in Sprint 5 onboarding pipeline.",
  "conflict_gap_id": null
}
```
* **Allowed Decision Types:** `ACCEPT`, `REJECT`, `REVIEW_REQUIRED`, `FOLLOW_UP_REQUIRED`
* **Success Response (`201 Created`):**
```json
{
  "decision_id": 1,
  "project_id": 1,
  "conflict_gap_id": null,
  "decided_by": 1,
  "decider_name": "Jun Chen",
  "decider_email": "jun@finregtech.io",
  "decision_type": "ACCEPT",
  "decision_rationale": "Accepted advisor recommendation to enforce mandatory EDD for beneficial ownership exceeding 25%.",
  "follow_up_action": "Incorporate enhanced threshold checks in Sprint 5 onboarding pipeline.",
  "created_at": "2026-10-07T17:20:00.000Z"
}
```

### 13.2 List Compliance Decisions
* **Method & Path:** `GET /api/v1/projects/{projectId}/decisions`
* **Access:** Project member
* **Success Response (`200 OK`):** Array of `DecisionResponse` objects.

---

## 14. Remaining Unimplemented Domains (Weeks 6–8 Roadmap)

| Domain | Underlying Database Schema | Target Week | Frontend Guidance |
| :--- | :--- | :--- | :--- |
| **Readiness Evaluations & Scoring** | `readiness.evaluations`, `readiness.readiness_scores` | Week 6 | Use static progress rings or mock evaluation data. |
| **Audit Pack CSV/PDF Exporters** | `reporting.audit_exports` | Week 8 | Retain export button in disabled or mock state. |

---

## 13. Standard Error Format & Status Codes

All errors conform to this unified JSON structure:

```json
{
  "detail": "Action requires project service role: OWNER (your role: LEGAL)",
  "errors": null
}
```

When payload validation fails (`422 Unprocessable Entity`), structured field details are returned:
```json
{
  "detail": "Request payload validation failed",
  "errors": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

### HTTP Status Code Reference:
* `400 Bad Request`: General malformed request.
* `401 Unauthorized`: Missing or invalid Bearer token / Bad credentials.
* `403 Forbidden`: Insufficient role or cross-project access violation.
* `404 Not Found`: Project, member, requirement, or source ID does not exist.
* `409 Conflict`: Unique constraint violation (e.g. duplicate member or project code).
* `422 Unprocessable Entity`: Request body failed schema validation.
* `500 Internal Server Error`: Unhandled server exception (logged with stack trace).

---

## 14. TypeScript Interface Definitions (`types/api.ts`)

Copy and paste these definitions directly into your frontend code:

```typescript
// ==========================================
// User & Auth Types
// ==========================================

export type PlatformRole = "ADMIN" | "BUILDER" | "ADVISOR";

export type ProjectServiceRole = 
  | "OWNER" 
  | "LEGAL" 
  | "REGULATORY" 
  | "TECH" 
  | "FUNDING_BUSINESS" 
  | "MARKETING";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user_id: number;
  full_name: string;
  email: string;
  platform_role: PlatformRole;
}

export interface UserMembershipContext {
  project_id: number;
  project_name: string;
  project_code: string;
  service_role: ProjectServiceRole;
  service_scope: string;
  member_status: "ACTIVE" | "REVOKED";
}

export interface CurrentUserContext {
  user_id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  platform_role: PlatformRole;
  memberships: UserMembershipContext[];
}

// ==========================================
// Project Cockpit Types
// ==========================================

export interface ProjectProfile {
  project_profile_id: number;
  project_id: number;
  description: string;
  jurisdiction: string;
  regulatory_scope: string;
  objectives: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectResponse {
  project_id: number;
  project_name: string;
  project_code: string;
  status: "ACTIVE" | "ARCHIVED";
  created_by: number;
  owner_name?: string;
  created_at: string;
  updated_at: string;
  profile?: ProjectProfile;
}

export interface ProjectCreate {
  project_name: string;
  project_code: string;
  description: string;
  jurisdiction?: string;
  regulatory_scope?: string;
  objectives?: string;
}

export interface ProjectUpdate {
  project_name?: string;
  status?: "ACTIVE" | "ARCHIVED";
  description?: string;
  jurisdiction?: string;
  regulatory_scope?: string;
  objectives?: string;
}

export interface DashboardSummary {
  total_projects: number;
  active_projects: number;
  archived_projects: number;
  total_requirements: number;
  total_members: number;
  open_requirements: number;
  completed_requirements: number;
}

// ==========================================
// Member Types
// ==========================================

export interface MemberResponse {
  project_member_id: number;
  project_id: number;
  user_id: number;
  full_name: string;
  email: string;
  platform_role: PlatformRole;
  service_role: ProjectServiceRole;
  service_scope: string;
  member_status: "ACTIVE" | "REVOKED";
  joined_at: string;
}

export interface MemberCreate {
  user_id: number;
  service_role: ProjectServiceRole;
  service_scope?: string;
}

export interface MemberUpdate {
  service_role?: ProjectServiceRole;
  service_scope?: string;
  member_status?: "ACTIVE" | "REVOKED";
}

// ==========================================
// Advisor & Invitation Types
// ==========================================

export interface AdvisorProfileResponse {
  advisor_profile_id: number;
  user_id: number;
  full_name: string;
  email: string;
  organization_name: string;
  professional_title: string;
  specialization: string;
  bio: string;
  created_at: string;
  updated_at: string;
}

export interface AdvisorInvitationCreate {
  advisor_email: string;
  access_level: ProjectServiceRole;
  expiry_days?: number;
}

export interface AdvisorInvitationResponse {
  invitation_id: number;
  project_id: number;
  invited_by: number;
  advisor_email: string;
  access_level: string;
  invitation_status: "PENDING" | "ACCEPTED" | "REVOKED" | "EXPIRED";
  invitation_token: string;
  expires_at: string;
  accepted_at?: string;
  revoked_at?: string;
  created_at: string;
}

// ==========================================
// Regulatory Sources & Requirements
// ==========================================

export interface RegulatorySourceResponse {
  source_id: number;
  source_title: string;
  issuing_authority: string;
  jurisdiction: string;
  source_url: string;
  version_label: string;
  publication_date: string;
  validation_status: "PENDING" | "VALIDATED" | "REJECTED";
  topic: string;
  relevance: string;
  applicability_rationale: string;
  retrieved_at: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedSourcesResponse {
  items: RegulatorySourceResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface RegulatoryRequirementResponse {
  requirement_id: number;
  project_id: number;
  source_id: number;
  requirement_code: string;
  requirement_title: string;
  requirement_text: string;
  applicability_status: "APPLICABLE" | "NOT_APPLICABLE" | "UNDER_REVIEW";
  requirement_status: "OPEN" | "IN_REVIEW" | "COMPLETED" | "BLOCKED";
  created_at: string;
  updated_at: string;
  source?: RegulatorySourceResponse;
}

export interface RegulatoryRequirementCreate {
  source_id: number;
  requirement_code: string;
  requirement_title: string;
  requirement_text: string;
  applicability_status?: "APPLICABLE" | "NOT_APPLICABLE" | "UNDER_REVIEW";
  requirement_status?: "OPEN" | "IN_REVIEW" | "COMPLETED" | "BLOCKED";
}

export interface RegulatoryRequirementUpdate {
  requirement_title?: string;
  requirement_text?: string;
  applicability_status?: "APPLICABLE" | "NOT_APPLICABLE" | "UNDER_REVIEW";
  requirement_status?: "OPEN" | "IN_REVIEW" | "COMPLETED" | "BLOCKED";
}

// ==========================================
// AI Copilot & Audit Types
// ==========================================

export interface CitationItem {
  source_id: number;
  source_title: string;
  issuing_authority: string;
  jurisdiction: string;
  source_url: string;
  topic: string;
  applicability_rationale: string;
  relevance_summary: string;
}

export interface RetrievalResponse {
  query: string;
  status: "GROUNDED_EVIDENCE_FOUND" | "NO_SOURCE_FOUND";
  citations: CitationItem[];
  disclaimer: string;
}

export interface AuditEventResponse {
  audit_event_id: number;
  project_id: number;
  actor_user_id: number;
  actor_name?: string;
  event_type: string;
  entity_type: string;
  entity_id: number;
  old_values: Record<string, unknown>;
  new_values: Record<string, unknown>;
  event_description: string;
  created_at: string;
}
```

---

## 15. Working cURL Command Examples

### 15.1 Authenticate and Extract Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"jun@finregtech.io","password":"Password123!"}'
```

### 15.2 Get Builder Summary Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/projects/summary" \
  -H "Authorization: Bearer <TOKEN>"
```

### 15.3 Query Regulatory Corpus for "Sanctions"
```bash
curl -X GET "http://localhost:8000/api/v1/regulatory/sources?topic=Sanctions&page=1&page_size=5" \
  -H "Authorization: Bearer <TOKEN>"
```

### 15.4 Grounded AI Query
```bash
curl -X POST "http://localhost:8000/api/v1/projects/1/ai/retrieve" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"sanctions screening and asset freezing","top_k":2}'
```

### 15.5 Inspect Project Audit Trail
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/audit-events?limit=10" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 16. How to Run and Verify the Backend Locally

If you need to start or restart the backend service locally:

1. **Open terminal in the `backend/` directory:**
   ```bash
   cd backend
   ```
2. **Install dependencies (Python 3.12.x):**
   ```bash
   pip install -r requirements.txt
   ```
3. **Seed database (idempotent, populates roles, accounts, ABC Shield project, 18 sources):**
   ```bash
   python scripts/seed_data.py
   ```
4. **Start the API server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. **Verify in your browser:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) to access the interactive Swagger documentation.

---

## 17. Frontend Integration Checklist for Harshini

- [ ] Configure `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.
- [ ] Connect the login form to `POST /api/v1/auth/login` and store `access_token` in secure client state / HTTP cookie.
- [ ] Add `Authorization: Bearer <access_token>` to all downstream API requests.
- [ ] Ensure **NO 2FA step or modal** is triggered during user authentication.
- [ ] Connect the Dashboard Header and Stats widget to `GET /api/v1/projects/summary`.
- [ ] Connect the Projects List view to `GET /api/v1/projects`.
- [ ] Connect the Project Creation modal to `POST /api/v1/projects`.
- [ ] Connect the Team Members tab to `GET /api/v1/projects/{projectId}/members` and `POST /api/v1/projects/{projectId}/members`.
- [ ] Connect the Advisor Directory to `GET /api/v1/advisors` and the Invitation modal to `POST /api/v1/projects/{projectId}/advisor-invitations`.
- [ ] Connect the Regulatory Sources tab to `GET /api/v1/regulatory/sources` and Requirements to `GET /api/v1/projects/{projectId}/requirements`.
- [ ] Connect the AI Copilot chat / search bar to `POST /api/v1/projects/{projectId}/ai/retrieve`. Ensure the returned `disclaimer` is displayed.
- [ ] Leave Weeks 5–8 domains (Advice Sessions, Readiness Scoring, Decisions, Exporting) in mock / disabled state.
