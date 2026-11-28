# FinRegTech ShipYard — Backend-to-RAG Integration Contract & Startup Configuration

## 1. Service Topology & Ports

| Service | Host / Port | Base Prefix | Purpose |
| --- | --- | --- | --- |
| Main Backend Gateway (FastAPI + PostgreSQL) | `http://127.0.0.1:8000` | `/api/v1` | Auth, RBAC, PostgreSQL persistence, project isolation, audit trail, RAG proxy |
| AI/RAG Microservice (`abc-shield-ai`, FastAPI + ChromaDB) | `http://127.0.0.1:8001` | `/api/v1` | Grounded regulatory retrieval, advice conflict comparison, human-review routing |

---

## 2. Backend Environment & Runtime Configuration (`backend/app/core/config.py`)

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `8000` | Main backend gateway HTTP port |
| `HOST` | `127.0.0.1` | Main backend bind host |
| `RAG_SERVICE_URL` | `http://127.0.0.1:8001` | Base URL of the `abc-shield-ai` microservice (`settings.RAG_SERVICE_URL`) |
| `RAG_SERVICE_TIMEOUT_SECONDS` | `35.0` | `httpx.Client(timeout=...)` timeout for health, query, and comparison requests |
| `RATE_LIMIT_AI_QUERY_MAX` | `30` | Max AI query requests per window (`RATE_LIMIT_AI_QUERY_WINDOW_SECONDS = 60`) |

### Local Side-by-Side Startup Configuration

1. **Start AI/RAG Microservice on Port `8001`:**
   From `abc-shield-ai/`:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8001
   ```
   Verify upstream health directly at `GET http://127.0.0.1:8001/api/v1/health` (or `GET http://127.0.0.1:8001/health`). Expected payload includes `"status": "ok"`, `"rag_pipeline_initialized": true`, `"chromadb_status": "connected"`.

2. **Start Main Backend Gateway on Port `8000`:**
   From `backend/` (ensure `.env` has `RAG_SERVICE_URL=http://127.0.0.1:8001` or uses the default):
   ```powershell
   .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Verify gateway-to-RAG health at `GET http://127.0.0.1:8000/api/v1/rag/health` (or `GET http://127.0.0.1:8000/health`).

---

## 3. Health Check Endpoints & Offline Behavior

| Endpoint (Backend Port `8000`) | Upstream Call (Port `8001`) | Response When Connected | Response When Port `8001` Is Down |
| --- | --- | --- | --- |
| `GET /health` | `GET /api/v1/health` | `200` with `database.status = "connected"`, `rag_service.status = "connected"` | `200` with `rag_service.status = "unreachable"` (`Connection refused on http://127.0.0.1:8001`) |
| `GET /api/v1/health` | `GET /api/v1/health` | `200` with `service = "finreg-rag-engine"`, `details.status = "connected"` | `200` with `details.status = "unreachable"` |
| `GET /api/v1/rag/health` | `GET /api/v1/health` | `200` with `status = "healthy"`, `rag_microservice.status = "connected"` | `200` with `status = "degraded"`, `rag_microservice.status = "unreachable"` |

---

## 4. Core Backend-to-RAG API Endpoints

### A. `POST /api/v1/rag/analyze` (`RAGAnalyzeRequest`)

- **Authentication & Project Isolation:**
  - Requires valid JWT bearer token (`get_current_user` -> `401 Unauthorized` when missing/invalid).
  - If `projectId` or `project_id` is supplied: verifies active `ProjectMember` (`member_status == "ACTIVE"` -> `403 Forbidden` for non-members/pending/revoked advisors; `404 Not Found` if project missing).
  - If `requirement_ids` or `advisor_advice_ids` are supplied without `projectId`/`project_id` -> `422 ValidationError`. If referenced IDs belong to a different project -> `404 NotFoundError`.
