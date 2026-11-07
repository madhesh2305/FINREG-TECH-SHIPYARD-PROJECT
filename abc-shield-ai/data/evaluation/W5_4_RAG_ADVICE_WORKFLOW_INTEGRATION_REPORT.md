# WEEK 5 — TASK W5.4: RAG INSIDE ADVICE WORKFLOW INTEGRATION REPORT

---

## 1. Document Control

| Attribute | Specification |
| :--- | :--- |
| **Task Reference** | **WEEK 5 — TASK W5.4: RAG Inside Advice Workflow** |
| **Document Version** | **1.0.0** |
| **Date** | **October 7, 2026** |
| **Role / Lead Author** | **Padma Kumar** — AI/RAG & Conflict Detection Engineer |
| **Project** | **ABC Shield / FinRegTech ShipYard AI/RAG** |
| **Collaborators** | **Vishal** (Backend Lead), **Harshini** (Frontend Lead), **Sanjay** (API Gateway / Infrastructure Lead) |
| **Verified Baseline** | **548 / 548 Tests Passing (100.0% Pass Rate)** |
| **Corpus Invariant** | **15 Canonical Regulatory Records (15 Candidate / 0 Approved), ChromaDB = 15 Vectors** |
| **Status** | **COMPLETE** |

---

## 2. Objective & Workflow Mission

The objective of Task W5.4 is to make the existing Padma AI/RAG capability usable from the product's upstream **Advice Workflow**.

### Core Workflow Path:
```
Project Context (PRJ-ABC-001)
  ↓
Requirement / Advice Context (REQ-001, ADV-UK-001)
  ↓
Advisor Advice / Compliance Inquiry
  ↓
AdviceRAGAdapter (Normalizes Context & Traceability)
  ↓
GroundedGenerator (Single Source of Truth)
  ↓
RegulatoryRetriever & ChromaDB (Vector Similarity)
  ↓
Grounded Synthesis (System Prompt Guardrails)
  ↓
Citations + Provenance Assembly
  ↓
Conflict & Relationship Detection (CO-001..CO-011)
  ↓
Evidence Gap Analysis (Coverage & Limitation Detection)
  ↓
Status Determination (W4.11 External Status + Advice Workflow Status)
  ↓
Human SME Review Flag (Non-Adjudicative Gate)
  ↓
StructuredAIResponse & AdviceRAGResult Return
  ↓
Vishal's Backend Workflow / Harshini's Frontend UI
```

### Non-Negotiable Operating Principles:
1. **The RAG system SUPPORTS the Advice workflow**: It retrieves evidence, cites provisions, tracks provenance, and identifies overlaps.
2. **The RAG system NEVER makes the final legal or professional decision**: It does not choose which advisor is correct, does not resolve statutory conflicts automatically, and does not declare entities compliant.
3. **Single Source of Truth**: The existing `GroundedGenerator` and `RegulatoryRetriever` are reused without duplicate retrieval or generation logic.

---

## 3. Actual Advice Workflow Discovered (Repository Inspection)

Prior to implementing changes, the entire repository was systematically inspected to answer the 9 core inspection questions:

