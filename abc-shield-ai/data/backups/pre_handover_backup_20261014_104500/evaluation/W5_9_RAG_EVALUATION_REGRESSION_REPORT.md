# Week 5.9 RAG Evaluation & Regression Report

**Role:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Task:** TASK W5.9 — RAG Evaluation & Regression  
**Date:** October 8, 2026  
**Status:** COMPLETE & FULLY VERIFIED (642/642 Tests Passing)  

---

## 1. Objective

The objective of Task W5.9 is to establish empirical, verifiable evidence that the integrated Week 5 RAG system (encompassing W5.1 Integration Readiness, W5.2 Backend Contract Alignment, W5.3 Frontend Support, W5.4 Advice Workflow Adapter, W5.5 Advice Comparison, W5.6 Conflict/Relationship Detection, W5.7 Regulatory $\leftrightarrow$ RAG Boundary, and W5.8 Regulatory $\leftrightarrow$ Advice Traceability) satisfies all retrieval, grounding, citation, provenance, gap, conflict, comparison, security, and stability requirements without any regression from the frozen Week 4.7 baseline.

Governance constraints strictly observed:
- Zero algorithmic hacks or artificial threshold tuning.
- Zero modifications to raw Excel registers or canonical JSON artifacts.
- Zero mutations to the persistent ChromaDB collection (exactly 15 vectors preserved).
- Zero alterations to approval states (all 15 records remain `Candidate - Awaiting Approval`, 0 Approved).
- Zero fabricated evaluation scores or synthetic label overrides.

---

## 2. Existing Evaluation Assets Inspected

Before conducting the evaluation, all existing evaluation assets and test suites were systematically inspected:
1. `data/evaluation/W4_7_retrieval_baseline_report.md`: Documented retrieval baseline established on September 30, 2026.
2. `data/evaluation/evaluation_cases.json`: 34 benchmark cases covering Categories A through O (21 applicable retrieval cases, 13 zero-expected/safety cases).
3. `rag/evaluation/`:
   - `evaluation_dataset.py`: `EvaluationDatasetValidator` validating schemas and target IDs against the active register.
   - `retrieval_evaluator.py`: `RetrievalEvaluator` computing deduplicated Precision@K, Recall@K, Hit Rate@K, and MRR.
   - `generation_evaluator.py`: Grounding and faithfulness evaluation against reference targets.
   - `safety_evaluator.py`: Safety, prompt-injection, and forbidden adjudication checks.
   - `evaluation_models.py`: Pydantic models for case results and aggregate metrics.
4. Existing test suites across Weeks 4 and 5:
   - `tests/test_retrieval_baseline.py` (W4.7 baseline verification)
   - `tests/test_grounded_generation_w48.py` (W4.8 grounding verification)
   - `tests/test_evidence_gap_w49.py` (W4.9 gap handling verification)
   - `tests/test_conflict_handling_w410.py` (W4.10 conflict detection verification)
   - `tests/test_structured_output.py` (W4.11 wire contract verification)
   - `tests/test_rag_backend_contract_w52.py` (W5.2 contract alignment)
   - `tests/test_rag_frontend_contract_w53.py` (W5.3 frontend integration support)
   - `tests/test_rag_advice_workflow_w54.py` (W5.4 advice workflow adapter)
   - `tests/test_rag_advice_comparison_w55.py` (W5.5 advice comparator)
   - `tests/test_conflict_relationship_integration_w56.py` (W5.6 relationship integration)
   - `tests/test_regulatory_rag_integration_w57.py` (W5.7 boundary verification)
   - `tests/test_regulatory_advice_traceability_w58.py` (W5.8 traceability verification)

---

## 3. W4.7 Baseline

The frozen Week 4.7 retrieval baseline measured on September 30, 2026 against the active ChromaDB index (`regulatory_records`, 15 vectors, `all-MiniLM-L6-v2`, 384 dimensions) across the 21 applicable benchmark cases was:

- **Evaluated Cases ($N$):** 21
- **Zero-Expected Cases:** 13
- **Precision@1:** `0.9048`
- **Precision@3:** `0.4444`
- **Precision@5:** `0.2762`
- **Recall@1:** `0.7381`
- **Recall@3:** `0.9762`
- **Recall@5:** `1.0000`
- **Hit Rate@1:** `0.9048`
- **Hit Rate@3:** `1.0000`
- **Hit Rate@5:** `1.0000`
- **Mean Reciprocal Rank (MRR):** `0.9524`

