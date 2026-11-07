# STEP 1: INGESTION LOADER & NORMALIZER ADAPTATION REPORT

**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Role:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Date:** 2026-10-14  
**Status:** COMPLETE — 100% Regression Baseline Preserved  
**Regression Baseline:** 686 / 686 tests passing (675 existing baseline + 11 new dedicated Step 1 tests)  

---

## 1. Executive Summary

As part of integrating Madhesh's finalized regulatory knowledge handover, **Step 1: Ingestion Loader and Normalizer Adaptation** has been executed under strict engineering safeguards:

1. **Active Corpus & Vector Store Untouched:** Zero modifications were made to `data/raw/`, `data/processed/normalized_regulatory_records.json` (15 records), `data/processed/regulatory_chunks.json` (15 chunks), or `data/processed/chroma_db/` (15 vectors).
2. **Schema & Loader Modernized with Backward Compatibility:** The ingestion loaders (`ExcelDataLoader`), schemas (`SourceRegisterRecord`), and normalizer (`RegulatoryRecordNormalizer`) have been updated to seamlessly load and normalize both the legacy 15-record raw files and the new staged canonical 25-record files.
3. **Fail-Closed Candidate Gating:** All 25 incoming staged records are strictly normalized with `validation_status = 'Candidate - Awaiting Approval'` and `is_approved_for_rag = False`. No records are admitted into the approved tier.
4. **Deterministic Conflict Reference Preservation:** Conflict overlap relationships (`CO-001` through `CO-011`) are deterministically loaded from the verified active source workbook (`ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx`, sheet `"Conflict_Handling"`). If this sheet is missing, the loader fails fast with a clear error rather than falling back to an unverified file.
5. **Full Regression Validation:** 11 new dedicated unit tests were created in `tests/test_handover_step1_adaptation.py`. All 11 tests passed in 0.60s. The full project test suite passed with **686 / 686 tests passing** in 96.51s.

---

## 2. Staged File Inspection vs. Active Baseline

Prior to implementing any code adjustments, the staged handover files in `data/incoming_handover_20261014/` were inspected without assumptions:

| File Type | Staged Path | Actual Sheet Name | Dimensions / Headers Verified |
| :--- | :--- | :--- | :--- |
| **Regulatory Records (25)** | `data/incoming_handover_20261014/Regulatory_Research/ABC_Shield_Canonical_25_Record_Corpus.xlsx` | `Regulatory_Records` | 25 rows, 18 columns (including `Record_ID`, `Exact_Source_Extract`, `Structured_Summary`, `Domain_Categorisation`) |
| **Source Register (15)** | `data/incoming_handover_20261014/Source_Register/ABC_Shield_Canonical_Source_Register.xlsx` | `Source Register` | 15 rows, 18 columns (including `Source_ID`, `Issuing_Authority`, `Layer`, `Relevance_For_ABC_Shield`, `Notes`) |
| **Data Dictionary (18)** | `data/incoming_handover_20261014/Data_Dictionary/ABC shield_Data Dictionary.xlsx` | `Data_Dictionary` | 18 rows, 5 columns (`Field_Name`, `Field_Type`, `Required`, `Description`, `Allowed_Values`) |
| **Conflict Handling** | *Not present in staged handover workbooks* | N/A | **Verified Source Preserved:** Active `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx`, sheet `Conflict_Handling` (11 rows, `CO-001`..`CO-011`). |

---

## 3. Code Adaptations & Implementation Details

### A. `rag/ingestion/schemas.py`
- Extended `SourceRegisterRecord` with optional canonical metadata fields discovered in the canonical source register:
  - `regulatory_layer: Optional[str] = None`
  - `corpus_status_current: Optional[str] = None`
  - `corpus_record_count: Optional[int] = None`
  - `reconciliation_note: Optional[str] = None`
- **Maintained Exact Model Invariants:** Maintained exact 31-field count on `NormalizedRegulatoryRecord` and `RegulatoryChunk`. Existing serialization tests (`test_normalized_records.py` and `test_chunks.py`) strictly enforce `len(model_fields) == 31` to guarantee schema stability and exact JSON roundtrip fidelity.

