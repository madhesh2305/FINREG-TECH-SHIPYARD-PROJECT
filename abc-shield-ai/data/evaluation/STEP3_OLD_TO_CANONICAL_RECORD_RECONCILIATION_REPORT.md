# ABC SHIELD — STEP 3: OLD-TO-CANONICAL RECORD RECONCILIATION REPORT

**Project Root:** `D:\FInregTech Shipyard\abc-shield-ai`  
**Engineer:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Date:** 2026-10-14  
**Task:** Step 3 — Old-to-Canonical Record Reconciliation (Inspection & Reporting Only)  
**Status:** **STEP 3 COMPLETE**  

---

## 1. Executive Summary

In preparation for activating the new canonical regulatory corpus in ABC Shield, a comprehensive, evidence-based reconciliation was conducted between the active 15-record baseline (`data/processed/normalized_regulatory_records.json`) and Madhesh's canonical 25-record corpus (`data/raw/ABC_Shield_Canonical_25_Record_Corpus.xlsx`).

**Key Conclusions:**
1. **Structural Evolution (Breadth-First $\to$ Depth-First):**
   - The **active 15-record dataset** was a breadth-first survey allocating exactly 1 high-level umbrella record to each of 15 candidate sources (`RR-UK-01` through `RR-UK-09` and `RR-EU-01` through `RR-EU-06`).
   - The **canonical 25-record corpus** reflects Mohan Sir and Madhesh's curated compliance focus, concentrating exclusively on **5 core operational sources** (`UK-01`, `UK-02`, `UK-03`, `UK-09`, `EU-01`) partitioned into granular statutory sections, principles, and regulatory chapters.
2. **Reconciliation Categorization (25 Canonical Records):**
   - **Direct 1:1 Substantive Matches:** **3 records** (`UK-01-R001`, `EU-01-R002`, `UK-09-R001`).
   - **Granular Partitions of Active Umbrella Records:** **11 records** (`UK-02-R001`..`R006` partitioning MoJ Six Principles; `UK-03-R001`..`R005` partitioning FCA FCG 6).
   - **Genuinely New Regulatory Provisions:** **11 records** (`UK-01-R002`..`R006` adding Bribery Act Sections 2, 6, 7, 8, 9; `EU-01-R001`, `EU-01-R003`..`R007` adding Directive Articles 1, 4, 13, 16, 20, 21).
   - **Duplicates / Collisions:** **0 records** (All 25 represent distinct legal articles/principles).
   - **Unresolved / Ambiguous Records:** **0 records** (All 25 have verified provenance and official URLs).
3. **Active Baseline Retirement (10 Records):**
   - 10 active records belonging to deferred or supporting sources (`RR-UK-04`..`RR-UK-08`, `RR-EU-02`..`RR-EU-06`) have no counterpart in the 25-record corpus. In the canonical register, these sources are designated as either Supporting Context (3 sources) or Deferred (7 sources) with `Corpus_Record_Count = 0`.
4. **Conflict Dataset Integrity (`CO-001` through `CO-011`):**
   - The conflict detection engine operates on `source_id`.
   - **Active Conflict Pairs:** Relationships `CO-001` (`UK-01` vs `UK-02`), `CO-002` (`UK-01` vs `UK-03`), and `CO-003` (`UK-03` vs `UK-09`) remain 100% active and supported across 18 granular records in the 25-record corpus.
   - **Deferred Conflict Pairs:** Relationships `CO-004` through `CO-011` involve deferred or supporting sources with 0 chunks in the 25-record corpus. Under the Week 4.10 "both-source" rule, they will be cleanly suppressed at runtime without generating errors.
5. **Zero Mutation Safeguard:** Active JSON datasets, chunks, ChromaDB vectors, and raw workbooks were not modified.

---

## 2. Dataset Overview & Inventory