---

## 4. Current Retrieval Metrics

Empirical rerun executed on October 8, 2026 using `RetrievalEvaluator().evaluate_all(benchmark_cases, top_k=5)` against the live ChromaDB vector store:

- **Evaluated Cases ($N$):** 21
- **Zero-Expected Cases:** 13
- **Precision@1:** `0.9048`
- **Precision@3:** `0.4444`
- **Precision@5:** `0.2762`
- **Recall@1:** `0.7381`
- **Recall@3:** `0.9762`
- **Recall@5:** `1.0000`
- **Hit Rate@1:** `0.9048`
- **Hit Rate@3:** `1.0000`
- **Hit Rate@5:** `1.0000`
- **Mean Reciprocal Rank (MRR):** `0.9524`

---

## 5. Metric Comparison

| Metric | W4.7 Baseline | Week 5 Measured | Absolute Delta | Relative Change | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precision@1** | 0.9048 | 0.9048 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Precision@3** | 0.4444 | 0.4444 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Precision@5** | 0.2762 | 0.2762 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Recall@1** | 0.7381 | 0.7381 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Recall@3** | 0.9762 | 0.9762 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Recall@5** | 1.0000 | 1.0000 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Hit Rate@1** | 0.9048 | 0.9048 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Hit Rate@3** | 1.0000 | 1.0000 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **Hit Rate@5** | 1.0000 | 1.0000 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |
| **MRR** | 0.9524 | 0.9524 | 0.0000 | 0.0% | **IDENTICAL (PASS)** |

**Conclusion:** Zero retrieval regression occurred across all Week 5 feature enhancements and pipeline integrations.

---

## 6. Retrieval Qualitative Results

Qualitative evaluation verified key statutory inquiries:
1. **UK Bribery Act 2010 Section 1:** Retained at **Rank 1** (Cosine similarity: 0.8192). Correctly retrieves `RR-UK-01-C01`.
2. **MoJ Six Principles Guidance:** Retained at **Rank 1** (Cosine similarity: 0.7511). Correctly retrieves `RR-UK-02-C01`.
3. **Cross-Instrument Co-retrieval:** Queries addressing corporate bribery prevention co-retrieve primary legislation (`UK-01`) and secondary guidance (`UK-02`) in top-3 results.
4. **Jurisdiction Filtering:** Scoping retrieval by `jurisdiction="UK"` excludes EU records while retaining UK statutory provisions without degradation.

---

## 7. Grounding Evaluation

Verified via `GroundedGenerator.generate_structured_response()`:
- Answers are strictly derived from supplied context chunks.
- No legal conclusions, penalties, or statutory duties outside retrieved chunks are generated.
- When all evidence chunks have `validation_status="Candidate - Awaiting Approval"`, `metadata.has_candidate_evidence = True` and candidate warnings are attached.
- Status is mapped to `ResponseStatus.GROUNDED` and external status `SUCCESS` or `CONFLICT_DETECTED`.

---

## 8. Citation Evaluation

Verified deterministic citation mechanics:
- Citations reference only retrieved chunks (zero citation hallucination).
- Citation IDs follow canonical format `CIT-RR-{JUR}-{ID}-C{CHUNK}`.
- Official URLs point exclusively to verified authoritative registries (`legislation.gov.uk`, `eur-lex.europa.eu`, `justice.gov.uk`).
- Zero broken or fabricated hyperlinks exist.
- Detached citations (citations pointing to unretrieved chunks) are strictly forbidden and verified as 0.

---

## 9. Provenance Evaluation

Full audit lineage verified:
- Every citation has a 1-to-1 matching `ProvenanceRecord`.
- Provenance attributes include `chunk_id`, `record_id`, `source_id`, `regulation`, `regulator`, `jurisdiction`, `section_article`, `title`, `official_source`, `validation_status`, and `is_approved_for_rag`.
- Zero internal server paths (`D:\...`, `C:\...`) or database secrets are exposed in provenance records or serialized JSON payloads.

---

## 10. Evidence-Gap Evaluation

Verified deterministic gap classification via `GapHandler`:
- **Unrepresented Statutory Provision (`CASE-02`):** Queries seeking Section 7 corporate failure to prevent bribery produce `GapType.MISSING_SPECIFIC_PROVISION` and `coverage_nature="CORPUS_COVERAGE_LIMITATION"`.
- **User-Safe Messaging:** Discloses that Section 7 is not present in the ABC Shield corpus without asserting that Section 7 does not exist in UK law and without accusing the advisor of legal error.
- **External Status:** Mapped cleanly to `GAP_DETECTED`.