### B. `rag/ingestion/excel_loader.py`
- Added canonical filename constants:
  - `CANONICAL_25_CORPUS_FILENAME = "ABC_Shield_Canonical_25_Record_Corpus.xlsx"`
  - `CANONICAL_SOURCE_REGISTER_FILENAME = "ABC_Shield_Canonical_Source_Register.xlsx"`
- Added recursive/subfolder lookup (`_find_file`) enabling `ExcelDataLoader` to discover workbooks whether placed directly in a flat directory or categorized into subfolders (`Regulatory_Research/`, `Source_Register/`, `Data_Dictionary/`).
- Updated `load_data_dictionary()`: Accepts sheet names `"Data_Dictionary"` and legacy `"Sheet1"`.
- Updated `load_source_register()`:
  - Mapped `Issuing_Authority` $\to$ `authority`.
  - Mapped `Layer` $\to$ `regulatory_layer`.
  - Mapped `Relevance_For_ABC_Shield` $\to$ `abc_shield_relevance`.
  - Mapped `Notes` $\to$ `source_qa_note`.
  - Disallows fabrication of metadata, dates, authority levels, URLs, or approval statuses.
- Updated `load_regulatory_records_raw()`: Accepts sheet names `"Regulatory_Records"`, `"RAG_Records"`, and `"Regulatory Records"`.
- Updated `load_conflict_overlap(conflict_path=None)`:
  - Added parameter `conflict_path`.
  - If not explicitly passed, falls back deterministically to verified source `ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx`.
  - Validates presence of sheet `"Conflict_Handling"`. If missing, raises a clear, descriptive `ValueError`. Never silently substitutes an unverified sheet or arbitrary file.

### C. `rag/ingestion/normalizer.py`
- **Mandatory Safeguard 4 Implemented:**
  - `raw_requirement = raw.get("Requirement") or raw.get("Structured_Summary")`.
  - If both are missing, raises a clear `ValueError(f"Record {rec_id} has neither 'Requirement' nor 'Structured_Summary'.")`.
  - **No Fallback to Source Extract:** Never falls back from requirement/summary to `Exact_Source_Extract`.
  - `verbatim_text = raw.get("Regulatory_Text") or raw.get("Exact_Source_Extract")`. Verbatim source excerpt is strictly preserved in `regulatory_text`.
- **Mandatory Candidate Gating:**
  - Evaluates `is_approved_for_rag = False` across all candidate records.
  - Normalizes `validation_status` to `'Candidate - Awaiting Approval'`.
  - "Approved for Extraction" in raw workbooks is strictly treated as extraction readiness, NOT RAG SME approval.
- **Enriched Retrieval Text & Citation Label Synthesis:**
  - If `retrieval_text` is not provided in raw columns, synthesizes a rich retrieval document combining Jurisdiction, Article/Section reference, Topic, Requirement, and Verbatim text excerpt.
  - If `citation_label` is absent, formats as `[{Record_ID}] {Source_Name}, {Article_Reference} ({Jurisdiction})`.

---

## 4. In-Memory Staged Processing Results

Normalizing and chunking the staged files in-memory without disk or vector-store side effects yielded the following verified counts:

1. **Raw Records Loaded:** 25 records (`RR-UK-01` through `RR-UK-15`, `RR-EU-01` through `RR-EU-10`).
2. **Normalized Records:** 25 normalized records.
3. **Approval Status:**
   - `is_approved_for_rag == False`: **25 / 25 records (100%)**
   - `is_approved_for_rag == True`: **0 records (0%)**
   - `validation_status == 'Candidate - Awaiting Approval'`: **25 / 25 records (100%)**
4. **Validation Pipeline (`RegulatoryRecordValidator`):**
   - Critical Errors: **0**
   - Candidate Records: **25**
   - Approved Records: **0**
5. **In-Memory Chunking (`RegulatoryRecordChunker`):**
   - Produced exactly **25 chunks** (1 chunk per record, preserving 1:1 record-to-chunk granularity).
   - All 25 chunks retain `is_approved_for_rag = False` and `validation_status = 'Candidate - Awaiting Approval'`.
