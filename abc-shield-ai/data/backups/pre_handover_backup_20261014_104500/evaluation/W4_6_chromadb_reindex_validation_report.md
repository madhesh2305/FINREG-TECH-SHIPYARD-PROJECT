# TASK W4.6 — EMBEDDINGS & CHROMADB RE-INDEXING REPORT

**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Role:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Date:** 2026-09-29  
**Status:** BLOCKED (Pending Padma's Review on Downstream Regression Test Realignment)  

---

## 1. Executive Summary

Task W4.6 rebuilt the local persistent ChromaDB regulatory vector index (`regulatory_records` collection at `data/processed/chroma_db/`) using the 15 canonical Week 4 RAG chunks from `data/processed/regulatory_chunks.json`.

All indexing operations were executed 100% locally on CPU using `sentence-transformers` model `all-MiniLM-L6-v2`. Zero remote APIs or external embedding services were called. The re-indexed store contains exactly 15 vectors (9 UK, 6 EU) matching the upstream canonical chunk IDs (`RR-UK-01-C01` through `RR-EU-06-C01`), with strictly 384 dimensions, cosine distance metric, full Week 4 enriched metadata, fail-closed candidate approval gating (`is_approved_for_rag = False`), and verified disk persistence across fresh `PersistentClient` restarts.

All 139 focused unit tests across ingestion, chunks, normalized records, source control, and retrieval passed. However, in accordance with **Stop Condition 31** and **Rule 37**, Task W4.6 is marked **BLOCKED** because 6 downstream regression tests from Tasks 5–11 failed. The root cause is documented in Section 27: the Week 4 enriched `retrieval_text` successfully eliminated previous Week 3 retrieval deficiencies (Section 1 of the Bribery Act 2010 now ranks at #1 instead of #4, and DORA and Section 7 are now present in the corpus), causing downstream tests that hardcoded Week 3 ranking failures and missing provisions to fail.

---

## 2. Input Artifact

- **File Path:** `data/processed/regulatory_chunks.json`
- **File Mode:** Strictly Read-Only
- **Pre-execution SHA-256:** `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef`
- **Post-execution SHA-256:** `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef` (100% Unchanged)
- **Total Chunks Loaded:** 15

---

## 3. Embedding Model & Execution

- **Library:** `sentence-transformers`
- **Model Name:** `all-MiniLM-L6-v2`
- **Execution Mode:** Local / CPU Inference (Zero external network calls)
- **Normalization:** L2-normalized embeddings (`normalize_embeddings=True`)
- **Measured Embedding Dimension:** 384

---

## 4. ChromaDB Vector Store & Configuration

- **Collection Name:** `regulatory_records`
- **Persistence Path:** `data/processed/chroma_db/`
- **Distance Metric:** `cosine` (`{"hnsw:space": "cosine"}`)
- **Persistence Mechanism:** `chromadb.PersistentClient`

---

## 5. Before / After Re-Indexing Comparison

| Dimension / Metric | Before Re-Indexing (Week 3 Residuals) | After Re-Indexing (Week 4 Canonical) | Status |
|:---|:---|:---|:---|
| **Collection Count** | 15 vectors | 15 vectors | **Preserved (15)** |
| **Document Content** | Legacy concise requirement paraphrase (e.g. `"It is an offence to offer, promise or give..."`) | Canonical Week 4 `retrieval_text` (e.g. `"Source: UK-01 \| UK Parliament... Section 1: Offences of bribing..."`) | **Updated to W4** |
| **UK Chunks** | 9 | 9 (`RR-UK-01-C01` .. `RR-UK-09-C01`) | **Aligned** |
| **EU Chunks** | 6 | 6 (`RR-EU-01-C01` .. `RR-EU-06-C01`) | **Aligned** |
| **Embedding Dimension**| 384 | 384 | **Verified** |
| **Metadata Fields** | 19 basic fields | 26 scalar metadata fields (including all 7 Week 4 enriched fields) | **Enriched** |
| **Text Type** | `"requirement_paraphrase"` | `"retrieval_text"` | **Verified** |
| **Approval Status** | 15 Candidate / 0 Approved | 15 Candidate / 0 Approved | **Fail-Closed** |

---

## 6. Vector & Chunk Alignment (1:1 Mapping)

Every chunk in `data/processed/regulatory_chunks.json` has a corresponding vector in ChromaDB with matching ID, text, and metadata:

| Chunk ID | Record ID | Source ID | Jurisdiction | Regulation | Stored Text Match | Embedding Dim | Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `RR-UK-01-C01` | `RR-UK-01` | `UK-01` | UK | Bribery Act 2010 | 100% Match | 384 | Candidate |
| `RR-UK-02-C01` | `RR-UK-02` | `UK-02` | UK | Bribery Act 2010 – Guidance | 100% Match | 384 | Candidate |
| `RR-UK-03-C01` | `RR-UK-03` | `UK-03` | UK | FCA Financial Crime Guide – FCG 6 | 100% Match | 384 | Candidate |
| `RR-UK-04-C01` | `RR-UK-04` | `UK-04` | UK | FSMA 2000 (Section 59) | 100% Match | 384 | Candidate |
| `RR-UK-05-C01` | `RR-UK-05` | `UK-05` | UK | SM&CR (Rule 2.1) | 100% Match | 384 | Candidate |
| `RR-UK-06-C01` | `RR-UK-06` | `UK-06` | UK | Sanctions and AML Act 2018 | 100% Match | 384 | Candidate |
| `RR-UK-07-C01` | `RR-UK-07` | `UK-07` | UK | FCA FG21/4 Guidance | 100% Match | 384 | Candidate |
| `RR-UK-08-C01` | `RR-UK-08` | `UK-08` | UK | Bank of England SS1/21 | 100% Match | 384 | Candidate |
| `RR-UK-09-C01` | `RR-UK-09` | `UK-09` | UK | JMLSG Guidance Part I | 100% Match | 384 | Candidate |
| `RR-EU-01-C01` | `RR-EU-01` | `EU-01` | EU | Directive (EU) 2026/1021 | 100% Match | 384 | Candidate |
| `RR-EU-02-C01` | `RR-EU-02` | `EU-02` | EU | DORA (Regulation (EU) 2022/2554) | 100% Match | 384 | Candidate |
| `RR-EU-03-C01` | `RR-EU-03` | `EU-03` | EU | CSDDD (Directive (EU) 2024/1760) | 100% Match | 384 | Candidate |
| `RR-EU-04-C01` | `RR-EU-04` | `EU-04` | EU | MiFID II (Directive 2014/65/EU) | 100% Match | 384 | Candidate |
| `RR-EU-05-C01` | `RR-EU-05` | `EU-05` | EU | GDPR (Regulation (EU) 2016/679) | 100% Match | 384 | Candidate |
| `RR-EU-06-C01` | `RR-EU-06` | `EU-06` | EU | EU AI Act (Regulation (EU) 2024/1689) | 100% Match | 384 | Candidate |

- **Missing IDs:** 0
- **Obsolete IDs:** 0
- **Duplicate IDs:** 0

---

## 7. Metadata & Week 4 Enriched Fields Verification

All 15 vectors store the following fields in ChromaDB metadata:
1. `chunk_id`
2. `record_id`
3. `source_id`
4. `regulation`
5. `regulator`
6. `jurisdiction`
7. `section_article`
8. `title`
9. `topic`
10. `official_source`
11. `version_date`
12. `effective_date`
13. `validation_status`
14. `is_approved_for_rag`
15. `text_type` (`"retrieval_text"`)
16. `authority_level`
17. `source_type`
18. `chunk_index`
19. `total_chunks`
20. `content_type`
21. `retrieval_tags` (Stored as clean semicolon-delimited string, e.g. `"Bribery; Corruption; Section 1; UK-01"`, 100% semantically recoverable)
22. `citation_label`
23. `retrieval_priority`
24. `authority_rule`
25. `rag_instruction`
26. `official_source_check_note`

---

## 8. Regulatory Gating & Approval Controls

- **Candidate Vectors:** 15 (`validation_status == "Candidate - Awaiting Approval"`)
- **Approved Vectors:** 0 (`is_approved_for_rag == False`)
- **Approved-Only Filtering Test (`filter_approved_only=True`):** Returns exactly **0 results**
- **Candidate-Inclusive Retrieval (`filter_approved_only=False`):** Returns candidate records with explicit candidate warning
- **UK Jurisdiction Filtering (`jurisdiction="UK"`):** Returns strictly UK records (100% UK, 0% EU)
- **EU Jurisdiction Filtering (`jurisdiction="EU"`):** Returns strictly EU records (100% EU, 0% UK)

---

## 9. Persistence Reopen Test

The persistent collection was verified by re-instantiating a fresh `chromadb.PersistentClient(path="data/processed/chroma_db")`:
- Count on disk: **15**
- Vector dimension: **384**
- Documents: All 15 start with `"Source: "` and match canonical text
- Metadata: All 15 retain `is_approved_for_rag = False` and Week 4 fields

---

## 10. Retrieval Smoke Test

Query: *"What does the Bribery Act 2010 say about bribing another person?"*
- **Rank 1 Chunk:** `RR-UK-01-C01` (Section 1: Offences of bribing another person)
- **Similarity Score:** `0.8192` (Substantial improvement over Week 3 baseline of 0.5758)
- **Cosine Distance:** `0.1808`
- **Execution:** Succeeded with structured `RetrievalResult` and candidate status preserved.

---

## 11. Test Results Summary

### A. Focused Test Suites (139 / 139 Passed — 100%)
| Test File | Tests Run | Passed | Failed |
|:---|:---|:---|:---|
| `tests/test_chromadb_reindex.py` (New W4.6 Suite) | 22 | 22 | 0 |
| `tests/test_chunks.py` | 26 | 26 | 0 |
| `tests/test_ingestion.py` | 25 | 25 | 0 |
| `tests/test_normalized_records.py` | 26 | 26 | 0 |
| `tests/test_source_control_approval.py` | 25 | 25 | 0 |
| `tests/test_retrieval.py` | 15 | 15 | 0 |
| **Total Focused Tests** | **139** | **139** | **0** |

### B. Full Regression Suite (`pytest -q`)
- **Total Tests Collected:** 260
- **Passed:** 254
- **Failed:** 6 (Downstream tests from Tasks 5–11)
- **Execution Time:** 198.81s

---

## 12. Root Cause Analysis of Downstream Regression Failures

The 6 test failures in `test_api.py`, `test_citations.py`, `test_evaluation.py`, `test_gap_handler.py`, and `test_generation.py` did NOT occur because of any defect in ChromaDB or W4.6 indexing. They occurred because the Week 3 downstream test suites hardcoded the specific deficiencies and missing content of the Week 3 corpus:

1. **`test_api.py::test_insufficient_evidence_passes_through_correctly`**:
   - Query: *"What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?"*
   - In Week 3, Section 7 was missing from the corpus, so the test asserted status was `INSUFFICIENT_EVIDENCE`.
   - In Week 4, Section 7 is explicitly referenced in `RR-UK-01-C01`'s retrieval text and source notes, so the generator now finds grounded evidence and returns `GROUNDED`.

2. **`test_api.py::test_gap_remains_server_generated`**:
   - Query: *"What are the DORA operational resilience requirements?"*
   - In Week 3, DORA was missing from the corpus, so the test asserted `data["gap"] is not None`.
   - In Week 4, DORA Article 5 is present as canonical record `RR-EU-02-C01`, so the system retrieves DORA and returns grounded evidence (`gap` is `None`).

3. **`test_citations.py::test_7_bribery_act_top_k_3_no_citation_for_rr_uk_01`**, **`test_gap_handler.py::test_3_bribery_act_top_k_3_produces_missing_specific_provision`**, & **`test_generation.py::test_1a_bribery_act_top_k_3_insufficient_evidence_preserves_honest_grounding`**:
   - Query: *"What does the Bribery Act 2010 say about bribing another person?"* with `top_k=3`.
   - In Week 3, because the chunk text lacked full context, Section 1 (`RR-UK-01-C01`) ranked at **#4** (behind RR-UK-07, RR-UK-05, RR-UK-04). These tests explicitly asserted that Section 1 was absent from top 3 and triggered `INSUFFICIENT_EVIDENCE`.
   - In Week 4, thanks to `retrieval_text`, `RR-UK-01-C01`'s similarity score rose to **0.8192**, jumping directly to **Rank 1**. As a result, Section 1 is now present in the top 3 and the query returns `GROUNDED`.

4. **`test_evaluation.py::test_evaluation_runner_failure_analysis_populated`**:
   - Evaluator checked: `assert epa.retrieved_at_k1 is False` (asserting that Section 1 failed to be retrieved at k=1).
   - In Week 4, Section 1 IS retrieved at k=1, so `retrieved_at_k1` is `True`.

---

## 13. System Immutability & File Hashes

| File / Component | SHA-256 Checksum | Immutability Status |
|:---|:---|:---|
| `data/processed/normalized_regulatory_records.json` | `5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d` | **UNMODIFIED** |
| `data/processed/regulatory_chunks.json` | `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef` | **UNMODIFIED** |
| `data/raw/ABC shield_Data Dictionary.xlsx` | `57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6` | **UNMODIFIED** |
| `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` | `2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b` | **UNMODIFIED** |
| `data/raw/ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` | `5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00` | **UNMODIFIED** |
| `data/raw/ABC_Shield_Source_Register (1).xlsx` | `0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b` | **UNMODIFIED** |
| `data/raw/ABC_Shield_Source_Register_Reviewed (1).xlsx` | `fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4` | **UNMODIFIED** |

---

## 14. Files Modified in Task W4.6

1. [`rag/retrieval/vector_store.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/retrieval/vector_store.py):
   - Added `reset_collection()` for safe collection replacement.
   - Enhanced `_sanitize_metadata()` to include all Week 4 enriched fields.
2. [`rag/retrieval/__init__.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/retrieval/__init__.py):
   - Added `reset_collection: bool = True` parameter to `index_processed_chunks()`.
3. [`tests/test_retrieval.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_retrieval.py):
   - Allowed `retrieval_text` in assertions alongside `requirement_paraphrase`.
   - Allowed multi-jurisdiction semantic retrieval in test 13 while asserting top result is UK.
4. [`data/processed/chroma_db/`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/processed/chroma_db/):
   - Re-indexed with 15 Week 4 canonical vectors.
5. [`tests/test_chromadb_reindex.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_chromadb_reindex.py):
   - Created 22 comprehensive automated tests for W4.6 (all passing).

---

## 15. Recommendation & Next Steps

Task W4.6 indexing and persistence are completely successful. However, because downstream tests in Tasks 5, 6, 7, 10, 11 are coupled to Week 3 retrieval deficiencies, we must not expand scope or alter downstream test expectations without Padma's explicit guidance.

**Options for Padma's Review:**
1. **Realign Downstream Tests in W4.7 / W4.8**: Recognize that Week 4's enriched retrieval text resolved the Week 3 Section 1 ranking flaw, and update the test queries used for testing missing provisions / GAP handling to truly absent provisions (e.g. Section 99 of Bribery Act, environmental emissions standards) in W4.7 or W4.8.
2. **Authorize Minimal Test Updates now in W4.6**: Authorize updating the 6 downstream tests to use genuinely out-of-scope / missing queries so that the full regression suite achieves 260 / 260 passed before proceeding to W4.7.
