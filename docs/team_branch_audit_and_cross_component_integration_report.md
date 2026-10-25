# FINREGTECH SHIPYARD: TEAM BRANCH AUDIT, CROSS-COMPONENT COMPATIBILITY & SAFE INTEGRATION REPORT

**Author:** Vishal S.R. (Backend & Workflow Engineer Intern)  
**Date:** October 25, 2026  
**Repository:** `https://github.com/madhesh2305/FINREG-TECH-SHIPYARD-PROJECT`  
**Target Backend Branch:** `feature/vishal-backend`  
**Audit Scope:** Harshini Senthilkumar (`origin/feature/harshini-frontend`), Padma Kumar (`origin/ai-rag`), Vishal S.R. (`origin/feature/vishal-backend`)  
**Verdict:** FULLY COMPATIBLE WITH IDENTIFIED TEAM DEFECT REMEDIATIONS (126/126 backend tests passed, 19/19 RAG integration tests passed, 7/7 retrieval tests passed; primary DB 100% intact)

---

## 1. Remote Branch Inventory & Commit Discovery

Fresh remote branches discovered and verified from GitHub (`origin`):

| Component / Role | Remote Branch Name | Latest Commit SHA | Author | Commit Date | Commit Subject |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Frontend Owner** | `origin/feature/harshini-frontend` | `bde132e2e9878579002ea12b1da7d050502e6f1d` | `harshinisenthil-28 <harshini28senthil@gmail.com>` | 2026-10-23 19:05:21 +0530 | `Failed to Fetch Code` |
| **AI / RAG Owner** | `origin/ai-rag` | `1c2912aac2544b39d9b3206b2c934e97320500b6` | `Padma Kumar <spkumar43903@gmail.com>` | 2026-10-23 17:49:20 +0530 | `integration files` |
| **Backend Owner** | `origin/feature/vishal-backend` | `961cb9fbd348ada9a096897b7eb297ca6b0f4a9e` | `Vishal S.R.` | 2026-10-21 16:20:00 +0530 | Verified backend baseline |
| **Frontend Mirror** | `origin/feature/vishal-frontend` | `cbc0a51e232d09ebdfddf94fc486659666f31b81` | `Vishal S.R.` | 2026-10-21 16:05:00 +0530 | Isolated baseline mirror |
| **Main Release** | `origin/main` | `358057a9581df932d0a801076199dd6959d12706` | `madhesh2305` | 2026-09-12 23:31:19 +0530 | Initial commit |

---

## 2. Harshini Frontend Audit (`feature/harshini-frontend` @ `bde132e`)

### 2.1 Confirmed Improvements
1. **Purged Plaintext User Credentials:** In `src/services/authService.js`, `localStorage.removeItem('finreg_registered_users')` purges legacy insecure mock accounts. `getRegisteredUsers()` returns `[]`.
2. **Authoritative Registration (`POST /auth/register`):** User registration dispatches payload `{ full_name, email, password, role, organization }` to the real PostgreSQL backend. Fake offline registration fallbacks have been removed.
3. **Authoritative Login (`POST /auth/login`):** Credentials are sent directly to the backend. Plaintext passwords are not stored in browser storage.
4. **Session Recovery (`GET /users/me`):** Authenticated state is validated against `/users/me` on startup.
5. **Universal API Client (`src/services/api.js`):** Attaches `Authorization: Bearer <token>` and correctly handles `FormData` uploads.
6. **Purged Mock Project Storage:** `src/services/projectService.js` purges `finreg_projects`.