6. **Conflict Handling Verification:**
   - Loaded exactly **11 conflict/overlap rows** (`CO-001` through `CO-011`).
   - Mapped correctly with primary records, conflicting records, overlap types, and notes.

---

## 5. Verification & Test Evidence

### A. Dedicated Step 1 Adaptation Test Suite
File: `tests/test_handover_step1_adaptation.py`  
Command: `& "d:\FInregTech Shipyard\.venv\Scripts\python.exe" -m pytest -v tests/test_handover_step1_adaptation.py`  
Result: **11 passed in 0.60s**

| Test Name | Verifies | Status |
| :--- | :--- | :--- |
| `test_staged_data_dictionary_loaded` | Data dictionary loads 18 field definitions from `ABC shield_Data Dictionary.xlsx` | PASSED |
| `test_staged_source_register_loaded` | Source register loads 15 sources from canonical file with mapped headers | PASSED |
| `test_staged_regulatory_records_raw_loaded` | Canonical 25-record corpus loads 25 raw dicts with sheet `Regulatory_Records` | PASSED |
| `test_staged_records_normalized_correctly` | Staged records normalize with `Structured_Summary` and verbatim extracts | PASSED |
| `test_requirement_does_not_fall_back_to_extract` | Missing summary raises `ValueError` rather than falling back to extract | PASSED |
| `test_all_25_incoming_records_are_candidate_status_and_not_approved` | Gating verification: all 25 are Candidate, 0 Approved | PASSED |
| `test_staged_validation_report_has_zero_critical_errors` | Validator produces 0 critical errors on staged corpus | PASSED |
| `test_staged_records_chunking_in_memory` | Chunker produces exactly 25 chunks from 25 normalized records | PASSED |
| `test_conflict_overlap_loads_co001_through_co011` | Conflict handling loads 11 rows `CO-001`..`CO-011` from verified source | PASSED |
| `test_conflict_overlap_fails_clearly_when_sheet_missing` | Fails fast with `ValueError` when conflict sheet is absent | PASSED |
| `test_active_raw_data_backward_compatibility` | 100% backward compatibility loading legacy active `data/raw/` files | PASSED |

### B. ChromaDB & Artifact Integrity Suite
Command: `& "d:\FInregTech Shipyard\.venv\Scripts\python.exe" -m pytest -v tests/test_chromadb_reindex.py`  
Result: **22 passed in 70.01s**
- Verifies collection count is strictly 15.
- Verifies `normalized_regulatory_records.json` and `regulatory_chunks.json` are unmodified.
- Verifies raw Excel workbooks in `data/raw/` match SHA-256 integrity hashes.

### C. Full Project Regression Suite
Command: `powershell -Command "[System.Environment]::SetEnvironmentVariable('HF_HUB_OFFLINE', '1'); & 'd:\FInregTech Shipyard\.venv\Scripts\python.exe' -m pytest -q"`  
Result: **686 passed in 96.51s (0:01:36)**  
- Existing baseline: 675 tests passed
- Added tests: 11 tests passed
- Total passing: **686 / 686 (100%)**
- Regressions / Failures: **0**

---

## 6. Safeguards & Boundary Confirmations

- [x] **Active `data/raw/` workbooks unchanged:** Cryptographic hash verification confirmed.
- [x] **Active `normalized_regulatory_records.json` unchanged:** Last modified 29-09-2026.
- [x] **Active `regulatory_chunks.json` unchanged:** Last modified 29-09-2026.
- [x] **Active ChromaDB unchanged:** Collection count remains 15 vectors.
- [x] **Original Downloads preserved:** `C:\Users\askla\Downloads\` untouched.
- [x] **Candidate-only tier enforced:** 0 records promoted to approved status.
- [x] **Conflict relationships preserved:** `CO-001` through `CO-011` loaded deterministically.
- [x] **Next Steps Gated:** No active files replaced, no active chunks regenerated, and no vector re-indexing executed. All subsequent steps require explicit user authorization.