---

## 11. No-Source Evaluation

Evaluated zero-evidence handling:
- Queries with zero matching evidence or executed under `filter_approved_only=True` return `GapType.UNAPPROVED_EVIDENCE` or `NO_RETRIEVED_EVIDENCE`.
- Response status maps to `ResponseStatus.UNAPPROVED_EVIDENCE`.
- Product wire status maps to `NO_SOURCE_FOUND`.
- LLM generation is skipped; citations and provenance are empty (`[]`).

---

## 12. Unsupported-Question Evaluation

Evaluated out-of-corpus domain inquiries:
- Queries covering operational resilience (DORA), cybersecurity (NIS2), data protection (GDPR), crypto-assets (MiCA), or general taxation are classified as `GapType.OUT_OF_SCOPE`.
- System abstains from legal advice and issues a structured disclaimer.
- External status maps to `GAP_DETECTED`.

---

## 13. Conflict / Relationship Evaluation

Evaluated integration between `ConflictDetector` and Week 5 workflows:
- Co-retrieval of UK BA 2010 (`UK-01`) and MoJ Guidance (`UK-02`) triggers registered relationship `CO-001` (`OVERLAP`).
- Taxonomy strictly preserved: `CONFLICT`, `OVERLAP`, `SCOPE_DIFFERENCE`, `AUTHORITY_DIFFERENCE`, `VERSION_DIFFERENCE`.
- Commentary remains neutral and descriptive without declaring one source superior or invalid.
- Human review is mandated (`requires_human_review = True`).

---

## 14. Advice Comparison Evaluation

