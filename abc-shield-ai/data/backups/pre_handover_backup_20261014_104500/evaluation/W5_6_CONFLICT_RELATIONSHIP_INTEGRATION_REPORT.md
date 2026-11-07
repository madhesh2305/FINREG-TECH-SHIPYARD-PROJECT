# WEEK 5 — TASK W5.6: CONFLICT / RELATIONSHIP INTEGRATION REPORT

---

## 1. Document Control

| Attribute | Specification |
| :--- | :--- |
| **Task Reference** | **WEEK 5 — TASK W5.6: Conflict / Relationship Integration** |
| **Document Version** | **1.0.0** |
| **Date** | **October 7, 2026** |
| **Role / Lead Author** | **Padma Kumar** — AI/RAG & Conflict Detection Engineer |
| **Project** | **ABC Shield / FinRegTech ShipYard AI/RAG** |
| **Collaborators** | **Vishal** (Backend Lead), **Harshini** (Frontend Lead), **Sanjay** (API Gateway / Infrastructure Lead) |
| **Preceding Verified Baseline** | **564 / 564 Tests Passing** |
| **New Regression Baseline** | **584 / 584 Tests Passing (100.0% Pass Rate)** |
| **Corpus Invariant** | **15 Canonical Regulatory Records (15 Candidate / 0 Approved), ChromaDB = 15 Vectors** |
| **Status** | **COMPLETE** |

---

## 2. Objective & Scope

Task W5.6 cleanly integrates the existing W4.10 Conflict/Relationship detection capability (`CO-001` through `CO-011`) into the Week 5 Advice/RAG comparison workflow (`AdviceComparator` established in W5.5).

### Core Goals Verified:
1. **Consistent Representation**: Preserves the canonical W4.10 relationship taxonomy (`CONFLICT`, `OVERLAP`, `SCOPE_DIFFERENCE`, `AUTHORITY_DIFFERENCE`, `VERSION_DIFFERENCE`) without invented severity scores or artificial confidences.
2. **Traceability**: Connects conflict findings to upstream request context (`comparison_id`, `request_id`, `project_id`, `requirement_ids`, `advisor_ids`).
3. **Evidence Grounding**: Connects registered relationships to retrieved regulatory chunks (`retrieved_chunk_ids`, `retrieved_source_ids`, `citations`, `provenance`).
4. **Three-Tier Grounding Separation**: Strictly separates Tier A (registered regulatory metadata), Tier B (retrieved ChromaDB evidence), and Tier C (inferred advisor differences).
5. **Safety & Non-Adjudication**: Preserves `decision = None`, forbids `correct_advisor` fields, flags `human_review_required = True`, and enforces mandatory non-adjudication disclaimers.
6. **Backend & Frontend Safety**: Exposes structured Pydantic models with `extra="forbid"`, JSON-serializable payloads, and explicit boolean/enum indicators.

---

## 3. Three-Tier Grounding Architecture

To avoid conflation between regulatory facts, retrieved text, and advisor opinions, W5.6 establishes and enforces a strict three-tier separation:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    THREE-TIER GROUNDING MODEL                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TIER A: REGISTERED REGULATORY METADATA (Conflict Overlap Register CO-001..CO-011)             │
│  - Sourced from: Controlled Excel register loaded at startup                                    │
│  - Field: result.relationships: List[ConflictFinding]                                            │
│  - Nature: Objective statutory/regulatory relationship documented between source pairs           │
│  - Taxonomy: CONFLICT, OVERLAP, SCOPE_DIFFERENCE, AUTHORITY_DIFFERENCE, VERSION_DIFFERENCE       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TIER B: RETRIEVED REGULATORY EVIDENCE (ChromaDB Vector Store)                                   │
│  - Sourced from: Dense vector similarity search across canonical corpus chunks                   │
│  - Fields: result.supporting_evidence, result.citations, result.provenance                       │
│  - Nature: Factual regulatory provisions retrieved to substantiate advisor claims                │
│  - Invariants: Verifiable chunk IDs, source IDs, record IDs (RR-*), and candidate status         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TIER C: INFERRED ADVISOR DIFFERENCES (Advice Comparison Logic)                                  │
│  - Sourced from: Semantic difference analysis between Advisor 1 and Advisor 2 advice texts       │
│  - Field: result.differences: List[AdviceDifference]                                             │
│  - Nature: Heuristic identification of position variations and potential contradictions          │
│  - Taxonomy: NO_DIFFERENCE, SUBSTANTIVE_DIFFERENCE, SCOPE_DIFFERENCE, etc.                       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

These three tiers are completely distinct and never merged into a single generic bucket.

---

## 4. Components Modified & Verified

### 4.1. [`rag/pipeline/advice_comparator.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_comparator.py)
- **`AdviceComparisonRequest`**: Added optional `request_id: Optional[str] = None` field to support end-to-end request tracing across backend orchestration.
- **`ComparisonTraceabilityContext`**: Added `request_id: Optional[str] = None` field.
- **`AdviceComparator.compare_advice()`**:
  - Accepts `request_id: Optional[str] = None`.
  - Propagates `request_id` to `traceability.request_id` (defaulting cleanly to `comparison_id` if omitted).
  - Propagates `relationships` (Tier A) from `ConflictDetector.detect(retrieved_chunks)`.
  - Enforces `human_review_required = True` whenever `len(relationships) > 0`.
- **`AdviceComparator.compare_from_request()`**:
  - Propagates `request.request_id` into `compare_advice()`.

