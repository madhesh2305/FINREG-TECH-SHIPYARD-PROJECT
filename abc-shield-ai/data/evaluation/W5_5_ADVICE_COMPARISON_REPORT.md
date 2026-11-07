# WEEK 5 — TASK W5.5: ADVICE COMPARISON REPORT

---

## 1. Document Control

| Attribute | Specification |
| :--- | :--- |
| **Task Reference** | **WEEK 5 — TASK W5.5: Advice Comparison** |
| **Document Version** | **1.0.0** |
| **Date** | **October 7, 2026** |
| **Role / Lead Author** | **Padma Kumar** — AI/RAG & Conflict Detection Engineer |
| **Project** | **ABC Shield / FinRegTech ShipYard AI/RAG** |
| **Collaborators** | **Vishal** (Backend Lead), **Harshini** (Frontend Lead), **Sanjay** (API Gateway / Infrastructure Lead) |
| **Verified Baseline** | **564 / 564 Tests Passing (100.0% Pass Rate)** |
| **Corpus Invariant** | **15 Canonical Regulatory Records (15 Candidate / 0 Approved), ChromaDB = 15 Vectors** |
| **Status** | **COMPLETE** |

---

## 2. Objective & Mission

Task W5.5 implements and validates the AI/RAG-side **Advice Comparison** capability within the FinRegTech ShipYard / ABC Shield platform.

### Core Comparison Workflow:
```
Advisor 1 Advice Record
        ↓
Advisor 2 Advice Record
        ↓
AdviceComparator (Difference & Contradiction Detection)
        ↓
Regulatory Evidence Retrieval (ChromaDB Vector Store)
        ↓
Supporting Evidence Breakdown (Corroboration per Advisor)
        ↓
Citations + Provenance Assembly
        ↓
Documented Relationship Detection (CO-001..CO-011 via ConflictDetector)
        ↓
Evidence Gap & Limitation Analysis (Missing Provisions / Unapproved Gating)
        ↓
Human Review Gate (human_review_required = True)
        ↓
Strict Non-Adjudication: decision = None (Final disposition by Human Owner)
```

### Critical Non-Adjudication Invariants:
1. **The AI/RAG system MUST NOT decide which advisor is correct**: It never outputs `"correct_advisor"`, never declares a legal interpretation controlling, and never resolves disputes automatically.
2. **Strictly Descriptive Analysis**: The system detects differences, contradictions, scope variations, authority differences, and version shifts without taking sides.
3. **Evidence-Grounded**: It retrieves supporting chunks, provides deterministic citations and audit provenance, and identifies evidence gaps honestly.

---

## 3. Existing Components Inspected & Reused

Before implementation, all relevant repository components were inspected:
1. **[`AdviceRAGAdapter`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_adapter.py)** (W5.4): Reused single-query pipeline and traceability patterns.
2. **[`ConflictDetector`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/conflict/conflict_detector.py)** (W4.10): Reused the controlled Conflict Overlap dataset and canonical taxonomy (`CONFLICT`, `OVERLAP`, `SCOPE_DIFFERENCE`, `AUTHORITY_DIFFERENCE`, `VERSION_DIFFERENCE`).
3. **[`GapHandler`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/generation/gap_handler.py)** (W4.9): Reused safe evidence-gap classification (`MISSING_SPECIFIC_PROVISION`, `UNAPPROVED_EVIDENCE`, `OUT_OF_SCOPE`) with safe wording invariants.
4. **[`RegulatoryRetriever`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/retrieval/retriever.py)** & **[`ChromaVectorStore`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/retrieval/vector_store.py)**: Reused shared vector store singletons with zero duplicate retrieval code and zero external data sources.
5. **[`CitationBuilder`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/generation/citations.py)**: Reused deterministic citation format `[chunk_id | record_id | regulation | section]` and provenance models.

---

## 4. Comparison Architecture & Data Flow