### A. Inspected Assets
1. **Active Normalized Records:** [`data/processed/normalized_regulatory_records.json`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/processed/normalized_regulatory_records.json) — 15 records.
2. **Active Regulatory Chunks:** [`data/processed/regulatory_chunks.json`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/processed/regulatory_chunks.json) — 15 chunks (`RR-UK-01-C01`..`RR-EU-06-C01`).
3. **Canonical 25-Record Corpus:** [`data/raw/ABC_Shield_Canonical_25_Record_Corpus.xlsx`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/raw/ABC_Shield_Canonical_25_Record_Corpus.xlsx) — 25 records across 18 columns.
4. **Canonical Source Register:** [`data/raw/ABC_Shield_Canonical_Source_Register.xlsx`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/raw/ABC_Shield_Canonical_Source_Register.xlsx) — 15 sources across 18 columns.
5. **Conflict Overlap Dataset:** [`data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx) (sheet `Conflict_Handling`) — 11 rows (`CO-001`..`CO-011`).

### B. Record Count Reconciliation
$$\begin{array}{|l|c|c|l|}
\hline
\textbf{Corpus Layer} & \textbf{Active Baseline} & \textbf{Canonical Handover} & \textbf{Structural Shift} \\
\hline
\text{Total Regulatory Records} & 15 & 25 & +10\text{ records (depth expansion)} \\
\text{Total Sources Extracted} & 15 & 5 & -10\text{ sources (deferred/supporting)} \\
\text{UK Records} & 9 & 18 & +9\text{ records (Sections 1--9, Principles 1--6, FCG 6)} \\
\text{EU Records} & 6 & 7 & +1\text{ record (Granular Articles of Dir 2026/1021)} \\
\text{Approved for RAG} & 0 & 0 & 100\%\text{ Candidate Gating Preserved} \\
\hline
\end{array}$$

---

## 3. Record-by-Record Reconciliation Mapping Table

Every record in the canonical 25-record corpus was evaluated against the active 15 records based on Source ID, Section/Article, Topic, Official URL, and verbatim legislative text:

| Canonical ID | Source ID | Section / Article | Topic / Provision | Relationship to Active Baseline | Active Record Reference | Reconciliation Evidence & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UK-01-R001** | UK-01 | Section 1 | Bribing another person | **Matched Existing Record** | `RR-UK-01` | Direct 1:1 substantive match on Bribery Act 2010 Section 1 offences. |
| **UK-01-R002** | UK-01 | Section 2 | Being bribed | **Genuinely New Record** | None | Adds statutory offence of being bribed (passive bribery). |
| **UK-01-R003** | UK-01 | Section 6 | Bribery of foreign public officials | **Genuinely New Record** | None | Adds statutory offence of bribing a foreign public official (FPO). |
| **UK-01-R004** | UK-01 | Section 7 | Failure of commercial organisations | **Genuinely New Record** | None | Adds corporate criminal failure-to-prevent offence (critical for ABC Shield). |
| **UK-01-R005** | UK-01 | Section 8 | Meaning of associated person | **Genuinely New Record** | None | Defines "associated person" performing services for the organisation. |
| **UK-01-R006** | UK-01 | Section 9 | Guidance on preventing bribery | **Genuinely New Record** | None | Statutory duty of Secretary of State to publish guidance. |
| **UK-02-R001** | UK-02 | Principle 1 | Proportionate procedures | **Granular Partition** | `RR-UK-02` | `RR-UK-02` was an umbrella summary; `UK-02-R001` provides dedicated Principle 1 rules. |
| **UK-02-R002** | UK-02 | Principle 2 | Top-level commitment | **Granular Partition** | `RR-UK-02` | Dedicated coverage of governance and board/executive tone from the top. |
| **UK-02-R003** | UK-02 | Principle 3 | Risk assessment | **Granular Partition** | `RR-UK-02` | Dedicated coverage of periodic, documented bribery risk assessment. |
| **UK-02-R004** | UK-02 | Principle 4 | Due diligence | **Granular Partition** | `RR-UK-02` | Dedicated coverage of supply-chain and associated-person due diligence. |
| **UK-02-R005** | UK-02 | Principle 5 | Communication & training | **Granular Partition** | `RR-UK-02` | Dedicated coverage of internal/external communication and training. |
| **UK-02-R006** | UK-02 | Principle 6 | Monitoring and review | **Granular Partition** | `RR-UK-02` | Dedicated coverage of monitoring, evaluation, and improvement. |
| **UK-03-R001** | UK-03 | FCG 6.1.1 | Scope | **Granular Partition** | `RR-UK-03` | `RR-UK-03` was an umbrella summary; `UK-03-R001` provides exact FCA scope rules. |
| **UK-03-R002** | UK-03 | FCG 6.2.1 | Governance | **Granular Partition** | `RR-UK-03` | Dedicated coverage of senior management responsibilities under FCA guidance. |
| **UK-03-R003** | UK-03 | FCG 6.2.2 | Risk assessment | **Granular Partition** | `RR-UK-03` | Dedicated coverage of firm-level bribery/corruption risk assessments. |
| **UK-03-R004** | UK-03 | FCG 6.2.3 | Policies and procedures | **Granular Partition** | `RR-UK-03` | Dedicated coverage of gifts, hospitality, political donations, expenses. |
| **UK-03-R005** | UK-03 | FCG 6.2.4 | Dealing with third parties | **Granular Partition** | `RR-UK-03` | Dedicated coverage of third-party risk management and intermediary vetting. |
| **UK-09-R001** | UK-09 | PRIN 2.1.1R - Principle 1 | Integrity | **Matched Existing Record** | `RR-UK-09` | Direct 1:1 substantive match on FCA Principle for Businesses 1 (Integrity). |
| **EU-01-R001** | EU-01 | Article 1 | Subject matter and scope | **Genuinely New Record** | None | Defines Directive (EU) 2026/1021 minimum rules on corruption offences. |
| **EU-01-R002** | EU-01 | Article 3 | Public-sector bribery | **Matched Existing Record** | `RR-EU-01` | Direct 1:1 substantive match on intentional active/passive public-sector bribery. |
| **EU-01-R003** | EU-01 | Article 4 | Private-sector bribery | **Genuinely New Record** | None | Adds private-sector commercial bribery offences. |
| **EU-01-R004** | EU-01 | Article 20 | Prevention of corruption | **Genuinely New Record** | None | Adds preventive and awareness measures required across Member States. |
| **EU-01-R005** | EU-01 | Article 21 | National strategies | **Genuinely New Record** | None | Adds Member State duty to adopt and publish national anti-corruption strategies. |
| **EU-01-R006** | EU-01 | Article 13 | Liability of legal persons | **Genuinely New Record** | None | Adds EU-level corporate legal person criminal/non-criminal liability framework. |
| **EU-01-R007** | EU-01 | Article 16 | Mitigating circumstances | **Genuinely New Record** | None | Adds compliance programme mitigation provisions under EU law. |

---

## 4. Status of the Active 15 Records

The transition plan for the 15 active records currently in `normalized_regulatory_records.json`:

1. **Directly Matched & Retained (3 records):**
   - `RR-UK-01` $\to$ Replaced by `UK-01-R001` (enriched with verbatim excerpt).
   - `RR-EU-01` $\to$ Replaced by `EU-01-R002` (enriched with verbatim excerpt).
   - `RR-UK-09` $\to$ Replaced by `UK-09-R001` (enriched with verbatim excerpt).
2. **Superseded by Granular Partitions (2 records):**
   - `RR-UK-02` (Six Principles overview) $\to$ Superseded by 6 principle-level records (`UK-02-R001` through `UK-02-R006`).
   - `RR-UK-03` (FCG 6 overview) $\to$ Superseded by 5 section-level records (`UK-03-R001` through `UK-03-R005`).
3. **Retired from Active Retrieval Corpus (10 records):**
   - The following 10 sources are not extracted into the canonical 25-record corpus, as approved by Mohan Sir and recorded in the canonical source register:
     - `RR-EU-02` (Source `EU-02`: Commission Explanatory Page — Supporting Context)
     - `RR-UK-04` (Source `UK-04`: Government Anti-Bribery Policy — Supporting Context)
     - `RR-UK-08` (Source `UK-08`: FCA Web Summary — Supporting Context)
     - `RR-UK-05` (Source `UK-05`: Trade Risk Guidance — Deferred)
     - `RR-UK-06` (Source `UK-06`: Professional Standard — Deferred)
     - `RR-UK-07` (Source `UK-07`: Practice Note — Deferred)
     - `RR-EU-03` (Source `EU-03`: Whistleblower Directive — Deferred)
     - `RR-EU-04` (Source `EU-04`: OLAF Regulation — Deferred)
     - `RR-EU-05` (Source `EU-05`: OLAF Amendment — Deferred)
     - `RR-EU-06` (Source `EU-06`: Anti-Corruption Strategy — Deferred / Monitor)

---

## 5. Conflict & Relationship Reference Integrity (`CO-001`..`CO-011`)

The conflict detection engine ([`rag/conflict/conflict_detector.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/conflict/conflict_detector.py)) matches documented relationships by evaluating `chunk.source_id` against `Source_ID_1` and `Source_ID_2`:

