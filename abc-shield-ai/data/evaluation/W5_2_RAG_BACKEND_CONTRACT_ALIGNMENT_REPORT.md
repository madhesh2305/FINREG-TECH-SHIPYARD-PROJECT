# WEEK 5 — TASK W5.2: RAG BACKEND CONTRACT ALIGNMENT REPORT

---

## 1. Document Control

| Attribute | Specification |
| :--- | :--- |
| **Task Reference** | **WEEK 5 — TASK W5.2: RAG Backend Contract Alignment** |
| **Document Version** | **1.0.0** |
| **Date** | **October 7, 2026** |
| **Role / Lead Author** | **Padma Kumar** — AI/RAG & Conflict Detection Engineer |
| **Project** | **ABC Shield / FinRegTech ShipYard AI/RAG** |
| **Collaborators** | **Vishal** (Backend Lead), **Harshini** (Frontend Lead), **Sanjay** (API Gateway / Infrastructure Lead) |
| **Verified Baseline** | **524 / 524 Tests Passing (100.0% Pass Rate)** |
| **Corpus Invariant** | **15 Canonical Regulatory Records (15 Candidate / 0 Approved), ChromaDB = 15 Vectors** |
| **Status** | **COMPLETE** |

---

## 2. Objective

The objective of Task W5.2 is to make the existing Padma AI/RAG API ready to receive the product workflow context provided by Vishal's backend:
- `project_id`: Project / workspace context string
- `requirement_ids`: Upstream requirement context identifiers
- `context`: Filtering hints dictionary (`jurisdiction`, `regulatory_area`)

The RAG pipeline receives these integration fields via `POST /api/v1/query` and dispatches them down to the existing `RegulatoryRetriever` and `GroundedGenerator` while preserving all existing security controls, fail-closed boundaries, and the W4.11 contract.

---

## 3. Changes Implemented

### 3.1 Extended `QueryRequest` Model (`api/models/query.py`)
Extended the client request schema with three optional integration fields while strictly maintaining Pydantic validation rules and `extra="forbid"`:
- `project_id: Optional[str] = None`
- `requirement_ids: Optional[List[str]] = None`
- `context: Optional[Dict[str, Any]] = None`
- Preserved: `min_length=1`, `max_length=settings.query_max_length` (2000), whitespace validator, and `extra="forbid"`.

### 3.2 Wired Integration Fields into API Route (`api/routes/query.py`)
Updated `execute_query()` to extract supported integration parameters and pass them directly to `GroundedGenerator.generate_structured_response()`:
- `project_id`: Extracted from `request.project_id` and passed into retriever vector filter.
- `jurisdiction`: Extracted from `request.context.get("jurisdiction")` and passed into retriever vector filter.
- `requirement_ids`: Accepted as workflow context and preserved in API logging.
- Preserved existing architecture: Zero duplicate retrieval logic; zero changes to `GroundedGenerator` internals.

### 3.3 Security Test Adjustment (`tests/test_security_phase2_retrieval_context.py`)
- Updated `test_api_forbids_client_side_tenant_tampering` to verify that unauthorized tenant tampering fields (e.g. `tenant_id="MaliciousTenantInjection"`) are strictly rejected with `extra_forbidden`, because `project_id` is now a formally supported integration attribute.

---

## 4. API Contract Specification (Updated `QueryRequest`)

```json
{
  "project_id": "PRJ-ABC-001",
  "query": "What procedures should commercial organisations implement to prevent bribery?",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "context": {
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption"
  }
}
```

### Response Schema (`StructuredAIResponse`)
The response structure is strictly unchanged and 100% conforming to the W4.11 Integration Contract:
- `request_id`: Server-generated correlation ID (`REQ-<uuid4>`)
- `query`: Preserved user query text
- `status`: `ResponseStatus` enum (`GROUNDED`, `INSUFFICIENT_EVIDENCE`, `OUT_OF_SCOPE`, etc.)
- `answer`: Grounded response text
- `grounded`: Boolean flag (`true` / `false`)
- `gap`: Structured `GapResult` (or `null` when grounded)
- `citations`: Deterministic `Citation` records
- `provenance`: Traceable `ProvenanceRecord` records
- `conflicts`: Deterministic `ConflictFinding` records (`CO-001`..`CO-011`)
- `retrieved_evidence`: Structured `RetrievedEvidenceItem` records
- `metadata`: `ResponseMetadata` (`retrieved_count`, `approved_evidence_count`, `conflict_count`, `requires_human_review`, `has_candidate_evidence`, `response_version="1.0"`)

---

## 5. Security & Isolation Preservation

All security controls established across S1 and Phases 1–4 remain active and fully validated:
1. **`extra="forbid"` Defense:** Arbitrary client-injected fields (e.g. `is_approved_for_rag`, `provider`, `model_name`, `unauthorized_field`) continue to be rejected with HTTP 422 Unprocessable Entity.
2. **Project Isolation & Fail-Closed Behavior:** Supplying an unassigned project ID (e.g. `ForeignProject-XYZ`) to `POST /api/v1/query` returns 0 evidence chunks and fails closed to `status="INSUFFICIENT_EVIDENCE"`, preventing cross-tenant leakage.
3. **Integration Context vs Authorization:** The `project_id` supplied in the request is treated as integration context, NOT as proof of authorization. Vishal's production backend middleware must validate and inject the trusted tenant context server-side.
4. **Approval Fail-Closed Gating:** All 15 canonical regulatory records remain marked `Candidate - Awaiting Approval` (0 approved records). Approved-only queries return 0 results and 0 LLM calls.
5. **Deterministic Citations & Non-Adjudication:** Zero citation hallucination on gaps; both-source requirement enforced on conflict detection; zero legal adjudication.