- **Request Fields:**
  - `query` (`str`, required, non-whitespace)
  - `projectId` / `project_id` (`int | str`, optional)
  - `requirement_ids` (`List[str]`, optional)
  - `advisor_advice_ids` (`List[int | str]`, optional; when `>= 2` provided, resolves DB `Advice` records and proxies to `compare_advice`)
  - `context` (`Dict[str, Any]`, optional)
- **Gateway -> RAG Microservice Proxy (`RAGServiceClient.query_rag`):**
  - Sends `POST http://127.0.0.1:8001/api/v1/query` with `{"query": ..., "context": {"project_id": ...}, "requirement_ids": ..., "advisor_advice_ids": ...}` (sets `project_id` at top level only when `scope_tenant_documents=True`).
- **Formatted Response Fields (`format_rag_response_for_frontend`):**
  - `schema_version`, `request_id`, `query`, `status` (`"SUCCESS"` | `"CONFLICT_DETECTED"` | raw upstream status), `answer`, `grounded` (`bool`), `gap` (`is_gap`, `isGapDetected`, `gap_type`, `message`, `user_safe_message`), `citations`, `provenance` (`record_id`, `source_id`, `section_article`, `official_source`, `version_date`, `validation_status`, `is_approved_for_rag`), `conflicts`, `findings`, `retrieved_evidence`, `metadata` (`retrieved_count`, `approved_evidence_count`, `citation_count`, `conflict_count`, `has_gap`, `requires_human_review`, `has_candidate_evidence`, `disclaimer`, `timestamp`).

### B. `POST /api/v1/rag/query` (`QueryRequestPayload`)

- Enforces project membership (`ADMIN`, creator, or `ACTIVE` `ProjectMember` -> `403 Forbidden` otherwise) when `current_user` is authenticated and `project_id`/`projectId` resolves to an existing project; passes `context` and forwards to `POST http://127.0.0.1:8001/api/v1/query`.

### C. `POST /api/v1/rag/compare` & `POST /api/v1/ai/compare`

- `POST /api/v1/ai/compare` requires `get_current_user` (`401` if unauthenticated) and verifies `ACTIVE` `ProjectMember` (`403`) if `projectId`/`project_id` is specified.
- `RAGServiceClient.compare_advice` forwards normalized `advisor_1`, `advisor_2`, `comparison_id`, and `context` to `POST http://127.0.0.1:8001/api/v1/compare`.

### D. Human Review & Grounded Project Retrieval Endpoints

- `POST /api/v1/projects/{projectId}/ai/retrieve` (`RetrievalRequest`, requires `require_project_member`): searches local PostgreSQL regulatory sources without external RAG downtime failure.
- `GET /api/v1/projects/{projectId}/human-reviews` (`require_project_member`) and `PATCH /api/v1/projects/{projectId}/human-reviews/{reviewId}` (`require_project_member`): records review status updates in `conflict_gaps` and emits `HUMAN_REVIEW_UPDATED` audit events.

---

## 5. Error & Timeout Behavior

| Condition | HTTP Status | Detail |
| --- | --- | --- |
| RAG service offline / connection refused on `127.0.0.1:8001` | `503 Service Unavailable` | `"The regulatory AI intelligence service is currently unreachable on port 8001..."` (`ServiceUnavailableError`) |
| RAG request exceeds `RAG_SERVICE_TIMEOUT_SECONDS` (`35.0s`) | `503 Service Unavailable` | `"The regulatory AI intelligence service timed out after 35.0s."` |
| Upstream RAG returns HTTP `422` | `422 Unprocessable Content` | `ValidationError` forwarding upstream validation error details |
| Upstream RAG returns unexpected `5xx` or other non-`200`/`422` status | `503 Service Unavailable` | `ServiceUnavailableError` reporting upstream HTTP status |
| Unauthenticated caller on `/api/v1/rag/analyze` or `/api/v1/ai/compare` | `401 Unauthorized` | `AuthenticationError` |
| Non-member / pending or revoked advisor specifying another `projectId` | `403 Forbidden` | `ForbiddenError` |
