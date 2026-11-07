# Week 4.6 Test Alignment Report: Realigning Downstream Test Expectations for Week 4 Corpus

**Role:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Task:** TASK W4.6-TEST-ALIGNMENT — Realign Downstream Test Expectations for Week 4  
**Date:** September 29, 2026  
**Status:** COMPLETE & FULLY VERIFIED (260/260 Tests Passing)

---

## 1. Executive Summary

Following the successful Week 4 ChromaDB vector re-indexing (Task W4.6 Core), 139/139 focused ingestion, schema, source-control, normalization, chunking, and re-indexing tests passed. However, when executing the broader regression suite, exactly 6 downstream tests failed.

Investigation confirmed that **zero failures** were due to regressions in RAG components or database corruption. Instead, all 6 failing tests were written during earlier sprints (Tasks 5, 6, 7, 10, 11) where assertions explicitly codified **known deficiencies of the sparse Week 3 regulatory corpus**:
1. **Bribery Act Section 1 Rank Deficiency:** In Week 3, the brief title-only text caused Section 1 (`RR-UK-01-C01`) to rank #4, so a query with `top_k=3` failed to retrieve it. In Week 4, enriched `retrieval_text` elevated Section 1 to **Rank 1** (cosine similarity `0.8192`).
2. **Absence of DORA:** In Week 3, DORA was entirely absent from the corpus, so queries regarding DORA triggered evidence gaps. In Week 4, DORA Article 5 is present as `RR-EU-02-C01`.
3. **Absence of Section 7 Details:** In Week 3, Section 7 was missing from the corpus. In Week 4, Section 7 is explicitly referenced in `RR-UK-01-C01`'s retrieval notes, causing retrieval overlap.

Under Task W4.6-TEST-ALIGNMENT, we safely realigned ONLY these 6 obsolete downstream test expectations without touching any production code, without weakening safety guardrails, without re-indexing ChromaDB, and without modifying any canonical data artifacts.

---

## 2. Alignment Matrix: Detailed Test Realignment Analysis

