# FINREGTECH SHIPYARD – FRONTEND INTEGRATION STATUS & ISSUES LOG
**FCC Project Cockpit – Integration Assessment for Harshini**

* **Author:** Vishal S.R. (Backend & Workflow Engineer)  
* **Recipient:** Harshini (Frontend Lead – Next.js / React / TypeScript)  
* **Backend API Base:** `http://localhost:8000/api/v1`  
* **Date:** September 29, 2026  
* **Verification Method:** Live TCP network requests with `Origin: http://localhost:3000` against active Uvicorn daemon  

---

## 1. Executive Summary & Integration Assessment

The backend API is running, verified, and 100% compliant with the Week 4 contract. All 10 real HTTP flows were executed over the network and returned `200 OK` / `201 Created` with valid CORS headers for `http://localhost:3000`.

### Overall Frontend Connection Status: **NOT CONNECTED (Repository Missing from Workspace)**
* **Root Cause:** The workspace `FinRegTechnology ShipYard` currently contains only the `backend/` directory. Harshini's Next.js frontend repository has not yet been merged or cloned into this workspace.
* **Impact:** Once Harshini places the Next.js project alongside `backend/` or points her independent development server to `http://localhost:8000/api/v1`, the flows below define the exact connection requirements and potential integration pitfalls.

---

## 2. Integration Status by Flow

| Frontend Flow | Backend Endpoint | Status | Problem | Required Fix |
| :--- | :--- | :--- | :--- | :--- |
| **LOGIN** | `POST /api/v1/auth/login` | **NOT CONNECTED** | Frontend repo not in local workspace. Potential risk: frontend sending `form-data` instead of JSON, or attempting a 2FA challenge. | Ensure Next.js sends JSON body `{ "email": string, "password": string }`. Store `access_token` in secure cookie or client state. Do **NOT** invoke any 2FA flow. |
| **USER PROFILE** | `GET /api/v1/users/me` | **NOT CONNECTED** | Token must be extracted from login response and passed in header. | Attach `Authorization: Bearer <access_token>`. Expect response containing `platform_role` and `memberships` array. |
| **BUILDER DASHBOARD** | `GET /api/v1/projects/summary` | **NOT CONNECTED** | Frontend may attempt to compute metrics locally or hit unimplemented endpoints. | Call `GET /api/v1/projects/summary` directly. Bind UI cards to `total_projects`, `active_projects`, `total_requirements`, `total_members`, etc. |
| **MY PROJECTS** | `GET /api/v1/projects` | **NOT CONNECTED** | Frontend may expect cross-project visibility or unrestricted listing. | Call `GET /api/v1/projects`. Note that the backend returns only projects where the user is an active member. |
| **PROJECT DETAILS** | `GET /api/v1/projects/{projectId}` | **NOT CONNECTED** | Route path parameter mismatch risk (`projectId` must be an integer). | Ensure Next.js router passes numeric `projectId` (e.g. `/projects/1`). Caller must be an active project member. |
| **CREATE PROJECT** | `POST /api/v1/projects` | **NOT CONNECTED** | Payload schema mismatch risk (e.g. missing `project_code`). | Send `{ "project_name": string, "project_code": string, "description": string, "jurisdiction": string, "regulatory_scope": string, "objectives": string }`. Creator is auto-assigned as `OWNER`. |
| **PROJECT MEMBERS** | `GET /api/v1/projects/{projectId}/members` | **NOT CONNECTED** | Frontend may display service roles differently than backend enum. | Render valid service roles: `OWNER`, `LEGAL`, `REGULATORY`, `TECH`, `FUNDING_BUSINESS`, `MARKETING`. Service scope is auto-populated if omitted. |
| **ADVISOR DIRECTORY** | `GET /api/v1/advisors` | **NOT CONNECTED** | Frontend may look for advisors scoped under project instead of global registry. | Fetch public advisor registry from `GET /api/v1/advisors`. Use `POST /api/v1/projects/{projectId}/advisor-invitations` to invite an advisor. |
| **ADVISOR INVITATIONS** | `GET /api/v1/projects/{projectId}/advisor-invitations` | **NOT CONNECTED** | Frontend may try to directly create memberships for advisors without invitation tokens. | Follow invitation flow: Builder creates invitation token $\rightarrow$ Advisor accepts token $\rightarrow$ Membership activated. |
| **REGULATORY SOURCES** | `GET /api/v1/regulatory/sources` | **NOT CONNECTED** | Response is paginated (`{ items: [...], total, page, page_size, pages }`). Frontend might expect a plain array. | Parse `response.data.items` for sources array and `response.data.total` for pagination controls. |
| **PROJECT REQUIREMENTS** | `GET /api/v1/projects/{projectId}/requirements` | **NOT CONNECTED** | Requirement creation must link to a valid source (`source_id`). | In creation modal, provide dropdown of existing sources from `GET /regulatory/sources`. Backend returns `404 Not Found` if `source_id` is invalid. |
| **AUDIT TRAIL** | `GET /api/v1/projects/{projectId}/audit-events` | **NOT CONNECTED** | Frontend may expect sensitive keys like raw tokens. | All passwords and tokens are redacted to `[REDACTED]`. Render `event_type`, `event_description`, `actor_name`, and `created_at`. |
| **GROUNDED AI COPILOT** | `POST /api/v1/projects/{projectId}/ai/retrieve` | **NOT CONNECTED** | Frontend might expect conversational markdown instead of structured citations. | Send `{ "query": string, "top_k": number }`. Render `status` (`GROUNDED_EVIDENCE_FOUND` or `NO_SOURCE_FOUND`), `citations` list, and mandatory `disclaimer`. |

---

## 3. Potential Integration Pitfalls & Solutions for Harshini

### 1. API Base URL Suffix:
* **Common Mistake:** Setting `NEXT_PUBLIC_API_URL=http://localhost:8000` (missing `/api/v1`).
* **Solution:** Must be configured as:
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  ```

### 2. Authorization Header Formatting:
* **Common Mistake:** Sending `Token <jwt>` or omitting the space in `Bearer <jwt>`.
* **Solution:** Axios/Fetch interceptor should format exactly:
  ```typescript
  config.headers.Authorization = `Bearer ${token}`;
  ```

### 3. Paginated vs. Flat List Responses:
* **Sources API:** `GET /api/v1/regulatory/sources` returns an object: `{ items: [...], total: 18, page: 1, page_size: 20, pages: 1 }`.
* **Projects / Requirements / Members / Audit APIs:** Return direct arrays `[...]`.

### 4. Zero 2FA Requirement:
* The backend does **not** implement 2FA. Harshini must bypass or remove any multi-factor authentication steps, SMS verification modals, or authenticator app prompts.

### 5. Out-of-Scope Domains (Weeks 5–8):
* Do **not** fire requests to `/advice/*`, `/readiness/*`, `/decisions/*`, or `/exports/*`. Keep those views in static mock/placeholder states.

---

## 4. How Harshini Can Connect Her Next.js Frontend

1. Ensure the FastAPI backend is running locally on port 8000:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```
2. In the Next.js project root, create or edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```
3. Run the Next.js dev server:
   ```bash
   npm run dev
   # (Starts on http://localhost:3000)
   ```
4. Log in using pre-seeded Builder credentials:
   * **Email:** `jun@finregtech.io`
   * **Password:** `Password123!`
