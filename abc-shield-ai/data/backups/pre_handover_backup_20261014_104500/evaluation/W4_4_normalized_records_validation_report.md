# Task W4.4 — Normalized Regulatory Records Validation Report

**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Engineer:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Date:** 29 September 2026  
**Status:** COMPLETE — Verified Against Canonical Source Records  

---

## 1. Objective

Task W4.4 regenerates, enriches, and validates the normalized regulatory records dataset:
`data/processed/normalized_regulatory_records.json`

The purpose is to transform Madhesh's reviewed Week 4 RAG-ready regulatory knowledge into typed internal representations that faithfully carry all enriched fields (Retrieval_Text, Retrieval_Tags, Citation_Label, Retrieval_Priority, Authority_Rule, RAG_Instruction, Official_Source_Check_Note, Chunk_ID) into the processed layer while strictly maintaining:
- 100% conceptual separation between `Requirement`, `Regulatory_Text`, and `Retrieval_Text`.
- Strict nullity for `regulatory_text` (zero legal text fabrication).
- Fail-closed approval gating (`is_approved_for_rag = False` across all 15 records).
- Total immutability of raw Excel files, ChromaDB (15 vectors), and `regulatory_chunks.json`.

---

## 2. Source Workbooks

The normalization pipeline utilized the approved Week 4 workbooks as primary sources of truth:

1. **Regulatory Records Knowledge Base:**  
   `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx`  
   - Primary sheet: `RAG_Records` (15 records, 25 columns)  
   - Control sheets: `Source_Control`, `RAG_Rules`, `Conflict_Handling`, `Official_Verification`  
2. **Reviewed Source Register:**  
   `data/raw/ABC_Shield_Source_Register_Reviewed (1).xlsx`  
   - Primary sheet: `Source Register` (15 sources, 22 columns)  
   - Control sheet: `Review Notes`  

Legacy Week 3 workbooks (`ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` and `ABC_Shield_Source_Register (1).xlsx`) remain fully supported as backward-compatible fallback paths.

---

## 3. Normalization Pipeline

The normalization architecture executes as follows:

```
[ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx]  [ABC_Shield_Source_Register_Reviewed (1).xlsx]
                 │                                                │
                 ▼                                                ▼
     ExcelWorkbookLoader                               ExcelWorkbookLoader
  (load_regulatory_records_raw)                       (load_source_register)
                 │                                                │
                 │ 15 raw row dicts                               │ 15 SourceRegisterRecords
                 └───────────────────────┬────────────────────────┘
                                         ▼
                             RegulatoryDataNormalizer
                             - Foreign-key join (Source_ID)
                             - Retrieval_Tags parsing (';' -> List[str])
                             - Official_Source_URL resolution
                             - Authority/Priority preservation
                             - Text separation enforcement
                                         │
                                         ▼
                         15 NormalizedRegulatoryRecord models
                             - @model_validator(mode="after")
                             - is_approved_for_rag fail-closed evaluation
                                         │
                                         ▼
                             RegulatoryDataValidator
                             - 13 guardrail checks (completeness, URL, types)
                             - Zero critical errors
                                         │
                                         ▼
                            export_normalized_records()
                                         │
                                         ▼
                 [data/processed/normalized_regulatory_records.json]
                                         │
                                         ▼
                           Round-Trip Verification
                        (Read back -> Pydantic reloaded)
```

---

## 4. Exact Files Modified

| File Path | Action | Description |
| :--- | :---: | :--- |
| `rag/ingestion/__init__.py` | **MODIFIED** | Added `export_normalized_records` pipeline runner and exported in `__all__`. |
| `data/processed/normalized_regulatory_records.json` | **REGENERATED** | Replaced Week 3 legacy JSON with full Week 4 enriched 15-record dataset. |
| `tests/test_normalized_records.py` | **CREATED** | 26 comprehensive automated normalization tests covering all prompt requirements. |
| `data/evaluation/W4_4_normalized_records_validation_report.md` | **CREATED** | Complete 25-section W4.4 audit report. |

