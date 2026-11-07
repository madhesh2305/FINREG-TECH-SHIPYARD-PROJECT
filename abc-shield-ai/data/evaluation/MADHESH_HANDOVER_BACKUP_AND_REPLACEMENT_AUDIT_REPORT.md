# Madhesh Regulatory Knowledge Handover: Backup & File Replacement Audit Report

**Author:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Date:** 2026-10-14  
**Audit Objective:** Non-destructive pre-replacement audit, backup verification, schema comparison, discrepancy analysis, and reconciliation strategy for Madhesh's new regulatory knowledge handover.  
**Audit Action:** AUDIT ONLY — ZERO ACTIVE FILES MODIFIED OR OVERWRITTEN.  

---

## 1. Project Root & Current Architecture Inspection

- **Project Root Directory:** `D:\FInregTech Shipyard\abc-shield-ai`
- **Current Active Regulatory Data (`data/raw/`):**
  - `ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` (15 active RAG records, 15 sources in Source Control, 10 RAG rules, 11 Conflict Overlap pairs `CO-001`..`CO-011`, 5 official verifications).
  - `ABC_Shield_Source_Register_Reviewed (1).xlsx` (15 reviewed sources across 22 columns with review notes).
  - `ABC shield_Data Dictionary.xlsx` (18 field definitions under sheet `Sheet1`).
  - `ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` (legacy reference).
  - `ABC_Shield_Source_Register (1).xlsx` (legacy reference).
- **Current Processed Artifacts (`data/processed/`):**
  - `normalized_regulatory_records.json` (15 records, SHA256: `5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d`).
  - `regulatory_chunks.json` (15 chunks, SHA256: `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef`).
- **Current Vector Store (`data/processed/chroma_db/`):**
  - Collection: `regulatory_records`
  - Total Vectors: **15** (Embedding model: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, cosine distance).
- **Current Ingestion Pipeline Files (`rag/ingestion/`):**
  - `excel_loader.py`: Loads Excel workbooks in read-only mode using openpyxl.
  - `schemas.py`: Pydantic models for Source Register, Normalized Records, Chunks, Conflicts, Rules.
  - `normalizer.py`: Maps raw Excel rows into `NormalizedRegulatoryRecord` and joins with Source Register.
  - `chunker.py`: Chunks normalized records into `RegulatoryChunk` models.
  - `validator.py`: Validates schema conformance and fail-closed approval gating.
- **Current Configuration (`config/settings.py`):**
  - `data_raw_dir = Path("data/raw")`
  - `data_processed_dir = Path("data/processed")`
  - `chroma_persist_dir = Path("data/processed/chroma_db")`
  - `chroma_collection_name = "regulatory_records"`

---

## 2. Handover Files & Replacement Intent