```
                      ┌────────────────────────────────────────┐
                      │    Advisor 1 Text   │   Advisor 2 Text │
                      └───────────────┬─────┴─────┬────────────┘
                                      │           │
                                      ▼           ▼
                      ┌────────────────────────────────────────┐
                      │            AdviceComparator            │
                      │  • detect_advice_differences()         │
                      │  • Normalization & Polarity Check      │
                      │  • Scope & Authority Analysis          │
                      └───────────────────┬────────────────────┘
                                          │
                               Combined Query
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │          RegulatoryRetriever           │
                      │    (ChromaDB Dense Vector Search)      │
                      └─────────┬───────────────────┬──────────┘
                                │                   │
                     Retrieved Chunks          Metadata Filter
                                │                   │
                                ▼                   ▼
                      ┌───────────────────┐ ┌───────────────────┐
                      │  CitationBuilder  │ │ ConflictDetector  │
                      │(Citations & Prov) │ │  (CO-001..CO-011) │
                      └─────────┬─────────┘ └─────────┬─────────┘
                                │                     │
                                └──────────┬──────────┘
                                           │
                                           ▼
                      ┌────────────────────────────────────────┐
                      │       AdviceSupportingEvidence         │
                      │  • Evidence breakdown for Advisor 1    │
                      │  • Evidence breakdown for Advisor 2    │
                      └────────────────────┬───────────────────┘
                                           │
                                           ▼
                      ┌────────────────────────────────────────┐
                      │        AdviceComparisonResult          │
                      │  • differences: List[AdviceDifference] │
                      │  • relationships: List[ConflictFinding]│
                      │  • supporting_evidence: List[...]      │
                      │  • citations & provenance              │
                      │  • evidence_gaps: List[GapResult]      │
                      │  • human_review_required: True         │
                      │  • decision: None (STRICTLY UNSET)     │
                      │  • disclaimer: Non-adjudication notice │
                      └────────────────────────────────────────┘
```

---

## 5. Input Model (`AdviceComparisonRequest`)

```json
{
  "comparison_id": "CMP-2026-001",
  "project_id": "PRJ-ABC-001",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "advisor_1": {
    "advice_id": "ADV-001",
    "advice_text": "Commercial organisations must establish proportionate anti-bribery procedures under the Bribery Act 2010.",
    "advisor_name": "Counsel Alpha",
    "source_reference": "Bribery Act 2010, Guidance"
  },
  "advisor_2": {
    "advice_id": "ADV-002",
    "advice_text": "Anti-bribery prevention procedures are optional and voluntary for commercial organisations under the Bribery Act 2010.",
    "advisor_name": "Consultant Beta",
    "source_reference": "Informal Opinion"
  },
  "context": {
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption"
  }
}
```

---

## 6. Difference Detection Logic & Taxonomy

The comparator categorizes differences across six distinct tiers without collapsing all differences into "conflicts":

| Classification | Meaning | Contradiction Flag (`is_contradiction`) |
| :--- | :--- | :---: |
| **`NO_DIFFERENCE`** | Texts are normalized identical or substantively equivalent. | `False` |
| **`SUBSTANTIVE_DIFFERENCE`** | Advisors propose differing procedures, interpretations, or standards. | `False` |
| **`SCOPE_DIFFERENCE`** | Advisors address differing jurisdictions (UK vs EU) or differing frameworks (statutory criminal offences vs corporate compliance procedures). | `False` |
| **`AUTHORITY_DIFFERENCE`** | Advisors rely on differing regulatory tiers (primary Parliamentary Act vs Ministry of Justice executive guidance). | `False` |
| **`VERSION_DIFFERENCE`** | Advisors reference differing amendment versions or temporal dates (e.g. 2010 Act vs 2025 revised guidance). | `False` |
| **`POTENTIAL_CONTRADICTION`** | Advisors assert mutually incompatible legal mandates (e.g. mandatory vs optional, prohibited vs permitted, strict liability vs intent required). | **`True`** |

---

## 7. Supporting Evidence & Grounded Citations