| # | Test File | Test Identifier | Week 3 Obsolete Assumption | Week 4 Corpus Reality | Alignment Action Taken | Safety / Integrity Verification |
|---|---|---|---|---|---|---|
| **1** | `tests/test_generation.py` | `test_1a_bribery_act_top_k_3_insufficient_evidence_preserves_honest_grounding` | Bribery Act Section 1 is absent at `top_k=3` (ranked #4), asserting `INSUFFICIENT_EVIDENCE`. | Section 1 (`RR-UK-01-C01`) is ranked #1 (similarity `0.8192`), hence present in `top_k=3`. | Updated test to assert grounded response with `RR-UK-01-C01` retrieved at `top_k=3`, validating honest grounding on retrieved evidence. | Preserves honest grounding principle: model grounds when evidence is present; `test_3` continues to verify ungrounded/gap behavior on out-of-scope queries. |
| **2** | `tests/test_citations.py` | `test_7_bribery_act_top_k_3_no_citation_for_rr_uk_01` | Section 1 is absent at `top_k=3`, asserting zero citations for `RR-UK-01-C01`. | `RR-UK-01-C01` is retrieved at Rank 1 in `top_k=3`. | Updated test to assert that `RR-UK-01-C01` IS cited when retrieved at `top_k=3`, verifying citation metadata fidelity. | Preserves citation integrity: `test_5` and `test_6` continue to assert zero citations when retrieval is empty or evidence insufficient. |
| **3** | `tests/test_gap_handler.py` | `test_3_bribery_act_top_k_3_produces_missing_specific_provision` | Section 1 is absent from `top_k=3` results of live retriever, expecting `MISSING_SPECIFIC_PROVISION`. | Live retriever returns `RR-UK-01-C01` at Rank 1. | Injected mock retriever returning valid chunks that omit Section 1 (e.g. `RR-UK-07-C01`). | Unit test isolation: deterministically asserts that when Section 1 is missing, `MISSING_SPECIFIC_PROVISION` gap is identified, isolated from corpus ranking changes. |
| **4** | `tests/test_evaluation.py` | `test_evaluation_runner_failure_analysis_populated` | Section 1 is ranked > 1 (specifically #4), asserting `retrieved_at_k1 is False`. | Section 1 is ranked #1 in exact provision analysis (`retrieved_at_k1 is True`). | Updated assertions to `retrieved_at_k1 is True` and `rank_in_retrieval == 1`. | Benchmark correctness: failure analysis tool accurately measures exact provision ranking on the active index. |
| **5** | `tests/test_api.py` | `test_insufficient_evidence_passes_through_correctly` | Live Section 7 query returns `INSUFFICIENT_EVIDENCE` because Section 7 was missing from corpus. | Section 7 is mentioned in `RR-UK-01-C01` retrieval text, causing retriever to find evidence. | Used dependency injection (`app.dependency_overrides[get_grounded_generator]`) with mock generator returning `INSUFFICIENT_EVIDENCE` (matching pattern in `test_10`). | API layer contract verification: verifies HTTP 200 with `status="INSUFFICIENT_EVIDENCE"`, `grounded=False`, and complete GAP schema, decoupled from corpus contents. |
| **6** | `tests/test_api.py` | `test_gap_remains_server_generated` | DORA query triggers GAP because DORA was missing from corpus. | DORA Article 5 is present in Week 4 corpus (`RR-EU-02-C01`). | Updated query to `"What cybersecurity requirements apply to financial entities?"` (authentic out-of-scope query). | Verifies that when a GAP is triggered, the response GAP structure is server-generated with `gap_type` and `user_safe_message`. |

---

## 3. Test Suite Execution & Verification

### A. Realigned Suites Execution
Command: `pytest tests/test_generation.py tests/test_citations.py tests/test_gap_handler.py tests/test_evaluation.py tests/test_api.py -v`  
- **Total Tests:** 76  
- **Passed:** 76  
- **Failed:** 0  
- **Execution Time:** 138.14s  

### B. Week 4 Core Focused Suites Execution
Command: `pytest tests/test_chromadb_reindex.py tests/test_chunks.py tests/test_retrieval.py tests/test_normalized_records.py tests/test_source_control_approval.py tests/test_ingestion.py -q`  
- `test_chromadb_reindex.py`: 22 passed  
- `test_chunks.py`: 26 passed  
- `test_retrieval.py`: 15 passed  
- `test_normalized_records.py`: 26 passed  
- `test_source_control_approval.py`: 25 passed  
- `test_ingestion.py`: 25 passed  
- **Total Focused Tests:** 139  
- **Passed:** 139  
- **Failed:** 0  
- **Execution Time:** 57.55s  

### C. Full Repository Regression Suite Execution
Command: `pytest -q` across entire repository  
- **Total Tests:** 260  
- **Passed:** 260  
- **Failed:** 0  
- **Errors:** 0  
- **Execution Time:** 225.94s (0:03:45)  
- **Regression Pass Rate:** 100.0%  

---

## 4. Corpus & Database Immutability Audit

In strict compliance with the task rules, zero modifications were made to data files, upstream models, or the ChromaDB index during this alignment task:

| Artifact / Resource | Expected State | Actual Verified State | Hash Match / Count |
|---|---|---|---|
| `data/processed/normalized_regulatory_records.json` | `5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d` | Verified unchanged | **PASS** |
| `data/processed/regulatory_chunks.json` | `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef` | Verified unchanged | **PASS** |
| `data/raw/ABC shield_Data Dictionary.xlsx` | `57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6` | Verified unchanged | **PASS** |
| `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` | `2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b` | Verified unchanged | **PASS** |
| `data/raw/ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` | `5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00` | Verified unchanged | **PASS** |
| `data/raw/ABC_Shield_Source_Register (1).xlsx` | `0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b` | Verified unchanged | **PASS** |
| `data/raw/ABC_Shield_Source_Register_Reviewed (1).xlsx` | `fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4` | Verified unchanged | **PASS** |
| ChromaDB `regulatory_records` Vector Count | Exactly 15 vectors | 15 vectors (9 UK, 6 EU) | **PASS** |
| Production Source Code (`rag/`, `api/`) | Unmodified | 0 production files touched | **PASS** |

---

## 5. Scope & Guardrail Adherence Confirmation

1. **Production Code Scope:** Only 5 downstream test files (`tests/test_generation.py`, `tests/test_citations.py`, `tests/test_gap_handler.py`, `tests/test_evaluation.py`, `tests/test_api.py`) were modified. No lines of code in `rag/` or `api/` were altered.
2. **Approval Status Gating:** All 15 vectors in ChromaDB retain `validation_status = "Candidate - Awaiting Approval"` and `is_approved_for_rag = False`. Gating logic continues to block unapproved records from authoritative production responses.
3. **ChromaDB Integrity:** The database was NOT re-indexed, deleted, or rebuilt. Vector counts, dimensions (384), and metadata remain identical to the W4.6 core baseline.
4. **No Premature Execution:** W4.7 (or any subsequent task) has NOT been started. Execution has stopped cleanly for user review.

---

## 6. Conclusion & Status

Task W4.6-TEST-ALIGNMENT is **COMPLETE**. The test suite across the entire repository is now 100% aligned with the Week 4 enriched regulatory corpus, with all 260 tests passing and zero regressions.