| # | Inspection Item | Current Implementation Finding |
| :-: | :--- | :--- |
| **1** | **Where advisor advice enters the system** | Advisor advice context enters via `POST /api/v1/query` in `QueryRequest` (fields `query`, `advisor_advice_ids`, `requirement_ids`, `project_id`, `context`) and in-process via `AdviceRAGAdapter.execute_advice_rag()`. Upstream advice authoring occurs in Vishal's backend and Harshini's frontend. |
| **2** | **What fields identify an advice record** | Identified by `id` (request correlation ID), `advisor_advice_ids` (upstream advisor note IDs), `requirement_ids` (upstream requirement IDs), and `project_id` (workspace tenant ID). |
| **3** | **How `project_id` is represented** | Represented as `Optional[str] = None` in `QueryRequest`. In `RegulatoryRetriever`, it is passed into the metadata filter `{"project_id": project_id}` for workspace tenant isolation (fails closed if unassigned). |
| **4** | **How `requirement_id` is represented** | Represented as `Optional[List[str]] = None` in `QueryRequest`. Preserved as workflow context in API logging and tracked in `AdviceTraceabilityContext.requirement_ids`. |
| **5** | **Whether `advisor_advice_id` already exists** | Yes, added to `QueryRequest` in W5.3 as `advisor_advice_ids: Optional[List[str]] = None`. In W5.4, it is explicitly bound into `AdviceTraceabilityContext.advisor_advice_ids` and logged. |
| **6** | **Whether an advice service/controller already exists** | No separate advice service or controller existed in `abc-shield-ai` prior to W5.4. Only `api/routes/query.py` existed. W5.4 introduces `AdviceRAGAdapter` in `rag/pipeline/advice_adapter.py`. |
| **7** | **Whether Vishal's backend already has an integration point for RAG** | Yes, Vishal's backend integrates via HTTP `POST /api/v1/query` (Microservice Mode) or in-process Python import of `AdviceRAGAdapter` (In-Process Monolith Mode). |
| **8** | **Whether the RAG API can already be called from the advice workflow** | Yes, by submitting a standard JSON payload conforming to `QueryRequest`. |
| **9** | **Real integration vs isolated RAG endpoint** | Prior to W5.4, the API was an isolated RAG query route. In W5.4, `AdviceRAGAdapter` establishes a real programmatic interface that unifies correlation tracking, advice workflow status mapping, and RAG execution for both in-process and REST consumers. |

---

## 4. Existing RAG Integration Points

The RAG engine supports two complementary integration modes:

### Mode 1: HTTP Microservice REST API (Recommended for Production)
- **Endpoint:** `POST /api/v1/query`
- **Request Body:** `QueryRequest` JSON
- **Response Body:** `StructuredAIResponse` JSON (100% W4.11 Contract Compliant)
- **Handler:** `execute_query()` in [`api/routes/query.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/query.py)

### Mode 2: In-Process Python Pipeline Adapter (Local Monolith / Unit Testing)
- **Module:** `rag.pipeline.advice_adapter`
- **Primary Class:** [`AdviceRAGAdapter`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_adapter.py)
- **Methods:**
  - `execute_advice_rag(query, request_id, project_id, requirement_ids, advisor_advice_ids, context, ...)`
  - `execute_from_request(request: QueryRequest, ...)`
- **Return Type:** `AdviceRAGResult` packaging `StructuredAIResponse`, `external_status`, `workflow_status`, `traceability`, and `disclaimer`.

---

## 5. Advice → RAG Data Flow & Architecture

```
                  ┌────────────────────────────────────────┐
                  │ Harshini Advice UI / Vishal Backend     │
                  │ (Project, Requirements, Advisor Advice) │
                  └───────────────────┬────────────────────┘
                                      │
                         HTTP POST / In-Process Call
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │           AdviceRAGAdapter             │
                  │   (Normalizes & Records Traceability)   │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          GroundedGenerator             │
                  │     (Single Source of Truth)           │
                  └─────────┬───────────────────┬──────────┘
                            │                   │
                 Semantic Retrieval      LLM Generation
                            │                   │
                            ▼                   ▼
                  ┌───────────────────┐ ┌───────────────────┐
                  │RegulatoryRetriever│ │  LLM Provider     │
                  │& ChromaDB (15 vec)│ │(Grounded Response)│
                  └─────────┬─────────┘ └─────────┬─────────┘
                            │                     │
                            └──────────┬──────────┘
                                       │
                                       ▼
                  ┌────────────────────────────────────────┐
                  │            Safety Analyzers            │
                  │ • CitationBuilder (Strict citations)   │
                  │ • ConflictDetector (CO-001..CO-011)    │
                  │ • GapHandler (Coverage/limitation gaps)│
                  │ • ResponseBuilder (W4.11 status map)   │
                  └────────────────────┬───────────────────┘
                                       │
                                       ▼
                  ┌────────────────────────────────────────┐
                  │             AdviceRAGResult            │
                  │ • response: StructuredAIResponse       │
                  │ • external_status: SUCCESS / CONFLICT  │
                  │ • workflow_status: RAG_SUPPORTED / etc │
                  │ • traceability: TraceabilityContext    │
                  │ • requires_human_review: boolean       │
                  │ • disclaimer: Non-adjudication notice  │
                  └────────────────────────────────────────┘
```

---

## 6. Files Modified & Created

### Modified Files:
1. [`api/routes/query.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/query.py):
   - Wired route execution through `AdviceRAGAdapter` using the injected `GroundedGenerator`.
   - Enhanced structured logging to record `advisor_advice_ids` and `workflow_status`.
   - Preserved `HTTPException(status_code=500)` safe masking.