Madhesh's finalized handover package was identified at:  
`C:\Users\askla\Downloads\ABC_Shield_Finalized_Base_Complete\`

| Incoming Handover File | Source Subdirectory | Intended Role in Project | Target Existing File to Replace / Supersede |
|---|---|---|---|
| `ABC_Shield_Canonical_Source_Register.xlsx` | `Source_Register/` | Canonical Single Source Register (15 sources) | Supersedes `data/raw/ABC_Shield_Source_Register_Reviewed (1).xlsx` |
| `ABC_Shield_Canonical_25_Record_Corpus.xlsx` | `Regulatory_Research/` | 25-record curated working corpus | Supersedes `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` (15 records) |
| `ABC shield_Data Dictionary.xlsx` | `Data_Dictionary/` | Updated field definitions (18 fields) | Supersedes `data/raw/ABC shield_Data Dictionary.xlsx` |
| `ABC_Shield_Canonical_RAG_Test_Pack.xlsx` | `RAG Research/` | 15 prepared canonical RAG test cases | **NEW File** (to be added to `data/raw/` or `data/evaluation/`) |
| `ABC_Shield_Master_Handover_Tracker.xlsx` | `Handover/` | Master handover governance & open decisions | **NEW File** (to be added to `data/` for governance) |
| `README_ABC_Shield_FINAL.md` | `Handover/` | Handover documentation & exit criteria | **NEW File** (reference document) |
| `ABC Shield _scope note.docx` | Root | Programme scope boundaries & limitations | **NEW File** (reference document) |
| `ABC Shield.docx` | `SME_Questions/` | Outstanding SME approval questions | **NEW File** (reference document) |

---

## 3. Timestamped Backup Verification

Before inspecting or staging, a complete timestamped backup of all existing data assets was created:

- **Backup Path:** `D:\FInregTech Shipyard\abc-shield-ai\data\backups\pre_handover_backup_20261014_104500\`
- **Contents Backed Up:**
  - `raw/`: All 5 existing raw Excel workbooks and `.gitkeep`.
  - `processed/`: `normalized_regulatory_records.json`, `regulatory_chunks.json`, and complete `chroma_db/` directory.
  - `evaluation/`: All evaluation reports, prompt fixtures, and baseline JSON files.
- **Verification Metrics:** Exactly **50 files**, **1,518,532 bytes** verified.
- **Integrity Guarantee:** Zero files in the active directories (`data/raw/`, `data/processed/`, `data/chroma_db/`) were modified, deleted, or overwritten.

---

## 4. Staging of Incoming Handover Files

To strictly respect boundary rules and prevent pollution of the active production workspace:
- **Staging Path:** `D:\FInregTech Shipyard\abc-shield-ai\data\incoming_handover_20261014\`
- **Status:** All 15 files/directories from Madhesh's handover package are staged in complete isolation. Active pipeline files and ChromaDB continue pointing exclusively to `data/raw/` and `data/processed/`.

---

## 5. Detailed Technical Comparison: Existing vs Incoming

### A. Record Counts & Record IDs
- **Existing Corpus:**
  - Total Records: **15**
  - Record IDs: `RR-UK-01` through `RR-UK-10`, `RR-EU-01` through `RR-EU-06`.
  - Coverage: Exactly 1 record per source across 15 distinct sources.
- **Incoming Corpus:**
  - Total Records: **25**
  - Record IDs: `UK-01-R001` .. `UK-01-R006`, `UK-02-R001` .. `UK-02-R006`, `UK-03-R001` .. `UK-03-R005`, `EU-01-R001` .. `EU-01-R007`, `UK-09-R001`.
  - Coverage: Multi-record extraction concentrated across **5 core extraction sources**:
    - `UK-01` (Bribery Act 2010): 6 records (Sections 1, 2, 6, 7, 8, 9).
    - `UK-02` (MOJ Adequate Procedures Guidance): 6 records (Principles 1, 2, 3, 4, 5, 6).
    - `UK-03` (FCA FCG 6): 5 records (FCG 6.1.1, 6.2.1, 6.2.2, 6.2.3, 6.2.4).
    - `EU-01` (EU Proposed Directive COM(2023) 234): 7 records (Articles 1, 3, 4, 13, 16, 20, 21).
    - `UK-09` (FCA Principles for Businesses): 1 record (PRIN 2.1.1R - Principle 1).
  - **Key Observation:** The other 10 sources (`UK-04`, `UK-05`, `UK-06`, `UK-07`, `UK-08`, `EU-02`, `EU-03`, `EU-04`, `EU-05`, `EU-06`) have **0 active corpus records** in the 25-record set. They are preserved in the Source Register as Supporting or Deferred sources.

### B. Source Register Comparison
- **Source IDs:** Both registers contain the exact same 15 Source IDs (`UK-01`..`UK-09`, `EU-01`..`EU-06`).
- **Status Classification Shift:**
  - Existing: All 15 sources had `Status = "Candidate - Awaiting Approval"`.
  - Incoming:
    - 5 sources: `Status = "Approved for Extraction - Pending SME Validation"` (`UK-01`, `UK-02`, `UK-03`, `EU-01`, `UK-09`).
    - 3 sources: `Status = "Approved as Supporting Source - Pending SME Validation"` (`UK-04`, `UK-08`, `EU-02`).
    - 6 sources: `Status = "Deferred"` (`UK-05`, `UK-06`, `UK-07`, `EU-03`, `EU-04`, `EU-05`).
    - 1 source: `Status = "Deferred / Monitor"` (`EU-06`).
- **Column Schema:**
  - Existing: 22 columns (included `ABC Shield Relevance / In-Scope Rationale`, `Extraction Priority`, `Adoption Date`, etc.).
  - Incoming: 18 columns (added `Regulatory Layer`, `Programme Decision / Scope Note`, `Corpus_Status_Current`, `Corpus_Record_Count`, `Reconciliation_Note`).

### C. Corpus Schema & Column Discrepancies
- **Sheet Names:**
  - Existing RAG workbook sheet: `RAG_Records`
  - Incoming 25-record workbook sheet: `Regulatory_Records`
  - *Risk:* `excel_loader.py` currently looks for `"RAG_Records"` or `"Regulatory Records"` (with a space). Direct loading would fail with `ValueError`.
- **Column Mapping:**
  - Existing `RAG_Records` (25 columns) included pre-computed RAG fields: `Chunk_ID`, `Requirement`, `Retrieval_Text`, `Citation_Label`, `Retrieval_Tags`, `Authority_Rule`, `RAG_Instruction`.
  - Incoming `Regulatory_Records` (18 columns) separates verbatim extract from plain-English summary:
    - `Exact_Source_Extract` (verbatim quote from source)
    - `Structured_Summary` (requirement summary)
    - `Source_Name` (previously `Regulation_Name`)
    - `Official_URL` (previously `Official_Source_URL`)
    - `Regulatory_Layer` (new field)
  - *Risk:* `normalizer.py` strictly requires a column named `Requirement`. If passed `Regulatory_Records` directly, it raises `ValueError: Requirement is mandatory but missing for record UK-01-R001`.

### D. Critical Conflict Handling Discrepancy
- Existing `ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` contains a dedicated sheet: `Conflict_Handling` with 11 pre-mapped regulatory conflict and overlap records (`CO-001` through `CO-011`).
- Incoming `ABC_Shield_Canonical_25_Record_Corpus.xlsx` **DOES NOT CONTAIN** the `Conflict_Handling` sheet.
- *Critical Risk:* If `ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` were directly replaced or overwritten, `ConflictDetector` (which reads from this workbook) would load 0 conflict records, breaking relationship detection and all Week 4/5 conflict tests!

### E. Validation Status & Approval Integrity
- **Existing Records:** `Validation_Status = "Candidate - Awaiting Approval"`.
- **Incoming Records:**
  - `Status = "Approved for Extraction"`
  - `Validation_Status = "Pending SME Validation"`
- **Strict Compliance Rule:** Both Madhesh's README and project rules confirm: **`Approved for Extraction` is NOT final SME approval**. All 25 records remain `Pending SME Validation`. In the RAG layer, `is_approved_for_rag` must strictly remain `False` until formal compliance SME signoff.

### F. Data Dictionary Discrepancy
- Existing: Sheet name is `Sheet1` (18 rows).
- Incoming: Sheet name is `Data_Dictionary` (19 rows, added `Used By` column).
- *Risk:* `excel_loader.py` hardcodes `Sheet1` for Data Dictionary loading.

---

## 6. Actionability & Replacement Classification

| File Category | Specific Files | Recommendation | Action Required Before Replacement |
|---|---|---|---|
| **Safely Replaceable (with config update)** | `ABC_Shield_Canonical_Source_Register.xlsx`<br>`ABC_Shield_Canonical_RAG_Test_Pack.xlsx`<br>`ABC_Shield_Master_Handover_Tracker.xlsx` | **REPLACE / ADD** | Update `excel_loader.py` to recognize `Canonical_Source_Register` filename and column schema. |
| **Requires Field Mapping & Reconciliation (DO NOT DIRECTLY OVERWRITE)** | `ABC_Shield_Canonical_25_Record_Corpus.xlsx`<br>`ABC shield_Data Dictionary.xlsx` | **RECONCILE FIRST** | 1. Add column alias mapping (`Structured_Summary` $\to$ `Requirement`, `Exact_Source_Extract` $\to$ `Regulatory_Text`, `Source_Name` $\to$ `Regulation_Name`).<br>2. Update sheet name resolution to accept `Regulatory_Records` and `Data_Dictionary`.<br>3. Preserve `Conflict_Handling` sheet (`CO-001`..`CO-011`). |
| **Must Remain Unchanged** | `data/processed/chroma_db/`<br>`normalized_regulatory_records.json`<br>`regulatory_chunks.json` | **HOLD UNCHANGED** | Do not rebuild ChromaDB or update processed JSON until reconciliation script is executed and approved. |

---

## 7. Impact on Test Suite & Backward Compatibility

- **Current Full Regression Baseline:** **675 / 675 tests passing** (verified 100% green).
- **Test Dependencies on Legacy Structure:**
  - 21 test files contain direct assertions on `RR-UK-01`..`RR-UK-10` and `RR-EU-01`..`RR-EU-06`.
  - 28 test files contain assertions expecting a record/chunk/vector count of `15`.
  - 4 test files test the 11 registered conflict relationships (`CO-001`..`CO-011`).
- **Preservation Strategy:**
  - Replacement of active files without adapter logic would cause widespread test failures across 28 test suites.
  - An ingestion adapter must be implemented that maps incoming 25 records into `NormalizedRegulatoryRecord` while preserving backward-compatible retrieval and test fixtures.

---

## 8. Recommended Integration & Replacement Sequence

Once the audit report is reviewed and approved, the integration should proceed in this strict order:

1. **Step 1: Ingestion Loader Adaptation (`rag/ingestion/excel_loader.py`)**
   - Support `Regulatory_Records` sheet name alongside `RAG_Records`.
   - Support `Data_Dictionary` sheet name alongside `Sheet1`.
   - Add graceful column fallback: `Requirement` $\leftarrow$ `Structured_Summary`, `Regulatory_Text` $\leftarrow$ `Exact_Source_Extract`.
2. **Step 2: Conflict Dataset Preservation**
   - Ensure the 11 conflict relationships (`CO-001`..`CO-011`) are preserved either by carrying the `Conflict_Handling` sheet forward or maintaining it as a dedicated conflict register.
3. **Step 3: Staged Normalization & Chunking Validation**
   - Run a non-destructive normalization test generating 25 normalized records in memory.
   - Verify all 25 records evaluate to `is_approved_for_rag = False` (`Pending SME Validation`).
4. **Step 4: Active File Swap & Reprocessing**
   - Copy canonical files into `data/raw/`.
   - Re-run normalization to produce updated `normalized_regulatory_records.json` (25 records).
   - Re-run chunking to produce updated `regulatory_chunks.json`.
5. **Step 5: Vector Store Re-indexing**
   - Re-index `chroma_db` from 15 to 25 chunks using `reindex_chromadb.py`.
6. **Step 6: Test Suite & Regression Alignment**
   - Align record count and ID assertions in the test suite to support the 25 records.
   - Run the 15 new test cases from `ABC_Shield_Canonical_RAG_Test_Pack.xlsx`.
   - Verify full regression passes.

---

## 9. Current Status & Halt

**AUDIT COMPLETE.**  
- Backup created: `data/backups/pre_handover_backup_20261014_104500` (Verified).  
- Staging directory created: `data/incoming_handover_20261014` (Isolated).  
- Active files: 100% UNCHANGED.  
- ChromaDB: UNTOUCHED.  
- Tests: 675/675 PASSING.  

*Per instruction: Execution halted. No replacements will be performed until user review of this report.*