---

## 6. Focused W5.2 Test Results

Created [`tests/test_rag_backend_contract_w52.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_rag_backend_contract_w52.py) containing 10 targeted test cases:

| # | Test Case | Target Verification | Result |
| :-: | :--- | :--- | :---: |
| 1 | `test_w52_existing_request_without_optional_fields` | Standard query without optional fields returns HTTP 200, grounded answer, citations | **PASS** |
| 2 | `test_w52_request_with_project_id` | Request with `project_id` accepted as valid integration context (fails closed on unassigned) | **PASS** |
| 3 | `test_w52_request_with_requirement_ids` | Request with `requirement_ids` accepted as valid workflow context | **PASS** |
| 4 | `test_w52_request_with_context` | Request with `context.jurisdiction` properly filters evidence to UK only | **PASS** |
| 5 | `test_w52_full_w411_style_request` | Full W4.11-style request payload executes cleanly and produces StructuredAIResponse | **PASS** |
| 6 | `test_w52_invalid_empty_query_rejected` | Empty query string rejected with HTTP 422 | **PASS** |
| 7 | `test_w52_invalid_whitespace_query_rejected` | Whitespace-only query string rejected with HTTP 422 | **PASS** |
| 8 | `test_w52_unknown_top_level_field_rejected` | Unknown/unauthorized fields rejected via `extra="forbid"` with HTTP 422 | **PASS** |
| 9 | `test_w52_project_filtering_remains_enforced` | Foreign/unassigned `project_id` fails closed to 0 retrieved chunks | **PASS** |
| 10 | `test_w52_jurisdiction_filtering_remains_enforced` | Context jurisdiction filtering enforced for UK, EU, and invalid scopes | **PASS** |

**Focused Suite Result:** `10 passed in 16.05s (100% pass rate)`.

---

## 7. Full Regression Test Results

A full regression run was executed across the entire repository:

```
Command: python -m pytest -q
Results: 524 passed in 545.31s (0:09:05)
Failures: 0
Errors: 0
Pass Rate: 100.0%
```

- Baseline: 514 passed
- Added: 10 new W5.2 contract tests
- New Total: **524 passed** (0 failures, 0 errors)

---

## 8. Files Modified & Created

### Files Modified:
1. [`api/models/query.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/models/query.py): Added optional `project_id`, `requirement_ids`, and `context` fields to `QueryRequest` with `extra="forbid"`.
2. [`api/routes/query.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/query.py): Extracted `project_id` and `context.jurisdiction` and wired them to `generator.generate_structured_response()`.
3. [`tests/test_security_phase2_retrieval_context.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_security_phase2_retrieval_context.py): Updated line 265 in `test_api_forbids_client_side_tenant_tampering` to verify unauthorized tenant field rejection via `tenant_id`.

### Files Created:
1. [`tests/test_rag_backend_contract_w52.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_rag_backend_contract_w52.py): 10 focused contract alignment tests.
2. [`data/evaluation/W5_2_RAG_BACKEND_CONTRACT_ALIGNMENT_REPORT.md`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/evaluation/W5_2_RAG_BACKEND_CONTRACT_ALIGNMENT_REPORT.md): This report.

---

## 9. Governance & Responsibility Boundaries

### PADMA COMPLETED:
- RAG request schema alignment (`project_id`, `requirement_ids`, `context`)
- RAG API wiring to existing retriever and generator
- RAG-side context handling (`jurisdiction`, `project_id`)
- 10 focused contract validation tests (10/10 PASS)
- Full regression verification (524/524 PASS)

### VISHAL STILL OWNS (EXTERNAL BACKEND DEPENDENCIES):
- Authenticated user and tenant session binding
- Server-side `project_id` validation and injection
- Upstream advice generation business workflow
- Database persistence (PostgreSQL/SQLModel for requests, responses, provenance)
- Production API Gateway configuration (rate limiting, TLS termination, OAuth2/JWT)

---

## 10. W4.11 Compatibility Assessment

The changes directly implement Section 4 of the locked W4.11 Integration Contract specification without breaking existing clients or schemas:
- Backwards compatible: Requests containing only `query` continue to operate identically.
- Additive compatibility: Incoming requests containing `project_id`, `requirement_ids`, and `context` are parsed cleanly.
- Immutability preserved: Zero modifications to raw regulatory Excel workbooks, canonical JSON records, or ChromaDB vectors.

---

## 11. Conclusion

Task W5.2 is **COMPLETE**. The Padma AI/RAG API endpoint `POST /api/v1/query` is fully aligned with Vishal's backend requirements, maintaining strict security boundaries, fail-closed isolation, and complete regression integrity across all 524 automated tests.