2. [`api/dependencies.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/dependencies.py):
   - Added `get_advice_adapter()` factory dependency reusing the singleton `GroundedGenerator`.

### Created Files:
1. [`rag/pipeline/advice_adapter.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_adapter.py):
   - Implemented `AdviceRAGAdapter`, `AdviceRAGResult`, `AdviceWorkflowStatus`, and `AdviceTraceabilityContext`.
2. [`rag/pipeline/__init__.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/__init__.py):
   - Exported adapter models and classes.
3. [`tests/test_rag_advice_workflow_w54.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_rag_advice_workflow_w54.py):
   - 15 dedicated automated unit and contract tests verifying all required integration scenarios.
4. [`data/evaluation/W5_4_RAG_ADVICE_WORKFLOW_INTEGRATION_REPORT.md`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/evaluation/W5_4_RAG_ADVICE_WORKFLOW_INTEGRATION_REPORT.md):
   - Official comprehensive evaluation and evidence documentation.

---

## 7. Integration Boundary Specification

### Request Payload (`QueryRequest`)
```json
{
  "id": "ADV-REQ-98101",
  "project_id": "PRJ-ABC-001",
  "query": "Under Section 1 of the Bribery Act 2010, what elements constitute an offence of bribing another person?",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "advisor_advice_ids": ["ADV-UK-001"],
  "context": {
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption"
  }
}
```

### Traceability Model (`AdviceTraceabilityContext`)
```json
{
  "request_id": "ADV-REQ-98101",
  "project_id": "PRJ-ABC-001",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "advisor_advice_ids": ["ADV-UK-001"],
  "jurisdiction": "UK",
  "regulatory_area": "Anti-Bribery and Corruption",
  "timestamp": "2026-10-07T09:40:00.000000+00:00"
}
```