### 4.2. [`api/routes/compare.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/compare.py)
- Reused existing `POST /api/v1/compare` endpoint.
- Validates that `request_id` is seamlessly accepted, validated, and returned in the HTTP response.
- Rejects undeclared extra fields via `extra="forbid"`.

### 4.3. [`rag/conflict/conflict_detector.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/conflict/conflict_detector.py)
- Unmodified; 100% reused from W4.10.
- All 11 registered pairs (`CO-001` through `CO-011`) load deterministically.
- Deterministic relationship mapping via `classify_relationship()` verified.

---

## 5. Verification Matrix: 20 Dedicated Tests

The test suite [`tests/test_conflict_relationship_integration_w56.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_conflict_relationship_integration_w56.py) covers all 20 required verification scenarios:

| # | Test Name | Target Behavior | Result |
| :---: | :--- | :--- | :---: |
| 1 | `test_w56_canonical_taxonomy_preservation` | Canonical taxonomy preserved; no invented severity or confidence scores | **PASSED** |
| 2 | `test_w56_conflict_detector_co_register_loaded` | Real `ConflictDetector` loads exactly 11 controlled records (CO-001..CO-011) | **PASSED** |
| 3 | `test_w56_relationship_classification_overlap` | `classify_relationship` maps complementary overlaps to `OVERLAP` | **PASSED** |
| 4 | `test_w56_relationship_classification_scope_difference` | `classify_relationship` maps scope variances to `SCOPE_DIFFERENCE` | **PASSED** |
| 5 | `test_w56_relationship_classification_authority_difference` | `classify_relationship` maps authority variances to `AUTHORITY_DIFFERENCE` | **PASSED** |
| 6 | `test_w56_relationship_classification_version_difference` | `classify_relationship` maps amendments/versions to `VERSION_DIFFERENCE` | **PASSED** |
| 7 | `test_w56_relationship_classification_direct_conflict` | `classify_relationship` maps direct contradictions to `CONFLICT` | **PASSED** |
| 8 | `test_w56_advice_comparator_detects_co_relationships` | Co-retrieving documented sources (UK-01 and UK-02) surfaces `ConflictFinding` | **PASSED** |
| 9 | `test_w56_three_tier_separation` | Strict architectural separation between Tier A, Tier B, and Tier C | **PASSED** |
| 10 | `test_w56_supporting_regulatory_evidence_connection` | Conflict findings link to actual retrieved chunk IDs and source IDs | **PASSED** |
| 11 | `test_w56_provenance_integrity_for_conflict_findings` | Sources in conflict findings have verifiable `ProvenanceRecord` entries | **PASSED** |
| 12 | `test_w56_traceability_context_includes_request_and_project_ids` | Traceability contains `comparison_id`, `request_id`, `project_id`, `requirement_ids` | **PASSED** |
| 13 | `test_w56_human_review_flag_triggered_on_relationships` | `human_review_required=True` when relationships exist, even if advice texts match | **PASSED** |
| 14 | `test_w56_strict_non_adjudication_invariant` | `decision=None`, no `correct_advisor` field, mandatory disclaimer enforced | **PASSED** |
| 15 | `test_w56_candidate_records_fail_closed_under_approved_filter` | `filter_approved_only=True` returns 0 chunks and 0 relationships safely | **PASSED** |
| 16 | `test_w56_safe_evidence_gaps_preserved` | Unrepresented provisions (e.g. Section 7) generate safe `GapResult` | **PASSED** |
| 17 | `test_w56_project_isolation_enforced` | Tenant `project_id` isolation enforced without cross-tenant leakage | **PASSED** |
| 18 | `test_w56_w54_advice_adapter_compatibility` | W5.4 `AdviceRAGAdapter` functions seamlessly without regressions | **PASSED** |
| 19 | `test_w56_http_api_compare_serialization` | `POST /api/v1/compare` returns HTTP 200 with serialized relationships & traceability | **PASSED** |
| 20 | `test_w56_http_api_extra_forbid_rejection` | Injected unauthorized fields rejected with HTTP 422 (`extra="forbid"`) | **PASSED** |

---

## 6. Full Regression Results

Execution of the full automated test suite:

```powershell
$env:HF_HUB_OFFLINE='1'; & "d:\FInregTech Shipyard\.venv\Scripts\python.exe" -m pytest -q
........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 36%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 73%]
........................................................................ [ 86%]
........................................................................ [ 98%]
........                                                                 [100%]
584 passed in 117.71s (0:01:57)
```

- **Total Tests Passed**: **584**
- **Failures**: **0**
- **Errors**: **0**
- **Skipped**: **0**
- **Pass Rate**: **100.0%**

---

## 7. Corpus & Security Invariants Preserved

1. **Canonical Regulatory Corpus**:
   - 15 records in `data/processed/canonical_records.json` remain untouched.
   - 15 records remain `Candidate - Awaiting Approval` (0 Approved).
   - Raw Excel source workbooks in `data/raw/` remain unmodified.
2. **ChromaDB**:
   - Exactly 15 vectors preserved.
   - Zero vector re-indexing or re-embedding.
3. **Locked Integration Contract (W4.11)**:
   - `POST /api/v1/query` and `POST /api/v1/compare` contracts fully respected.
   - Zero breaking changes to `StructuredAIResponse` or existing response models.
4. **Ownership Boundaries Respected**:
   - No frontend code touched (Harshini's boundary preserved).
   - No database persistence or business workflow touched (Vishal's boundary preserved).
   - Strict non-adjudication: AI never picks a winner (`decision = None`).