$$\begin{array}{|l|l|l|c|l|}
\hline
\textbf{Conflict ID} & \textbf{Source 1} & \textbf{Source 2} & \textbf{Both in 25-Corpus?} & \textbf{Runtime Behavior} \\
\hline
\textbf{CO-001} & \text{UK-01 (Bribery Act)} & \text{UK-02 (Guidance)} & \textbf{YES} & \text{Active: Surfaces overlap when both retrieved} \\
\textbf{CO-002} & \text{UK-01 (Bribery Act)} & \text{UK-03 (FCA FCG 6)} & \textbf{YES} & \text{Active: Surfaces overlap when both retrieved} \\
\textbf{CO-003} & \text{UK-03 (FCA FCG 6)} & \text{UK-09 (Principle 1)} & \textbf{YES} & \text{Active: Surfaces overlap when both retrieved} \\
\text{CO-004} & \text{UK-01} & \text{UK-05 (Deferred)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-005} & \text{UK-06 (Deferred)} & \text{UK-07 (Deferred)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-006} & \text{UK-03} & \text{UK-08 (Supporting)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-007} & \text{EU-01} & \text{EU-02 (Supporting)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-008} & \text{EU-01} & \text{EU-06 (Deferred)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-009} & \text{EU-03 (Deferred)} & \text{EU-01} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-010} & \text{EU-04 (Deferred)} & \text{EU-05 (Deferred)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\text{CO-011} & \text{EU-01} & \text{EU-04 (Deferred)} & \text{NO} & \text{Cleanly suppressed (Both-Source Rule)} \\
\hline
\end{array}$$

**Integrity Finding:**
- `CO-001`, `CO-002`, and `CO-003` are backed by 18 active records in the 25-record corpus.
- No conflict relationships require rewritten IDs or definitions.
- Suppressed relationships remain in the workbook audit trail without causing runtime errors or false alarms.

---

## 6. Migration Impact & Risk Assessment

| Risk Area | Severity | Impact Description | Recommended Mitigation Action |
| :--- | :--- | :--- | :--- |
| **ID Format Shift** | Medium | Old IDs (`RR-UK-01`, `RR-UK-01-C01`) change to canonical format (`UK-01-R001`, `UK-01-R001-C01`). | Provide alias lookup or update downstream consumers that hardcoded legacy IDs. |
| **Legacy Test Assumptions** | Medium | Early Week 4 unit tests (`test_ingestion.py`, `test_normalized_records.py`) hardcoded `len(raw_records) == 15`. | When activating the 25-record corpus in Step 4, update test assertions to expect 25 records while testing legacy files via explicit parameters. |
| **Retired Sources in Cache** | Low | Historical queries looking for Trade guidance (`UK-05`) or Whistleblowing (`EU-03`) will return No-Source / Evidence Gap. | Desired behavior: RAG evidence-gap guardrail cleanly fires when unsupported topics are queried. |
| **ChromaDB Re-indexing** | High | Generating 25 embeddings requires reindexing the Chroma collection. | Execute in a controlled, isolated migration step with backup of the 15-vector database. |

---

## 7. Regulatory Governance & Approval-Gate Compliance

- **Status Across All 25 Records:**
  - `Status`: `'Approved for Extraction'` (extraction readiness sign-off by regulatory research).
  - `Validation_Status`: Strictly `'Pending SME Validation'` across all 25 records.
  - **`is_approved_for_rag`:** Strictly `False` (0 approved records).
- **Compliance Policy:** Neither the normalizer nor the migration script promotes any record to approved status. Candidate-inclusive retrieval mode (`filter_approved_only=False`) remains the sole path for pre-production evaluation.

---

## 8. Final Status

**STATUS: STEP 3 COMPLETE**

Reconciliation between the active 15-record dataset and the canonical 25-record corpus is fully substantiated by programmatic inspection, exact legal cross-referencing, and conflict-matrix verification.

Execution has stopped. No active normalized files or vector stores have been altered.