### Canonical RAG Response (`StructuredAIResponse`)
```json
{
  "request_id": "ADV-REQ-98101",
  "query": "Under Section 1 of the Bribery Act 2010, what elements constitute an offence of bribing another person?",
  "status": "GROUNDED",
  "answer": "Under Section 1 of the Bribery Act 2010, an individual or commercial organisation commits an offence if they offer, promise, or give a financial or other advantage to another person intending to induce improper performance of a relevant function or activity, or to reward such improper performance [Bribery Act 2010, Section 1].",
  "grounded": true,
  "gap": null,
  "citations": [
    {
      "citation_id": "CIT-RR-UK-01-C01",
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "formatted_citation": "[RR-UK-01-C01 | RR-UK-01 | Bribery Act 2010 | Section 1]",
      "is_approved_for_rag": false,
      "validation_status": "Candidate - Awaiting Approval"
    }
  ],
  "provenance": [
    {
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "jurisdiction": "UK",
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "is_approved_for_rag": false
    }
  ],
  "conflicts": [],
  "retrieved_evidence": [ /* raw chunk details */ ],
  "metadata": {
    "retrieved_count": 1,
    "approved_evidence_count": 0,
    "citation_count": 1,
    "conflict_count": 0,
    "has_gap": false,
    "gap_type": null,
    "requires_human_review": false,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

## 8. Status Taxonomy & Mapping Matrix

W5.4 strictly maintains the two distinct status tiers:
1. **External RAG Status:** Conforms 1:1 to W4.11 Section 7.A (`SUCCESS`, `CONFLICT_DETECTED`, `GAP_DETECTED`, `NO_SOURCE_FOUND`, `ERROR`).
2. **Advice Workflow Status:** Business-level status used by Vishal's advice workflow engine (`RAG_SUPPORTED`, `RAG_REVIEW_REQUIRED`, `RAG_GAP_DETECTED`, `RAG_NO_SOURCES`, `RAG_ERROR`).

| Internal `ResponseStatus` | Conflicts | Human Review | External RAG Status (W4.11) | Advice Workflow Status |
| :--- | :---: | :---: | :---: | :---: |
| `GROUNDED` | `0` | `False` | **`SUCCESS`** | **`RAG_SUPPORTED`** |
| `GROUNDED` / `CONFLICTING_EVIDENCE` | `> 0` | `True` | **`CONFLICT_DETECTED`** | **`RAG_REVIEW_REQUIRED`** |
| `INSUFFICIENT_EVIDENCE` / `OUT_OF_SCOPE` | Any | `False` | **`GAP_DETECTED`** | **`RAG_GAP_DETECTED`** |
| `UNAPPROVED_EVIDENCE` | `0` | `True` | **`NO_SOURCE_FOUND`** | **`RAG_NO_SOURCES`** |
| `RuntimeError` / Pipeline Failure | — | — | **`ERROR`** | **`RAG_ERROR`** |

---

## 9. Citations, Provenance, Conflict & Evidence-Gap Handling

### 9.1 Citations & Provenance
- Every statement synthesized from retrieved regulatory records is linked to a deterministic `Citation` and `ProvenanceRecord`.
- If no evidence is retrieved or a gap is detected, citations and provenance are strictly empty (`[]`), guaranteeing zero hallucination.

### 9.2 Conflict & Overlap Findings
- Documented relationships are surfaced if and only if **both** related sources are co-retrieved (`both_sources_retrieved == True`).
- Controlled taxonomy enforced: `OVERLAP` (10 pairs), `VERSION_DIFFERENCE` (1 pair), `CONFLICT` (0 pairs).
- Strictly non-adjudicative: Differences in scope, authority, and version are stated objectively without declaring which regulation prevails.

### 9.3 Evidence Gap Detection
- Identifies missing specific provisions (e.g. Section 7), unapproved evidence states, or out-of-scope inquiries.
- Enforces safe phrasing: *"The requested provision is not represented in the current ABC Shield regulatory evidence corpus."* It never claims the statute itself lacks the section.

---

## 10. Human Review Boundary & Non-Adjudication Invariants

1. **Mandatory Disclaimer:** Every `AdviceRAGResult` carries an explicit disclaimer:
   > *"This analysis provides source-grounded regulatory intelligence and does not constitute formal legal or professional advice. Final compliance determinations remain the responsibility of a qualified compliance professional."*
2. **Human SME Gate (`metadata.requires_human_review = true`):**
   - Automatically flagged whenever conflicts exist or candidate sources are used in authoritative modes.
   - Prevents automated advice publishing without compliance officer sign-off.
3. **No Automatic Decision-Making:**
   - The AI will never decide between competing legal opinions or resolve statutory conflicts.

---

## 11. Security & Isolation Controls

- **Pydantic Validation (`extra="forbid"`):** Rejects unauthorized fields with HTTP 422.
- **Tenant Isolation:** Passing an unassigned or foreign `project_id` returns 0 chunks and fails closed to `status="INSUFFICIENT_EVIDENCE"`. Client context cannot bypass server-side authorization.
- **Approval Gating:** All 15 canonical records remain `Candidate - Awaiting Approval` (0 Approved). Approved-only queries fail closed with 0 LLM calls and empty citations.
- **Error Masking:** Unhandled exceptions return generic HTTP 500 messages (`detail`) without leaking file paths, connection strings, or stack traces.

---

## 12. Verification & Test Results

### 12.1 Dedicated W5.4 Test Suite (`tests/test_rag_advice_workflow_w54.py`)

| # | Test Name | Target Verification | Result |
| :-: | :--- | :--- | :---: |
| 1 | `test_w54_advice_context_creates_valid_rag_request` | Advice context executes cleanly, grounds answer, records full traceability | **PASS** |
| 2 | `test_w54_project_id_passed_as_context_correctly` | `project_id` context propagated to retriever and recorded in traceability | **PASS** |
| 3 | `test_w54_requirement_ids_preserved_correctly` | Upstream requirement IDs preserved without modification | **PASS** |
| 4 | `test_w54_jurisdiction_and_regulatory_area_context_preserved` | Context dictionary hints (jurisdiction, area) parsed into traceability | **PASS** |
| 5 | `test_w54_advice_query_text_reaches_pipeline` | Advice query text reaches generator and is preserved verbatim in response | **PASS** |
| 6 | `test_w54_success_response_returned_correctly` | Grounded single-source query returns `SUCCESS` and `RAG_SUPPORTED` | **PASS** |
| 7 | `test_w54_conflict_detected_response_returned_correctly` | Co-retrieved conflicts return `CONFLICT_DETECTED` and `RAG_REVIEW_REQUIRED` | **PASS** |
| 8 | `test_w54_gap_detected_response_returned_correctly` | Absent provision returns `GAP_DETECTED`, `RAG_GAP_DETECTED`, 0 citations | **PASS** |
| 9 | `test_w54_no_source_found_remains_safe` | Approved-only query against candidate corpus returns `NO_SOURCE_FOUND` | **PASS** |
| 10 | `test_w54_rag_errors_represented_correctly` | Pipeline failure maps to `ERROR` and `RAG_ERROR` without leaking secrets | **PASS** |
| 11 | `test_w54_citations_provenance_remain_attached` | Citations and provenance records remain attached and populated | **PASS** |
| 12 | `test_w54_correlation_request_id_preserved` | Request correlation ID preserved across in-process adapter and HTTP API | **PASS** |
| 13 | `test_w54_unauthorized_project_context_fails_closed` | Supplying foreign/unassigned project ID fails closed (0 chunks returned) | **PASS** |
| 14 | `test_w54_candidate_records_remain_fail_closed` | Candidate records flagged (`is_approved_for_rag=False`); gating holds | **PASS** |
| 15 | `test_w54_no_legal_professional_decision_made` | Mandatory disclaimer present; objective relationship reporting verified | **PASS** |

**Pass Rate:** **15 / 15 Passed (100.0%)** in 23.88s.

---

## 13. Full Regression Test Verification

Ran complete regression suite:
```powershell
python -m pytest -q
```
- **Passed:** **548**
- **Failed:** **0**
- **Errors:** **0**
- **Baseline Growth:** 533 (post-W5.3) $\to$ **548** (+15 tests).

---

## 14. Ownership Boundaries & Governance Split

### PADMA IMPLEMENTED (AI/RAG Lead):
- Designed and implemented [`AdviceRAGAdapter`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_adapter.py).
- Wired adapter into [`api/routes/query.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/query.py) and [`api/dependencies.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/dependencies.py).
- Implemented `AdviceTraceabilityContext`, `AdviceRAGResult`, and `AdviceWorkflowStatus`.
- Maintained 100% W4.11 contract compatibility and fail-closed security.
- Authored and verified 15 dedicated integration tests (548/548 full regression).

### VISHAL DEPENDENCY (Backend Lead):
- Implement PostgreSQL/SQLModel models for `advice_requests`, `advice_responses`, `advice_citations`.
- Manage authenticated user sessions and OAuth2/JWT tokens.
- Perform server-side validation and authorization of `project_id`.
- Orchestrate business workflows and route `RAG_REVIEW_REQUIRED` tasks to compliance officers.

### HARSHINI DEPENDENCY (Frontend Lead):
- Build Advice authoring view and project/requirement selectors.
- Render grounded answers, interactive citation pills, and slide-out provenance drawers.
- Render side-by-side conflict cards and non-adjudication disclaimers.
- Display Candidate development warning banners and human-review badges.

---

## 15. Sign-off

Task W5.4 is **COMPLETE**. The RAG capability is fully operational inside the Advice workflow, supporting both in-process Python calls and microservice REST invocations.