Evaluated `AdviceComparator` pairwise comparison between Advisor 1 and Advisor 2:
- Detects substantive differences, scope variances, and direct contradictions.
- Connects supporting regulatory chunks and evidence status (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`).
- Mandates human SME review when differences or contradictions occur.
- **CRITICAL INVARIANT:** `decision` remains strictly `None` at the RAG layer. The RAG system never declares a winning advisor.

---

## 15. Traceability Evaluation

Verified end-to-end trace navigation helpers:
- `AdviceComparisonResult.get_evidence_trace_for_advice(advice_id)` resolves advice text to supporting chunks, citations, and provenance.
- `AdviceComparisonResult.get_conflict_trace(conflict_id)` resolves relationship findings to cited chunks and provenance.
- `AdviceComparisonResult.get_full_traceability_summary()` provides complete correlation from `comparison_id`, `request_id`, and `project_id` down to regulatory evidence.
- `AdviceRAGResult.get_evidence_trace()` provides direct correlation for single advice query processing.

---

## 16. Security / Approval Evaluation

Verified security and approval boundaries:
- **Approval Gating:** All 15 records in the knowledge base remain `Candidate - Awaiting Approval`. Executing queries with `filter_approved_only=True` returns exactly 0 records (fail-closed).
- **Tenant & Project Isolation:** Passing an unauthorized `project_id` isolates retrieval and returns 0 records, preventing cross-tenant vector leakage.
- **Payload Schema Hardening:** Pydantic models enforce `extra="forbid"`, rejecting rogue client parameters with HTTP 422.

---

## 17. Failure / Limitation Evaluation

Evaluated controlled error handling:
- Empty queries (`""`) and whitespace queries (`"   "`) are rejected cleanly at Pydantic validation boundaries with `ValidationError` / HTTP 422.
- Out-of-bounds `top_k` values are safely clamped to `[1, 20]`.
- System exceptions produce structured `ERROR` statuses without leaking internal stack traces or environment variables.

---

## 18. Full Regression Result

The full automated regression suite was executed via pytest:

- **Command:** `python -m pytest -q`
- **Previous Baseline:** 628 passed
- **New Dedicated Tests Added:** 14 tests (`tests/test_rag_evaluation_regression_w59.py`)
- **Total Test Count:** **642 passed**
- **Failures:** **0**
- **Errors:** **0**
- **Execution Time:** **50.40s**

---

## 19. Metric Changes & Explanation

- **Precision@1:** 0.9048 (Unchanged, 0.0000 delta)
- **Recall@1:** 0.7381 (Unchanged, 0.0000 delta)
- **HitRate@1:** 0.9048 (Unchanged, 0.0000 delta)
- **MRR:** 0.9524 (Unchanged, 0.0000 delta)

**Explanation:** No metric shifts occurred because the underlying ChromaDB vector store, embedding model (`all-MiniLM-L6-v2`), chunk segmentation, and canonical regulatory records were preserved with 100% bitwise immutability. The Week 5 integrations (adapters, comparators, traceability helpers) operate cleanly as orchestration wrappers without modifying the core vector retrieval logic.

---

## 20. Known Limitations

1. **Candidate-Only Status:** All 15 canonical records currently have validation status `Candidate - Awaiting Approval`. Production deployment requires formal compliance SME sign-off.
2. **Dense Semantic Bi-Encoder Limitations:** The dense vector model (`all-MiniLM-L6-v2`) excels at semantic conceptual search but can rank broad conceptual guidance above specific statutory section numbers when queries lack explicit statutory terminology. Hybrid retrieval (BM25 + Dense vector with Reciprocal Rank Fusion) is recommended for post-MVP enhancements.
3. **Corpus Coverage:** Section 7 of the UK Bribery Act 2010 (Failure of commercial organisations to prevent bribery) is not yet ingested into the candidate corpus. The system safely detects this as a `CORPUS_COVERAGE_LIMITATION`.

---

## 21. Padma Ownership

Completed by Padma Kumar (AI/RAG & Conflict Detection Engineer):
- Verified empirical retrieval baseline concordance (P@1=0.9048, MRR=0.9524).
- Verified grounding, citation authenticity, and provenance lineage integrity.
- Verified safe evidence-gap disclosure and out-of-scope domain handling.
- Verified non-adjudication invariants in `AdviceComparator` and conflict detection.
- Verified end-to-end traceability helpers in `AdviceComparisonResult` and `AdviceRAGResult`.
- Authored 14 comprehensive evaluation regression tests (`tests/test_rag_evaluation_regression_w59.py`).
- Confirmed full test suite pass (642/642 tests passing).

---

## 22. Vishal Dependencies

- Multi-tenant JWT authorization enforcement at API gateway.
- Database persistence for advice sessions, comparison records, and SME audit decisions.
- Storage of human compliance reviews when `requires_human_review = True`.

---

## 23. Harshini Dependencies

- Frontend rendering of provenance drawers, citation chips, and confidence indicators.
- Side-by-side comparison view displaying Advisor 1 vs Advisor 2 positions, identified differences, and supporting chunk badges.
- Mandatory display of the non-adjudication disclaimer on all RAG and Comparison screens.

---

## 24. Madhesh Dependencies

- Integrity of raw Excel workbooks and canonical regulatory record schemas.
- Formal SME review to transition Candidate records to Approved status in future ingestion cycles.

---

## Evaluation Summary Table (Step 17)

| Evaluation Area | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Precision@1** | 0.9048 (W4.7 baseline) | 0.9048 | **PASS** |
| **Recall@1** | 0.7381 (W4.7 baseline) | 0.7381 | **PASS** |
| **HitRate@1** | 0.9048 (W4.7 baseline) | 0.9048 | **PASS** |
| **MRR** | 0.9524 (W4.7 baseline) | 0.9524 | **PASS** |
| **Source Grounding** | Grounded in retrieved chunks; candidate warning attached | Verified grounded; caveats present | **PASS** |
| **Citation Correctness** | Formatted IDs; authentic official URLs; zero hallucinations | Canonical format; verified URLs | **PASS** |
| **Provenance** | Complete traceable audit lineage; no internal credential leaks | Full metadata present; zero leaks | **PASS** |
| **No-Source Handling** | Safe NO_SOURCE_FOUND; zero fabricated statutes | Returns safe status; empty citations | **PASS** |
| **Evidence Gaps** | Safe disclosure (CORPUS_COVERAGE_LIMITATION); non-blaming | Safe gap message; no advisor blame | **PASS** |
| **Conflict Detection** | Descriptive only; CO-001..CO-011 taxonomy preserved | Detected CO-001; non-adjudicative | **PASS** |
| **Advice Comparison** | Contradictions detected; decision = None strictly preserved | Differences found; decision is None | **PASS** |
| **Traceability** | Complete trace from advice ID to chunks and provenance | Navigation helpers fully verified | **PASS** |
| **Approval Gating** | Fail-closed under filter_approved_only=True (returns 0) | Returns 0 chunks; fail-closed verified | **PASS** |
| **Project Isolation** | Enforced via tenant context; schema rejects rogue fields | 0 leakage; extra="forbid" enforced | **PASS** |