**No other codebase files were modified.**  
`regulatory_chunks.json` was NOT modified.  
ChromaDB was NOT modified.  
Raw Excel workbooks were NOT modified.

---

## 5. Actual Normalized Schema Field Count

Inspection of the actual runtime Pydantic schema [`NormalizedRegulatoryRecord`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/ingestion/schemas.py#L97) and the serialized JSON output reveals:

- **Defined Pydantic Model Fields:** **`31`**
- **Exact Serialized Keys per JSON Record:** **`31`**

All 31 fields are serialized deterministically without omission:
```python
[
    'record_id', 'source_id', 'regulation', 'regulator', 'jurisdiction',
    'section_article', 'title', 'regulatory_text', 'requirement', 'summary',
    'topic', 'official_source', 'version_date', 'effective_date', 'validation_status',
    'applicability', 'relevance_to_project', 'notes_limitations', 'source_type',
    'authority_level', 'source_notes', 'is_approved_for_rag', 'chunk_id',
    'content_type', 'retrieval_text', 'retrieval_tags', 'citation_label',
    'retrieval_priority', 'authority_rule', 'rag_instruction', 'official_source_check_note'
]
```

---

## 6. Record Counts & Corpus Scope

- **Total Normalized Records:** **`15`**
- **Valid Records Count:** **`15`** (100% passed schema validation)
- **Candidate Records Count:** **`15`**
- **Approved Records Count:** **`0`**

---

## 7. UK / EU Jurisdictional Distribution

The 15 normalized records partition cleanly into 9 UK and 6 EU regulatory instruments:

| Jurisdiction | Record Count | Record ID Range | Key Statutes / Instruments |
| :--- | :---: | :--- | :--- |
| **UK** | **9** | `RR-UK-01` .. `RR-UK-09` | Bribery Act 2010, MOJ Guidance, FCA FCG 6, POCA 2002, MLR 2017, CFA 2017, SFO Guidance, CPS Guidance, FCA PRIN 2.1.1R |
| **EU** | **6** | `RR-EU-01` .. `RR-EU-06` | Directive (EU) 2026/1021, COM(2023) 234, 4AMLD, 5AMLD, Directive (EU) 2018/1673, Directive (EU) 2019/1937 |

---

## 8. Source Counts

- **Total Sources Resolved:** **`15`**
- **UK Sources:** 9 (`UK-01` through `UK-09`)
- **EU Sources:** 6 (`EU-01` through `EU-06`)
- **Foreign Key Join Rate:** **`15 / 15 (100%)`**
- **Orphan Records:** **`0`**

---

## 9. Chunk ID Preservation

Madhesh's pre-assigned upstream Chunk IDs were strictly preserved. No arbitrary IDs were generated:

| Record ID | Source ID | Upstream Chunk ID | Format Preserved |
| :--- | :--- | :--- | :---: |
| `RR-UK-01` | UK-01 | `RR-UK-01-C01` | **YES** |
| `RR-UK-02` | UK-02 | `RR-UK-02-C01` | **YES** |
| `RR-UK-03` | UK-03 | `RR-UK-03-C01` | **YES** |
| `RR-UK-04` | UK-04 | `RR-UK-04-C01` | **YES** |
| `RR-UK-05` | UK-05 | `RR-UK-05-C01` | **YES** |
| `RR-UK-06` | UK-06 | `RR-UK-06-C01` | **YES** |
| `RR-UK-07` | UK-07 | `RR-UK-07-C01` | **YES** |
| `RR-UK-08` | UK-08 | `RR-UK-08-C01` | **YES** |
| `RR-UK-09` | UK-09 | `RR-UK-09-C01` | **YES** |
| `RR-EU-01` | EU-01 | `RR-EU-01-C01` | **YES** |
| `RR-EU-02` | EU-02 | `RR-EU-02-C01` | **YES** |
| `RR-EU-03` | EU-03 | `RR-EU-03-C01` | **YES** |
| `RR-EU-04` | EU-04 | `RR-EU-04-C01` | **YES** |
| `RR-EU-05` | EU-05 | `RR-EU-05-C01` | **YES** |
| `RR-EU-06` | EU-06 | `RR-EU-06-C01` | **YES** |

Total Unique Chunk IDs: **15**.

---

## 10. Complete Field Mapping

Every normalized record maps data from the source workbooks according to explicit precedence rules:

| Normalized Field | Target Type | Primary Source (Week 4) | Fallback Source (Legacy) |
| :--- | :--- | :--- | :--- |
| `record_id` | `str` | `RAG_Records.Record_ID` | `Regulatory Records.Record_ID` |
| `source_id` | `str` | `RAG_Records.Source_ID` | `Regulatory Records.Source_ID` |
| `regulation` | `str` | `RAG_Records.Regulation_Name` | Joined `Source Register.Source Name` |
| `regulator` | `str` | `RAG_Records.Issuing_Authority` | Joined `Source Register.Issuing Authority` |
| `jurisdiction` | `str` | `RAG_Records.Jurisdiction` | Joined `Source Register.Jurisdiction` |
| `section_article` | `str` | `RAG_Records.Section_Article` | `Regulatory Records.Section_Article` |
| `title` | `str` | `RAG_Records.Title` | `Regulatory Records.Title` |
| `regulatory_text` | `Optional[str]` | `RAG_Records.Regulatory_Text` (`None`) | `Regulatory Records.Regulatory_Text` (`None`) |
| `requirement` | `str` | `RAG_Records.Requirement` | `Regulatory Records.Requirement` |
| `summary` | `Optional[str]` | `RAG_Records.Summary` | `Regulatory Records.Summary` |
| `topic` | `Optional[str]` | `RAG_Records.Topic` | Joined `Source Register.Topic` |
| `official_source` | `Optional[str]` | `RAG_Records.Official_Source_URL` | `Source_URL` / `Official Link/Reference` |
| `version_date` | `Optional[str]` | `RAG_Records.Version_Date` | Joined `Version/Last Updated` |
| `effective_date` | `Optional[str]` | `RAG_Records.Effective_Date` | Joined `Effective Date` / `Publication/Effective Date` |
| `validation_status` | `str` | `RAG_Records.Validation_Status` | Joined `Source Register.Status` |
| `applicability` | `Optional[str]` | `RAG_Records.Applicability` | None |
| `relevance_to_project`| `Optional[str]` | `RAG_Records.Relevance_to_Project` | None |
| `notes_limitations` | `Optional[str]` | `RAG_Records.Notes_Limitations` | None |
| `source_type` | `Optional[str]` | Joined `Source Register.Source Type` | `RAG_Records.Source_Type` |
| `authority_level` | `Optional[str]` | `RAG_Records.Authority_Level` | Joined `Source Register.Authority Level` |
| `source_notes` | `Optional[str]` | Joined `Source Register.Notes/Limitations`| None |
| `is_approved_for_rag`| `bool` | Evaluated via `is_sme_approved()` (`False`)| Computed (`False`) |
| `chunk_id` | `Optional[str]` | `RAG_Records.Chunk_ID` | None |
| `content_type` | `Optional[str]` | `RAG_Records.Content_Type` | None |
| `retrieval_text` | `Optional[str]` | `RAG_Records.Retrieval_Text` | None |
| `retrieval_tags` | `List[str]` | `RAG_Records.Retrieval_Tags` (parsed) | None |
| `citation_label` | `Optional[str]` | `RAG_Records.Citation_Label` | None |
| `retrieval_priority` | `Optional[str]` | `RAG_Records.Retrieval_Priority` | None |
| `authority_rule` | `Optional[str]` | `RAG_Records.Authority_Rule` | None |
| `rag_instruction` | `Optional[str]` | `RAG_Records.RAG_Instruction` | None |
| `official_source_check_note` | `Optional[str]` | `RAG_Records.Official_Source_Check_Note` | None |

---

## 11. Requirement vs. Regulatory_Text vs. Retrieval_Text

The conceptual and structural separation of text fields was rigorously enforced:

```
+---------------------------------------------------------------------------------------+
| Requirement (Concise Summary)                                                         |
| Length: 48 - 273 chars                                                                |
| "It is an offence to offer, promise or give a financial or other advantage..."        |
+---------------------------------------------------------------------------------------+
                                           ≠
+---------------------------------------------------------------------------------------+
| Regulatory_Text (Verbatim Statute)                                                    |
| Value: NULL / None across all 15 records                                              |
| Strictly NOT fabricated. Never copied from Requirement or Retrieval_Text.            |
+---------------------------------------------------------------------------------------+
                                           ≠
+---------------------------------------------------------------------------------------+
| Retrieval_Text (Composite Context Evidence Block)                                     |
| Length: 343 - 578 chars                                                               |
| "Source: Bribery Act 2010 | Reference: Section 1 | Topic: Offences... | Requirement:  |
| It is an offence... | Applicability: Persons... | Project relevance: Core UK..."      |
+---------------------------------------------------------------------------------------+
```

Across all 15 records:
- `retrieval_text == requirement` evaluated to **`False`** (100% distinct).
- `regulatory_text` evaluated to **`None`** (100% null).

---

## 12. Retrieval_Tags Conversion

Raw semicolon-delimited tag strings from Excel were converted into structured `List[str]`:

| Record ID | Raw Excel Value | Normalized Python List |
| :--- | :--- | :--- |
| `RR-UK-01` | `"UK;Bribery Act 2010;Offences of bribing another person;Section 1"` | `["UK", "Bribery Act 2010", "Offences of bribing another person", "Section 1"]` |
| `RR-UK-02` | `"UK;Bribery Act 2010;Guidance;Six Principles;Bribery prevention procedures"` | `["UK", "Bribery Act 2010", "Guidance", "Six Principles", "Bribery prevention procedures"]` |
| `RR-EU-01` | `"EU;Directive (EU) 2026/1021;Criminalisation;Article 3;Active and passive bribery"` | `["EU", "Directive (EU) 2026/1021", "Criminalisation", "Article 3", "Active and passive bribery"]` |

All tags have whitespace trimmed, empty entries discarded, and zero tags lost.

---

## 13. Official Source URL Mapping

The `official_source` field maps directly from `Official_Source_URL`. All 15 records point to official government or regulatory portals:

- **legislation.gov.uk:** `RR-UK-01`
- **GOV.UK:** `RR-UK-02`, `RR-UK-04`, `RR-UK-05`, `RR-UK-06`, `RR-UK-07`
- **FCA Handbook / FCA Portal:** `RR-UK-03`, `RR-UK-08`, `RR-UK-09`
- **EUR-Lex:** `RR-EU-01`, `RR-EU-03`, `RR-EU-04`, `RR-EU-05`
- **European Commission:** `RR-EU-02`, `RR-EU-06`

Zero fabricated, placeholder, or generic URLs exist.

---

## 14. Citation Metadata Preservation

Preformatted Citation Labels are preserved on every record:
- `UK-01 | Bribery Act 2010 | Section 1`
- `UK-02 | Bribery Act 2010 Guidance | Six Principles`
- `UK-03 | FCA Financial Crime Guide | FCG 6`
- `EU-01 | Directive (EU) 2026/1021 | Article 3`
- `EU-02 | Proposal COM(2023) 234 | Article 7`

Labels remain strictly linked to the authentic `Source_ID`, `Regulation`, and `Section_Article`.

---

## 15. Authority and Priority Metadata

- **Authority Levels Preserved:** Level A (7 records), Level B (4 records), Level C (2 records), Level D (2 records).
- **Retrieval Priorities Preserved:** `P1 — Core` (5 records), `P2 — Conditional` (10 records).
- **No Approval Reinterpretation:** Level A bindingness and P1 Core extraction status do *not* confer SME approval.

---

## 16. Source-Control Join

The `Source_Control` worksheet contains one row per source (15 rows total). The join logic was verified:
- Source-control metadata does NOT multiply regulatory records.
- Exactly 15 regulatory records produced from 15 source records.
- Zero duplicate Record IDs or Source IDs.

---

## 17. Approval Preservation

In compliance with Task W4.3:
- **Total Approved Records:** **`0`**
- **Total Candidate Records:** **`15`**
- **`is_approved_for_rag`:** **`False`** across all 15 records.
- Fail-closed `@model_validator(mode="after")` strictly prevents any record from being flagged as approved.

---

## 18. JSON Round-Trip Validation

After generating `data/processed/normalized_regulatory_records.json`, the file was read back from disk and deserialized through `NormalizedRegulatoryRecord`:

```python
with open("data/processed/normalized_regulatory_records.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)
reloaded = [NormalizedRegulatoryRecord(**item) for item in raw_data]
```

- **JSON Deserialization:** 15/15 succeeded without error.
- **Roundtrip Equality:** `[r.model_dump() for r in reloaded] == raw_data` (**100% identical**).
- **Silent Field Drops:** **`0`**.

---

## 19. Focused Test Results

A dedicated test suite [`tests/test_normalized_records.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/tests/test_normalized_records.py) was executed:

```
tests/test_normalized_records.py::test_1_exactly_15_normalized_records PASSED
tests/test_normalized_records.py::test_2_uk_records_count_and_distribution PASSED
tests/test_normalized_records.py::test_3_eu_records_count_and_distribution PASSED
tests/test_normalized_records.py::test_4_unique_record_ids PASSED
tests/test_normalized_records.py::test_5_unique_source_ids PASSED
tests/test_normalized_records.py::test_6_unique_chunk_ids PASSED
tests/test_normalized_records.py::test_7_source_fk_resolution PASSED
tests/test_normalized_records.py::test_8_zero_orphan_records PASSED
tests/test_normalized_records.py::test_9_zero_duplicate_records PASSED
tests/test_normalized_records.py::test_10_source_control_join_does_not_multiply_records PASSED
tests/test_normalized_records.py::test_11_retrieval_text_present_for_all_records PASSED
tests/test_normalized_records.py::test_12_requirement_remains_separate_from_retrieval_text PASSED
tests/test_normalized_records.py::test_13_regulatory_text_remains_strictly_none PASSED
tests/test_normalized_records.py::test_14_retrieval_tags_are_normalized_lists PASSED
tests/test_normalized_records.py::test_15_official_source_url_mapped_correctly PASSED
tests/test_normalized_records.py::test_16_citation_label_preserved PASSED
tests/test_normalized_records.py::test_17_retrieval_priority_preserved PASSED
tests/test_normalized_records.py::test_18_authority_rule_preserved PASSED
tests/test_normalized_records.py::test_19_rag_instruction_preserved PASSED
tests/test_normalized_records.py::test_20_official_source_check_note_preserved PASSED
tests/test_normalized_records.py::test_21_all_records_remain_candidate_status PASSED
tests/test_normalized_records.py::test_22_is_approved_for_rag_is_strictly_false PASSED
tests/test_normalized_records.py::test_23_json_roundtrip_deserialization_fidelity PASSED
tests/test_normalized_records.py::test_24_exact_serialized_field_count PASSED
tests/test_normalized_records.py::test_25_legacy_week_3_fallback_compatibility PASSED
tests/test_normalized_records.py::test_26_raw_excel_workbooks_remain_completely_unmodified PASSED

============================= 26 passed in 0.64s ==============================
```

- Ingestion Tests (`test_ingestion.py`): **25/25 passed**.
- Source-Control Tests (`test_source_control_approval.py`): **25/25 passed**.
- Normalized Records Tests (`test_normalized_records.py`): **26/26 passed**.

---

## 20. Full Regression Result

The full regression test suite was executed across all modules (Ingestion, Retrieval, Generation, Citations, GAP Handling, Conflict Detection, Structured Output, Safety Evaluation, and FastAPI Integration):

- **Baseline Tests:** 186
- **New W4.4 Tests:** 26
- **Total Tests:** **212 passed, 0 failed, 0 errors (100% pass rate).**

---

## 21. ChromaDB Integrity

- Collection: `regulatory_records`
- Vector Count Before W4.4: **15**
- Vector Count After W4.4: **15**
- Reindexed: **NO (Untouched)**

---

## 22. `regulatory_chunks.json` Integrity

Task W4.4 explicitly preserved the Week 3 chunk artifact without modification:
- Path: `data/processed/regulatory_chunks.json`
- SHA-256 Before W4.4: `b5d99e7cc5b4c98aeec209469c8848d500645008b367cf9606ba41b17fa6a7b2`
- SHA-256 After W4.4: `b5d99e7cc5b4c98aeec209469c8848d500645008b367cf9606ba41b17fa6a7b2`
- Integrity Status: **100% UNTOUCHED (Chunk regeneration strictly deferred to W4.5)**

---

## 23. Raw Workbook SHA-256 Integrity

Cryptographic checksums of all raw Excel workbooks were verified identical before and after execution:

| Workbook Filename | SHA-256 Hash | Integrity Status |
| :--- | :--- | :---: |
| `ABC shield_Data Dictionary.xlsx` | `57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6` | **100% UNTOUCHED** |
| `ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` | `2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b` | **100% UNTOUCHED** |
| `ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` | `5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00` | **100% UNTOUCHED** |
| `ABC_Shield_Source_Register (1).xlsx` | `0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b` | **100% UNTOUCHED** |
| `ABC_Shield_Source_Register_Reviewed (1).xlsx` | `fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4` | **100% UNTOUCHED** |

---

## 24. Limitations

1. **Downstream Chunking Deferred:**
   - `data/processed/regulatory_chunks.json` still reflects Week 3 serialized chunks. It will be regenerated in Task W4.5 using the normalized records generated here.
2. **ChromaDB Rebuild Deferred:**
   - ChromaDB continues to store Week 3 vectors until Task W4.6, when the vector store will be reindexed with `Retrieval_Text`.
3. **Candidate Corpus Scope:**
   - All 15 records remain Candidate. Authoritative retrieval queries (`filter_approved_only=True`) safely return 0 results.

---

## 25. Final W4.4 Status Block

```
==================================================
W4.4 STATUS: COMPLETE
==================================================

Normalized Regulatory Records Successfully Regenerated.

Records:
15

UK:
9

EU:
6

Actual Serialized Schema Fields:
31

Unique Record IDs:
15

Unique Source IDs:
15

Unique Chunk IDs:
15

Source FK Resolution:
15/15

Candidate:
15

Approved:
0

Regulatory_Text:
NULL / NOT FABRICATED

Retrieval_Text:
15/15 PRESENT

Retrieval_Tags:
15/15 NORMALIZED

Citation Metadata:
PRESERVED

Authority/Priority Metadata:
PRESERVED

Source-Control:
PRESERVED

Normalized JSON:
REGENERATED AND ROUND-TRIP VERIFIED

Focused Tests:
26/26 PASSED

Ingestion Tests:
25/25 PASSED

Source-Control Tests:
25/25 PASSED

Full Regression:
212/212 PASSED

ChromaDB:
15 vectors, UNTOUCHED

regulatory_chunks.json:
UNTOUCHED

Raw Excel:
UNTOUCHED

Output:
data/processed/normalized_regulatory_records.json

Report:
data/evaluation/W4_4_normalized_records_validation_report.md

READY FOR PADMA REVIEW BEFORE W4.5.

STOP.
DO NOT START W4.5.
==================================================
```