For each advisor position, the comparator evaluates factual alignment against retrieved ChromaDB chunks:
- **`SUPPORTED`**: Multiple retrieved regulatory chunks corroborate the advisor's stated premise.
- **`PARTIALLY_SUPPORTED`**: At least one retrieved chunk provides partial relevant context.
- **`INSUFFICIENT_EVIDENCE`**: The retrieved evidence does not directly support the asserted position.
- **Traceable Linage**: Full `Citation` and `ProvenanceRecord` objects are returned linking exact `chunk_id`, `record_id`, `regulation`, `section_article`, and canonical `official_source` URLs.

---

## 8. Evidence Gap Handling & Safe Phrasing

When an advice assertion references a provision outside the 15-record canonical corpus (e.g. corporate failure to prevent bribery under Section 7, or DORA / NIS2):
- The system emits a structured [`GapResult`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/generation/gap_handler.py#L37).
- **Safe Phrasing Invariant**:
  > *"Section 7 is not represented in the current ABC Shield regulatory evidence corpus. This reflects corpus coverage limitations rather than proof that the advisor is incorrect."*
- The system **never** claims the statute lacks the provision, and **never** claims the advisor is wrong due to absence of evidence.

---

## 9. Output Model (`AdviceComparisonResult`)

```json
{
  "comparison_id": "CMP-2026-001",
  "advisor_1": {
    "advice_id": "ADV-001",
    "advice_text": "Commercial organisations must establish proportionate anti-bribery procedures under the Bribery Act 2010.",
    "advisor_name": "Counsel Alpha"
  },
  "advisor_2": {
    "advice_id": "ADV-002",
    "advice_text": "Anti-bribery prevention procedures are optional and voluntary for commercial organisations under the Bribery Act 2010.",
    "advisor_name": "Consultant Beta"
  },
  "differences": [
    {
      "difference_type": "POTENTIAL_CONTRADICTION",
      "summary": "Potential substantive contradiction detected regarding legal obligations, culpability standards, or operational mandates.",
      "advisor_1_position": "Commercial organisations must establish proportionate anti-bribery procedures under the Bribery Act 2010.",
      "advisor_2_position": "Anti-bribery prevention procedures are optional and voluntary for commercial organisations under the Bribery Act 2010.",
      "is_contradiction": true
    }
  ],
  "relationships": [
    {
      "conflict_id": "CO-001",
      "topic": "Anti-Bribery / Preventive Procedures",
      "source_id_1": "UK-01",
      "source_1": "Bribery Act 2010",
      "source_id_2": "UK-02",
      "source_2": "Bribery Act 2010 Guidance",
      "relationship": "Overlap - complementary",
      "conflict_type": "OVERLAP",
      "both_sources_retrieved": true,
      "requires_human_review": true,
      "message": "Retrieved evidence contains a documented regulatory overlap between UK-01 (Bribery Act 2010) and UK-02 (Bribery Act 2010 Guidance). The Conflict Overlap register identifies the relationship as: 'Overlap - complementary'. Documented differences in scope, authority, and version are reported as registered. No legal conflict resolution is made by this system."
    }
  ],
  "supporting_evidence": [
    {
      "advice_id": "ADV-001",
      "advice_text": "Commercial organisations must establish proportionate anti-bribery procedures under the Bribery Act 2010.",
      "supporting_chunk_ids": ["RR-UK-02-C01", "RR-UK-01-C01"],
      "supporting_source_ids": ["UK-02", "UK-01"],
      "evidence_status": "SUPPORTED",
      "notes": "Retrieved regulatory evidence (RR-UK-02-C01, RR-UK-01-C01) provides factual context relevant to this advice."
    },
    {
      "advice_id": "ADV-002",
      "advice_text": "Anti-bribery prevention procedures are optional and voluntary for commercial organisations under the Bribery Act 2010.",
      "supporting_chunk_ids": ["RR-UK-02-C01", "RR-UK-01-C01"],
      "supporting_source_ids": ["UK-02", "UK-01"],
      "evidence_status": "SUPPORTED",
      "notes": "Retrieved regulatory evidence (RR-UK-02-C01, RR-UK-01-C01) provides factual context relevant to this advice."
    }
  ],
  "citations": [
    {
      "citation_id": "CIT-RR-UK-01-C01",
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "is_approved_for_rag": false,
      "validation_status": "Candidate - Awaiting Approval"
    },
    {
      "citation_id": "CIT-RR-UK-02-C01",
      "chunk_id": "RR-UK-02-C01",
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "regulation": "Bribery Act 2010 Guidance",
      "section_article": "Six Principles",
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
    },
    {
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "regulation": "Bribery Act 2010 Guidance",
      "section_article": "Six Principles",
      "jurisdiction": "UK",
      "official_source": "https://www.justice.gov.uk/downloads/legislation/bribery-act-2010-guidance.pdf",
      "is_approved_for_rag": false
    }
  ],
  "evidence_gaps": [],
  "human_review_required": true,
  "decision": null,
  "disclaimer": "This comparison provides source-grounded regulatory analysis and factual difference identification. It does not constitute formal legal or professional advice. It does NOT determine which advisor is legally or professionally correct. Final legal determinations and compliance disposition remain the exclusive responsibility of a qualified compliance professional.",
  "traceability": {
    "comparison_id": "CMP-2026-001",
    "project_id": "PRJ-ABC-001",
    "requirement_ids": ["REQ-001", "REQ-002"],
    "advisor_1_id": "ADV-001",
    "advisor_2_id": "ADV-002",
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption",
    "timestamp": "2026-10-07T14:05:00.000000+00:00"
  }
}
```

---

## 10. Human Review Boundary & Non-Adjudication Invariants

1. **`decision: null` Strictly Enforced**: The field is initialized to `None` and cannot be set by the RAG layer.
2. **No Advisor Selection**: No `correct_advisor`, `winning_advisor`, or `ruling` field exists in the output schema.
3. **`human_review_required = True` Gate**: Automatically flagged whenever:
   - Contradictions exist (`is_contradiction = True`).
   - Substantive differences exist (`difference_type != "NO_DIFFERENCE"`).
   - Documented relationships exist (`len(relationships) > 0`).
   - Evidence gaps exist (`len(evidence_gaps) > 0`).
   - Candidate records are present (`is_candidate = True`).

---

## 11. Security & Isolation Controls

- **Validation Defense (`extra="forbid"`):** Request models [`AdvisorAdviceItem`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_comparator.py#L30) and [`AdviceComparisonRequest`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_comparator.py#L40) reject unauthorized top-level or nested client fields with HTTP 422.
- **Tenant Isolation:** Passing an unassigned or foreign `project_id` returns 0 chunks and fails closed cleanly.
- **Approval Gating:** Candidate records retain `is_approved_for_rag=False`. In `filter_approved_only=True` mode, retrieval returns 0 records and emits an `UNAPPROVED_EVIDENCE` gap.
- **Error Masking:** Unhandled exceptions return generic HTTP 500 responses without exposing filesystem paths or database connection details.

---

## 12. Verification & Test Results

### 12.1 Dedicated W5.5 Test Suite (`tests/test_rag_advice_comparison_w55.py`)

| # | Test Name | Verification Focus | Result |
| :-: | :--- | :--- | :---: |
| 1 | `test_w55_identical_advice_texts_yields_no_difference` | Identical advice texts produce `NO_DIFFERENCE` and `is_contradiction=False` | **PASS** |
| 2 | `test_w55_materially_different_advice_texts_detected` | Differing recommendations detected as `SUBSTANTIVE_DIFFERENCE` | **PASS** |
| 3 | `test_w55_potential_contradiction_flags_human_review` | Incompatible mandates flag `POTENTIAL_CONTRADICTION` and `human_review_required=True` | **PASS** |
| 4 | `test_w55_scope_difference_not_automatically_contradiction` | Offence vs procedure classified as `SCOPE_DIFFERENCE` without false contradiction | **PASS** |
| 5 | `test_w55_authority_or_version_difference_identified` | Statute vs guidance classified as `AUTHORITY_DIFFERENCE` | **PASS** |
| 6 | `test_w55_supporting_evidence_attaches_citations_and_provenance` | Citations, provenance, and supporting evidence breakdown attached | **PASS** |
| 7 | `test_w55_evidence_gap_identified_without_claiming_advice_is_wrong` | Missing provisions (Section 7) emit `GapResult` with non-prejudicial disclosure | **PASS** |
| 8 | `test_w55_no_approved_source_behavior_remains_safe` | Approved-only mode on candidate corpus fails closed safely | **PASS** |
| 9 | `test_w55_candidate_source_remains_fail_closed` | Candidate records tagged `is_approved_for_rag=False`; mandates human review | **PASS** |
| 10 | `test_w55_advisor_ids_preserved_for_traceability` | Advisor IDs, comparison ID, project ID, and requirement IDs preserved | **PASS** |
| 11 | `test_w55_project_isolation_remains_enforced` | Foreign/unassigned project ID fails closed (0 chunks returned) | **PASS** |
| 12 | `test_w55_no_final_legal_professional_decision_generated` | `decision=None` strictly preserved; non-adjudication disclaimer verified | **PASS** |
| 13 | `test_w55_existing_w410_conflict_detector_remains_compatible` | Co-retrieving documented sources surfaces `CO-001` relationship finding | **PASS** |
| 14 | `test_w55_existing_w54_advice_adapter_remains_compatible` | `AdviceRAGAdapter` continues to function with 100% compatibility | **PASS** |
| 15 | `test_w55_http_compare_endpoint` | `POST /api/v1/compare` returns HTTP 200 with complete `AdviceComparisonResult` | **PASS** |
| 16 | `test_w55_http_compare_extra_forbid_enforced` | Extra unauthorized client fields rejected with HTTP 422 | **PASS** |

**Pass Rate:** **16 / 16 Passed (100.0%)** in 7.88s.

---

## 13. Full Regression Test Verification

Ran complete regression suite:
```powershell
python -m pytest -q
```
- **Passed:** **564**
- **Failed:** **0**
- **Errors:** **0**
- **Execution Time:** 34.65s
- **Baseline Growth:** 548 (post-W5.4) $\to$ **564** (+16 tests).

---

## 14. Governance & Ownership Boundaries

### PADMA IMPLEMENTED (AI/RAG Lead):
- Designed and implemented [`AdviceComparator`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/pipeline/advice_comparator.py).
- Implemented difference detection, contradiction detection, scope/authority/version classification, supporting evidence breakdown, and evidence gap evaluation.
- Exposed `POST /api/v1/compare` endpoint in [`api/routes/compare.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/compare.py) with dependency injection.
- Preserved `decision: None` and mandatory non-adjudication disclaimers.
- Authored and verified 16 dedicated integration tests (564/564 full regression).

### VISHAL REMAINING DEPENDENCIES (FastAPI Backend Lead):
- Retrieve Advisor 1 and Advisor 2 advice records from PostgreSQL/SQLModel database.
- Authenticate callers and authorize workspace access for `project_id`.
- Persist `AdviceComparisonResult` and audit logs.
- Provide human review workflow queue where compliance officers make the final disposition.
- Store the eventual human SME decision in the backend database.

### HARSHINI REMAINING DEPENDENCIES (Frontend Lead):
- Build side-by-side comparison UI displaying Advisor 1 vs Advisor 2.
- Render difference badges (`SUBSTANTIVE_DIFFERENCE`, `SCOPE_DIFFERENCE`, `POTENTIAL_CONTRADICTION`).
- Render supporting evidence cards with interactive citation pills and provenance drawers.
- Render Candidate development warning banners and SME review action buttons.
- Display the mandatory non-adjudication disclaimer prominently.

---

## 15. Sign-off

Task W5.5 is **COMPLETE**. The Advice Comparison capability is operational, source-grounded, non-adjudicative, and fully verified across all regression suites.