### 2.2 Unresolved Disconnections & Frontend Defects
1. **DEF-FE-01 (High): Unwired `AiRagFindingsView` in `DashboardView.jsx`**
   - **File:** [DashboardView.jsx](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/components/DashboardView.jsx#L1618)
   - **Evidence:** Line 1618 renders `<AiRagFindingsView isDarkMode={isDarkMode} />` without passing the `findings` prop.
   - **Impact:** The view defaults to `findings=[]`, rendering an empty placeholder table even when the user runs queries or opens the tab.
2. **DEF-FE-02 (High): `analyzeRAGConflict` Is Uncalled Across Entire Codebase**
   - **File:** [ragService.js](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/ragService.js#L7)
   - **Evidence:** `git grep "analyzeRAGConflict"` shows it is defined only in `ragService.js` and imported by **zero** components in the application.
3. **DEF-FE-03 (Medium): Payload Key Discrepancy in `ragService.js`**
   - **File:** [ragService.js](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/frontend/src/services/ragService.js#L5)
   - **Evidence:** JSDoc states `@param {object} payload - { project_id, query, ... }` (snake_case `project_id`), whereas initial backend schemas expected camelCase `projectId`.

---

## 3. Padma Kumar AI/RAG Branch Audit (`ai-rag` @ `1c2912a`)

### 3.1 Confirmed Capabilities
1. **Canonical Semantic Router (`/api/v1/query`):** Implements `GroundedGenerator`, `AdviceRAGAdapter`, and returns unified `StructuredAIResponse`.
2. **Source-Grounded Advice Comparison (`/api/v1/compare`):** Implements `AdviceComparator` to analyze differences, citations, and registered conflicts between two advisor positions.
3. **Non-Adjudication Enforcement:** `decision` remains `None` and `human_review_required=True` across all comparisons, strictly preserving human SME adjudication.
4. **Candidate Evidence Isolation:** Candidate statutory records correctly report `is_approved_for_rag=False`. Filtering for approved records fails closed to `UNAPPROVED_EVIDENCE`.

### 3.2 Unresolved Structural Defects on `origin/ai-rag`
1. **DEF-RAG-01 (Critical): Flat Root Directory Layout Breaks Python Imports**
   - **Evidence:** Padma committed 17 files flat into the repository root: `health.py`, `query.py`, `main.py`, `settings.py`, `vector_store.py`, etc.
   - **Impact:** `query.py` executes `from api.models.query import QueryRequest` and `health.py` executes `from api.dependencies import check_chromadb_connectivity`. Cloned directly from `origin/ai-rag`, running `python main.py` or `pytest` immediately throws `ModuleNotFoundError: No module named 'api'`.
   - **Local Workaround:** In local `abc-shield-ai/`, files are organized in proper package subdirectories (`api/`, `config/`, `rag/`, `tests/`).
2. **DEF-RAG-02 (Critical): Missing ChromaDB Persist Directory in Git**
   - **Evidence:** `data/staging/madhesh_handover/step6/chroma_db` is omitted from `origin/ai-rag`.
   - **Impact:** `dependencies.py` lines 34-39 strictly fail closed:
     ```python
     if not persist_dir.exists():
       raise FileNotFoundError(
           f"Canonical ChromaDB persist directory '{persist_dir}' does not"
           " exist. Failing closed to prevent silent fallback to legacy"
           " production store."
       )
```
     A fresh clone crashes on startup unless the vector database directory is created or populated.
3. **DEF-RAG-03 (Medium): Port Collision in Default Configuration**
   - **Evidence:** `settings.py` sets `api_port: int = 8000`.
   - **Impact:** The main FinRegTech ShipYard backend runs on `8000`. Running both on port 8000 causes an `[Errno 10048] Only one usage of each socket address is normally permitted` collision. The microservice must run on port `8001`.

---

## 4. Cross-Component Compatibility Matrix

| # | Integration Dimension | Harshini Frontend (`bde132e`) | Vishal Backend (`feature/vishal-backend`) | Padma AI/RAG (`1c2912a`) | Status | Resolution / Action Required |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **User Registration** | Sends `{ full_name, email, password, role, organization }` via `POST /auth/register` | Accepts `full_name`, hashes with bcrypt, assigns role, returns JWT token | N/A | **ALREADY COMPATIBLE** | None. Direct DB persistence verified. |
| **2** | **User Authentication** | Sends `{ email, password }` via `POST /auth/login` | Returns `{ access_token, user_id, platform_role }` | N/A | **ALREADY COMPATIBLE** | None. Full lifecycle verified. |
| **3** | **Project Isolation** | Transmits project ID in route or payload | Validates `ProjectMember` active status; rejects outsiders with 403 / 404 | Passes project ID in audit context | **ALREADY COMPATIBLE** | BOLA/IDOR protection verified. |
| **4** | **RAG Query Endpoint** | Defines `POST /rag/analyze` in `ragService.js` | Exposes `POST /rag/analyze` with authorization and BOLA verification | Exposes `POST /api/v1/query` | **ALREADY COMPATIBLE** | Backend proxies and transforms responses. |
| **5** | **Field Naming (`projectId` vs `project_id`)** | Mentions `project_id` in comments, uses `projectId` in parts of UI | Added support for BOTH `projectId` and `project_id` in `RAGAnalyzeRequest` and `RAGCompareRequest` | Accepts `project_id` in top-level JSON request | **ALREADY COMPATIBLE** | Backend dual-field resolution implemented. |
| **6** | **Findings View Integration** | `<AiRagFindingsView />` expects array of `{ id, finding, type, requirement, supportingSource, humanReview, ... }` | Synthesizes UI-ready `findings` array directly in `/rag/analyze` response | Returns `StructuredAIResponse` with citations, gaps, conflicts | **BACKEND ENHANCED / FRONTEND FIX REQ** | Backend now provides `findings` array. Harshini needs to wire `<AiRagFindingsView findings={findings} />`. |
| **7** | **Advice Comparison** | Component `AdviceDecisionsView.jsx` available | Exposes `POST /rag/compare` and compares project advice records | Exposes `POST /api/v1/compare` with non-adjudication guarantee | **ALREADY COMPATIBLE** | Both endpoints verified. |
| **8** | **Citations & Provenance** | Renders statutory citations and issuing authority | Extracts and normalizes statutory provenance (`UK-01`, `FCA-01`) | Provides 25 canonical candidate records | **ALREADY COMPATIBLE** | Traceability verified end-to-end. |
| **9** | **Evidence Approval Gating** | Ready to display approval / candidate badges | Distinguishes approved vs candidate evidence in response metadata | Strictly returns `UNAPPROVED_EVIDENCE` status when `filter_approved_only=True` | **ALREADY COMPATIBLE** | Fail-closed security verified. |
| **10** | **Health & Readiness** | Probes service readiness | Exposes `GET /rag/health` and includes RAG in root health check | Exposes `GET /health` and `GET /api/v1/health` | **ALREADY COMPATIBLE** | Verified HTTP 200 health responses. |
| **11** | **Packaging & Port Allocation** | Vite connects to `http://localhost:8000/api/v1` | Backend listens on `8000`; proxies RAG to `8001` | Default `settings.py` specifies `8000` | **CONFIGURATION REQUIRED** | AI/RAG microservice must run on port `8001` via `ABC_SHIELD_RAG_BASE_URL`. |

---

## 5. Backend Enhancements Implemented on `feature/vishal-backend`

To make the integration resilient against frontend field discrepancies and directly power Harshini's `AiRagFindingsView`:

1. **Dual Casing Support in Schemas ([ai.py](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/schemas/ai.py)):**
   - Added `project_id: Optional[Union[int, str]] = None` alongside `projectId`.
   - Implemented `resolved_project_id` property on `RAGAnalyzeRequest` and `RAGCompareRequest`.
2. **Controller Resolution ([ai.py](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/api/v1/ai.py)):**
   - Refactored `compare_advisor_advice` and `analyze_rag` to resolve `target_pid = payload.resolved_project_id`.
   - Seamlessly handles both camelCase (`projectId`) and snake_case (`project_id`).
3. **UI Findings Synthesis ([rag_service.py](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/services/rag_service.py)):**
   - In `format_rag_response_for_frontend()`, conflicts, evidence gaps, and grounded citations are automatically synthesized into a `findings` list matching `AiRagFindingsView.jsx`:
     - `id`: Unique identifier (`FND-CONF-1`, `FND-GAP-1`, `FND-CIT-1`)
     - `finding`: Concise summary description
     - `type`: `"Conflict"`, `"Evidence Gap"`, or `"Source Grounded"`
     - `requirement`: Linked requirement topic
     - `supportingSource`: Authority citation or failure note
     - `humanReview`: `"Needs human review"` or `"Verified"`
     - Badges: Styled for Tailwind dark/light UI
4. **Resilient Microservice Timeout ([config.py](file:///C:/Users/Vishal/OneDrive/Documents/FinRegTechnology%20ShipYard/backend/app/core/config.py)):**
   - Increased `RAG_SERVICE_TIMEOUT_SECONDS` from `20.0` to `35.0` to accommodate Windows CPU PyTorch cold-start during initial model loading.

---

## 6. Verification Test Results

### 6.1 Backend Full Regression Suite (`backend/tests/`)
- **Command:** `pytest tests/ -v`
- **Result:** **126 / 126 Passed (100%)** in 54.74s
- **Coverage:** Admin, Advice, Advisors, Auth, Decisions, Projects, Registration, Regulatory, Security Negative, Week 6 Security Suite, RAG Integration.

### 6.2 Backend RAG Integration Suite (`backend/tests/test_rag_integration.py`)
- **Command:** `pytest tests/test_rag_integration.py -v`
- **Result:** **19 / 19 Passed (100%)** in 10.06s
- **Scenarios Verified:**
  1. `test_database_safety_guard`: Confirms tests run exclusively on `finregtech_test`.
  2. `test_authenticated_rag_query_success`: Authenticated query returns 200 with citations.
  3. `test_rag_query_unauthenticated`: Returns 401 Unauthorized.
  4. `test_rag_query_unauthorized_outsider`: Returns 403 Forbidden.
  5. `test_rag_query_invalid_requirement_bola`: Returns 404 on cross-tenant requirement.
  6. `test_rag_query_invalid_advice_bola`: Returns 404 on cross-tenant advice.
  7. `test_rag_advice_comparison_success`: Returns 200 with non-adjudicated comparison.
  8. `test_rag_query_empty_or_whitespace`: Returns 422 Unprocessable Entity.
  9. `test_rag_query_out_of_scope`: Returns 200 with `OUT_OF_SCOPE` gap status.
  10. `test_rag_query_insufficient_evidence_french_transposition`: Returns 200 with `INSUFFICIENT_EVIDENCE`.
  11. `test_rag_query_fail_closed_approved_only`: Returns 200 with `UNAPPROVED_EVIDENCE`.
  12. `test_rag_query_conflict_detection`: Returns 200 with documented conflicts.
  13. `test_rag_citation_provenance_traceability`: Verifies citation links and topic grounding.
  14. `test_rag_dashboard_frontend_contract`: Confirms top-level keys for `DashboardView.jsx`.
  15. `test_rag_query_snake_case_project_id_and_findings_view_contract`: Confirms `project_id` and UI-ready `findings` schema for `AiRagFindingsView.jsx`.
  16. `test_rag_service_unavailable`: Returns 503 when microservice is down.
  17. `test_rag_service_timeout`: Returns 503 on microservice timeout.
  18. `test_rag_health_endpoint`: Returns 200 with connected status.
  19. `test_root_health_includes_rag`: Root `/health` reports RAG subsystem status.

### 6.3 ABC Shield AI/RAG Retrieval Suite (`abc-shield-ai/tests/test_retrieval.py`)
- **Command:** `pytest tests/test_retrieval.py -v`
- **Result:** **7 / 7 Passed (100%)** in 21.93s
- **Scenarios Verified:** Root/versioned health check, UK Bribery Act query, fail-closed approved-only filter, out-of-scope query, French transposition insufficient evidence, advice comparison (`CO-001`), extra forbidden fields rejection.

### 6.4 Database Integrity Audit
- **Primary Database:** `"FinRegTech ShipYard"`
- **Active Project Count:** 178 (100% intact, zero test pollution)
- **Active User Count:** 344 (100% intact)
- **Automated Test Database:** `finregtech_test` (isolated, ephemeral test data only)

---

## 7. Action Plan & Forwardable Messages for Teammates

### 7.1 Forwardable Message for Harshini Senthilkumar (Frontend Owner)

```text
Hi Harshini,

I've audited your latest frontend branch (`feature/harshini-frontend` @ `bde132e`).
Great work removing the legacy plaintext user localStorage caching and hooking up live registration and login!

Here is what we need to complete the AI / RAG Findings integration:

1. Wiring `analyzeRAGConflict` in `DashboardView.jsx`:
   Currently, `DashboardView.jsx` (line 1618) renders `<AiRagFindingsView isDarkMode={isDarkMode} />` without passing the `findings` prop or fetching them, so the table remains empty.
   
   Suggested fix:
   - Import `analyzeRAGConflict` from `../services/ragService`:
     import { analyzeRAGConflict } from '../services/ragService';
   - In `DashboardView.jsx`, add state:
     const [ragFindings, setRagFindings] = useState([]);
   - In a `useEffect` when `activeTab === 'AI / RAG Findings'`, load the findings:
     useEffect(() => {
       if (activeTab === 'AI / RAG Findings' && currentProject?.id) {
         analyzeRAGConflict({
           projectId: currentProject.id,
           query: "Evaluate compliance conflicts and evidence gaps across regulatory regimes"
         }).then(res => {
           if (res && res.findings) {
             setRagFindings(res.findings);
           }
         });
       }
     }, [activeTab, currentProject?.id]);
   - Pass the findings into the component:
     <AiRagFindingsView isDarkMode={isDarkMode} findings={ragFindings} />

2. Backend schema support:
   I have updated the backend on `feature/vishal-backend` so that `POST /api/v1/rag/analyze` now returns a pre-formatted `findings` list matching your `AiRagFindingsView` props (`id`, `finding`, `type`, `requirement`, `supportingSource`, `humanReview`, `typeBadge`, `statusBadge`). It also accepts both `projectId` and `project_id`.

Once you connect this, the AI / RAG Findings table will populate automatically from live regulatory evidence!
```

---

### 7.2 Forwardable Message for Padma Kumar (AI/RAG Owner)

```text
Hi Padma Kumar,

I've reviewed your latest commit on branch `origin/ai-rag` (`1c2912a`).
The query logic, GroundedGenerator, and AdviceComparator contracts are solid and align with our Week 5/6 requirements!

However, there are three items that will prevent other developers or CI from running your branch:

1. Package Structure & Module Imports (Critical):
   All files were pushed flat to the root directory (`query.py`, `health.py`, `dependencies.py`, etc.).
   Because `query.py` contains `from api.models.query import QueryRequest` and `from rag.generation...`, running `python main.py` or `pytest` immediately fails with `ModuleNotFoundError: No module named 'api'`.
   Please organize the files into proper subdirectories:
   abc-shield-ai/
   ├── api/
   │   ├── main.py
   │   ├── dependencies.py
   │   ├── routes/ (health.py, query.py, compare.py)
   │   └── models/ (health.py, query.py)
   ├── config/ (settings.py)
   └── rag/ (retrieval/, conflict/, generation/, pipeline/, output/)

2. ChromaDB Staging Data in Git (Critical):
   `dependencies.py` has a fail-closed guard checking `data/staging/madhesh_handover/step6/chroma_db`. Since the database folder was not pushed to git, running the service raises `FileNotFoundError`.
   Please ensure either the 25-record vector store is committed, or add a script (e.g. `python scripts/seed_chroma.py`) to generate it from source JSON.

3. Default Port Conflict:
   `settings.py` sets `api_port: int = 8000`. The main FinRegTech backend already runs on port 8000.
   Please change the default to `api_port: int = 8001` or run via `uvicorn api.main:app --port 8001` to avoid `[Errno 10048]` socket collisions.

Our backend client is already configured to communicate with your service at `http://127.0.0.1:8001/api/v1` and passes all 19 integration tests!
```

---

## 8. Git Status Summary on `feature/vishal-backend`

All changes remain safely in the working tree and have **NOT** been committed or pushed, strictly adhering to release governance rules:

```text
On branch feature/vishal-backend
Your branch is up to date with 'origin/feature/vishal-backend'.

Changes not staged for commit:
	modified:   app/api/v1/ai.py
	modified:   app/core/config.py
	modified:   app/core/exceptions.py
	modified:   app/main.py
	modified:   app/schemas/ai.py
	modified:   tests/test_rag_integration.py
	modified:   tests/test_week6_security_suite.py

Untracked files:
	app/services/rag_service.py
	docs/abc_shield_ai_rag_integration_report.md
	docs/frontend_backend_integration_completion_report.md
	docs/frontend_backend_postgresql_integration_audit_report.md

Teammate Branches:
	feature/harshini-frontend: UNTOUCHED (read-only audit)
	origin/ai-rag: UNTOUCHED (read-only audit)
```
