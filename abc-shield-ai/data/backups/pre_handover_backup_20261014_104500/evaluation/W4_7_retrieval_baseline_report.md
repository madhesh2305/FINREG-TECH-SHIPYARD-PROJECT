# Week 4.7 Retrieval Baseline Report: Empirical Evaluation & Validation

**Role:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Project:** ABC Shield / FinRegTech ShipYard AI/RAG  
**Task:** TASK W4.7 — Update & Validate Retrieval Baseline  
**Date:** September 30, 2026  
**Status:** COMPLETE & FULLY VERIFIED (278/278 Full Regression Tests Passing)

---

## 1. Executive Summary & Objective

The objective of Task W4.7 is to empirically evaluate and establish the retrieval baseline of the newly rebuilt Week 4 ChromaDB vector store (`regulatory_records`, 15 vectors, `all-MiniLM-L6-v2`, 384 dimensions) using the controlled 34 benchmark cases in `data/evaluation/evaluation_cases.json`.

In strict adherence to governance boundaries:
- **Zero retrieval algorithm redesigns** were performed (no BM25, no hybrid search, no Reciprocal Rank Fusion, no rerankers, no query expansion, and no threshold tuning).
- **Zero modifications** were made to the canonical JSON artifacts, raw Excel files, or ChromaDB vector collections.
- The evaluation was executed strictly against the **live ChromaDB index**, with all 15 records in `Candidate - Awaiting Approval` status (`is_approved_for_rag = False`).

The measured Week 4 baseline demonstrates substantial improvements over the historical Week 3 baseline across all primary retrieval metrics, driven by the enriched statutory `retrieval_text` introduced in Week 4:
- **Precision@1:** Increased from **0.3810** (Week 3) to **0.9048** (Week 4) (+137.5% relative).
- **Recall@5:** Increased from **0.6429** (Week 3) to **1.0000** (Week 4) (100% recall of expected evidence).
- **Hit Rate@3:** Increased from **0.6667** (Week 3) to **1.0000** (Week 4) (100% hit rate within top 3).
- **Hit Rate@5:** Increased from **0.7143** (Week 3) to **1.0000** (Week 4).
- **Mean Reciprocal Rank (MRR):** Increased from **0.5016** (Week 3) to **0.9524** (Week 4) (+89.9% relative).
- **UK Bribery Act Section 1:** Elevated from **Rank 4** (Week 3) to **Rank 1** (Week 4) with cosine similarity **0.8192** (for specific phrasing) and **0.7171** (for statutory query).

---

## 2. Evaluation Scope & Methodology

Evaluation was conducted using the existing `rag/evaluation/` architecture (`EvaluationDatasetValidator`, `RetrievalEvaluator`, `RegulatoryRetriever`) without modifying production logic:
- Retrieval was performed across standard operational depths: **K = 1, K = 3, and K = 5**.
- In strict adherence to evaluation standards, **Applicable Retrieval Cases** (cases with expected relevant evidence) were evaluated for Precision, Recall, Hit Rate, and MRR.
- **Non-Applicable Cases** (out-of-scope, unapproved evidence, adversarial injection, and missing provision tests where expected records are empty) were segregated to prevent division-by-zero distortion and evaluate governance safety.
- Record-level deduplication was enforced: multiple chunks retrieved from the same parent regulatory record count as a single record.

---

## 3. Active ChromaDB Configuration & Embedding Model

- **Vector Store:** ChromaDB `PersistentClient` at `data/processed/chroma_db/`
- **Collection Name:** `regulatory_records`
- **Collection Distance Metric:** Cosine (`hnsw:space = "cosine"`)
- **Total Vectors Indexed:** Exactly 15
- **Jurisdiction Breakdown:** 9 UK (`RR-UK-01-C01` through `RR-UK-09-C01`) + 6 EU (`RR-EU-01-C01` through `RR-EU-06-C01`)
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimension:** 384 dimensions (runtime verified)
- **Inference Mode:** 100% Local CPU inference (zero remote API dependencies)
- **Text Indexed:** Canonical Week 4 `retrieval_text` (UTF-8 encoding verified)
- **Validation Status:** All 15 vectors retain `Candidate - Awaiting Approval` (`is_approved_for_rag = False`)

---

## 4. Benchmark Source & Case Stratification

- **Benchmark File:** `data/evaluation/evaluation_cases.json`
- **Total Benchmark Cases:** 34 (`CASE-01` through `CASE-34`)
- **Applicable Retrieval Cases (Evaluated Denominator):** 21 cases (`CASE-01`, `03`, `04`, `05`, `06`, `07`, `08`, `09`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `29`)
- **Non-Applicable / Safety / GAP Cases (Zero-Expected):** 13 cases (`CASE-02`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `30`, `31`, `32`, `33`, `34`)

### Category Distribution of Applicable Cases:
- **Category A (UK Anti-Bribery Statutory):** `CASE-01` (1 case)
- **Category B (MoJ Bribery Guidance):** `CASE-03`, `CASE-04` (2 cases)
- **Category C (FCA Financial Crime Guidance):** `CASE-05`, `CASE-06`, `CASE-07` (3 cases)
- **Category D (EU Anti-Corruption Legislation):** `CASE-08`, `CASE-09`, `CASE-10` (3 cases)
- **Category E (Exact Statutory & Article Inquiries):** `CASE-11`, `CASE-12`, `CASE-13` (3 cases)
- **Category F (Broad Thematic Compliance):** `CASE-14`, `CASE-15` (2 cases)
- **Category G (Cross-Instrument Alignment):** `CASE-16`, `CASE-17` (2 cases)
- **Category H (Documented Overlaps & Practice Notes):** `CASE-18`, `CASE-19`, `CASE-20` (3 cases)
- **Category I (Direct Legal Amendments):** `CASE-21` (1 case)
- **Category M (Text Fidelity Inquiries):** `CASE-29` (1 case)

---

## 5. Metric Definitions & Formulas

Metrics are computed across the 21 applicable cases ($N = 21$) with record-level deduplication:

1. **Precision@K:**  
   $$\text{Precision@K} = \frac{|\text{Relevant Unique Records in Top } K|}{K}$$  
   *Note:* In regulatory RAG where queries often seek a single specific governing provision ($|\text{Expected}| = 1$), retrieving 1 relevant record at $K=3$ produces a theoretical maximum Precision@3 of $0.3333$, and at $K=5$ a theoretical maximum of $0.2000$.

2. **Recall@K:**  
   $$\text{Recall@K} = \frac{|\text{Relevant Unique Records in Top } K|}{|\text{Expected Unique Records}|}$$

3. **Hit Rate@K:**  
   $$\text{Hit Rate@K} = \begin{cases} 1.0 & \text{if } |\text{Relevant Unique Records in Top } K| \ge 1 \\ 0.0 & \text{otherwise} \end{cases}$$

4. **Mean Reciprocal Rank (MRR):**  
   $$\text{MRR} = \frac{1}{N} \sum_{i=1}^{N} \frac{1}{\text{Rank of First Relevant Chunk in Case } i}$$

---

## 6. Quantitative Retrieval Metrics Table (Week 4 Measured Baseline)

Evaluated across the 21 applicable cases against the active ChromaDB collection:

| Retrieval Depth ($K$) | Precision@K | Recall@K | Hit Rate@K | Mean Reciprocal Rank (MRR) |
| :---: | :---: | :---: | :---: | :---: |
| **K = 1** | **0.9048** (19 / 21) | **0.7381** | **0.9048** (19 / 21) | **0.9524** |
| **K = 3** | **0.4444** | **0.9762** | **1.0000** (21 / 21) | — |
| **K = 5** | **0.2762** | **1.0000** (21 / 21) | **1.0000** (21 / 21) | — |

*Detailed Metric Values:*
- **Precision@1:** `0.9048`
- **Precision@3:** `0.4444`
- **Precision@5:** `0.2762`
- **Recall@1:** `0.7381`
- **Recall@3:** `0.9762`
- **Recall@5:** `1.0000`
- **HitRate@1:** `0.9048`
- **HitRate@3:** `1.0000`
- **HitRate@5:** `1.0000`
- **MRR:** `0.9524`

---

## 7. Week 3 vs Week 4 Comparative Analysis

A comparison between the documented historical Week 3 baseline (recorded in `data/evaluation/results/evaluation_summary.md` on 2026-09-24) and the measured Week 4 baseline (2026-09-30) shows the quantitative impact of the Week 4 enriched regulatory text:

| Metric | Week 3 Baseline | Week 4 Baseline | Absolute Delta | Relative Change |
| :--- | :---: | :---: | :---: | :---: |
| **Precision@1** | 0.3810 | **0.9048** | **+0.5238** | **+137.5%** |
| **Precision@3** | 0.2857 | **0.4444** | **+0.1587** | **+55.5%** |
| **Precision@5** | 0.1810 | **0.2762** | **+0.0952** | **+52.6%** |
| **Recall@1** | 0.2619 | **0.7381** | **+0.4762** | **+181.8%** |
| **Recall@3** | 0.5952 | **0.9762** | **+0.3810** | **+64.0%** |
| **Recall@5** | 0.6429 | **1.0000** | **+0.3571** | **+55.5%** |
| **Hit Rate@1** | 0.3810 | **0.9048** | **+0.5238** | **+137.5%** |
| **Hit Rate@3** | 0.6667 | **1.0000** | **+0.3333** | **+50.0%** |
| **Hit Rate@5** | 0.7143 | **1.0000** | **+0.2857** | **+40.0%** |
| **MRR** | 0.5016 | **0.9524** | **+0.4508** | **+89.9%** |
| **Section 1 Rank** | #4 | **#1** | **+3 ranks** | **Elevated to Top** |
| **Section 1 Similarity** | 0.5028 | **0.8192 / 0.7171** | **+0.2143 to +0.3164** | **Substantial Gain** |

---

## 8. Exact Provision Retrieval Deep-Dive

Statutory queries demand high lexical and semantic precision. In Week 3, dense bi-encoder embeddings frequently favored broader contextual documents over specific statutory sections. In Week 4, the statutory text enrichment resolved this limitation:

### A. UK Bribery Act 2010 Section 1 (Prompt-Specified Inquiry)
- **Query 1 (Natural Language):** *"What does the Bribery Act 2010 say about bribing another person?"*
  - **Expected Chunk:** `RR-UK-01-C01` (`RR-UK-01`)
  - **Actual Measured Rank:** **Rank 1**
  - **Measured Cosine Similarity:** **0.8192** (Cosine distance: `0.1808`)
  - **Top-5 Retrieved Context:**
    1. `RR-UK-01-C01` (Bribery Act 2010, Section 1) — Sim: `0.8192` (Jurisdiction: UK, Authority: A)
    2. `RR-UK-02-C01` (MoJ Guidance, Six Principles) — Sim: `0.5769` (Jurisdiction: UK, Authority: B)
    3. `RR-UK-05-C01` (Trade Guidance, Risk reduction) — Sim: `0.5335` (Jurisdiction: UK, Authority: B)
    4. `RR-EU-01-C01` (Directive (EU) 2026/1021, Article 3) — Sim: `0.5234` (Jurisdiction: EU, Authority: A)
    5. `RR-UK-04-C01` (Anti-bribery policy overview) — Sim: `0.5208` (Jurisdiction: UK, Authority: B)

- **Query 2 (Statutory Citation):** *"What constitutes an offence under Section 1 of the Bribery Act 2010?"*
  - **Expected Chunk:** `RR-UK-01-C01` (`RR-UK-01`)
  - **Actual Measured Rank:** **Rank 1**
  - **Measured Cosine Similarity:** **0.7171** (Cosine distance: `0.2829`)
  - **Retrieved at K=1:** `True`
  - **Retrieved at K=3:** `True`
  - **Retrieved at K=5:** `True`
  - **Week 3 Rank:** #4 (Similarity: `0.5028`)

### B. EU Corruption Directive (Article 3)
- **Query (`CASE-12`):** *"Explain Article 3 of Directive (EU) 2026/1021."*
  - **Expected Record:** `RR-EU-01`
  - **Actual Rank:** **Rank 1** (P@1 = 1.0, R@1 = 1.0)

### C. Whistleblower Protection Directive (Article 19)
- **Query (`CASE-13`):** *"What are the reporting channels required by Article 19 of Directive (EU) 2019/1937?"*
  - **Expected Record:** `RR-EU-03`
  - **Actual Rank:** **Rank 1** (P@1 = 1.0, R@1 = 1.0)

---

## 9. Governance & Filtering Verification

### A. Approval-Only Filter Evaluation (`filter_approved_only = True`)
- **Query:** *"What does the Bribery Act 2010 say about bribing another person?"*
- **Parameter:** `filter_approved_only = True`
- **Retrieved Count:** **0**
- **Safety Compliance:** Passed. Because all 15 records in the corpus have `validation_status = "Candidate - Awaiting Approval"` and `is_approved_for_rag = False`, the approval gate functions fail-closed. No candidate data leaks into approved-only queries.

### B. Jurisdiction Filter Evaluation
Retrieval was tested across both UK and EU jurisdiction boundaries using thematic compliance query `"bribery and corruption controls"`:
- **UK Jurisdiction Filter (`jurisdiction = "UK"`):**
  - **Retrieved Chunks:** `RR-UK-07-C01`, `RR-UK-08-C01`, `RR-UK-03-C01`, `RR-UK-05-C01`, `RR-UK-01-C01`
  - **Count:** 5
  - **Jurisdiction Consistency:** 100% (5/5 chunks have `jurisdiction = "UK"`)
  - **Cross-Jurisdiction Contamination:** **0.0%**
- **EU Jurisdiction Filter (`jurisdiction = "EU"`):**
  - **Retrieved Chunks:** `RR-EU-01-C01`, `RR-EU-06-C01`, `RR-EU-04-C01`, `RR-EU-02-C01`, `RR-EU-05-C01`
  - **Count:** 5
  - **Jurisdiction Consistency:** 100% (5/5 chunks have `jurisdiction = "EU"`)
  - **Cross-Jurisdiction Contamination:** **0.0%**

---

## 10. Failure Analysis & Controlled Taxonomy

Out of 21 applicable benchmark cases, exactly **19 cases achieved Rank 1 retrieval** (Hit Rate@1 = 90.48%). Only **2 cases** had their first relevant hit at Rank 2:

| Case ID | Query | Expected Record(s) | Retrieved Top 5 Records | First Hit Rank | Failure Taxonomy Classification | Root Cause & Analysis |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| **`CASE-07`** | *"What information is provided on the FCA bribery and corruption overview page?"* | `RR-UK-08` (FCA overview webpage) | 1. `RR-UK-03`<br>2. `RR-UK-08`<br>3. `RR-UK-02`<br>4. `RR-UK-05`<br>5. `RR-UK-07` | **Rank 2** (MRR = 0.5) | `GENERIC_CONTEXT_OVER_EXACT_PROVISION` | Both `RR-UK-03` (FCG 6 guidance) and `RR-UK-08` (overview page) are FCA instruments. FCG 6 possesses rich thematic text on bribery systems and controls which dense similarity ranked slightly ahead of the high-level web overview. At K=3, `RR-UK-08` is retrieved (Hit Rate@3 = 1.0). |
| **`CASE-14`** | *"What anti-bribery and corruption controls should a financial institution maintain?"* | `RR-UK-03`, `RR-UK-02` (Dual targets) | 1. `RR-UK-08`<br>2. `RR-UK-03`<br>3. `RR-UK-07`<br>4. `RR-UK-02`<br>5. `RR-UK-05` | **Rank 2** (MRR = 0.5) | `LOW_RANK` / `NEEDS_HUMAN_REVIEW` | Broad multi-instrument thematic question matching multiple guidance documents. First target (`RR-UK-03`) retrieved at Rank 2; second target (`RR-UK-02`) retrieved at Rank 4. By K=5, both targets are retrieved (Recall@5 = 1.0). This case is explicitly flagged in benchmark metadata with `requires_human_review: true`. |

### Corpus Coverage Limitations vs Retrieval Failures:
The remaining 13 benchmark cases (zero-expected) were examined to confirm whether missing evidence represents a retrieval failure or corpus boundary:
- **`CASE-02` (Bribery Act Section 7 corporate offence):** Section 7 is not an independent record in the current 15-record corpus. Properly handled as `MISSING_SPECIFIC_PROVISION` (Corpus Coverage Limitation, not a retrieval defect).
- **`CASE-22` (DORA operational resilience):** ICT third-party risk management is outside the core anti-bribery scope. Properly handled as `OUT_OF_SCOPE`.
- **`CASE-23`, `24`, `25` (Tax evasion, GDPR, AML):** Non-bribery statutory regimes absent by design. Properly handled as `OUT_OF_SCOPE`.
- **`CASE-26`, `27` (US Foreign Corrupt Practices Act):** US extraterritorial statutes absent from UK/EU corpus. Properly handled as `INSUFFICIENT_RETRIEVED_EVIDENCE`.
- **`CASE-30` (Bribery Act Section 11 penalties):** Specific statutory penalty figures absent from current chunks. Properly handled as `MISSING_SPECIFIC_PROVISION`.
- **`CASE-32`, `33`, `34` (Adversarial injections):** Jailbreaks and privilege escalations correctly rejected.

---

## 11. Top-K Representative Query Inspection

| Case ID / Query | Rank | Chunk ID | Similarity | Regulation | Section / Article | Jurisdiction | Authority Level |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **`CASE-01`**<br>*"What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?"* | **1**<br>2<br>3<br>4<br>5 | `RR-UK-01-C01`<br>`RR-EU-01-C01`<br>`RR-UK-02-C01`<br>`RR-UK-05-C01`<br>`RR-UK-08-C01` | **0.7818**<br>0.5284<br>0.5208<br>0.5186<br>0.5147 | Bribery Act 2010<br>Directive (EU) 2026/1021<br>MoJ Bribery Guidance<br>Trade Risk Guidance<br>FCA Overview Page | Section 1<br>Article 3<br>Six Principles<br>Risk-reduction<br>Overview | UK<br>EU<br>UK<br>UK<br>UK | A<br>A<br>B<br>B<br>B |
| **`CASE-03`**<br>*"What are the Six Principles in the Ministry of Justice Bribery Act 2010 guidance?"* | **1**<br>2<br>3<br>4<br>5 | `RR-UK-02-C01`<br>`RR-UK-03-C01`<br>`RR-UK-01-C01`<br>`RR-UK-08-C01`<br>`RR-UK-07-C01` | **0.7812**<br>0.5517<br>0.5369<br>0.5230<br>0.5185 | MoJ Bribery Guidance<br>FCA FCG 6<br>Bribery Act 2010<br>FCA Overview<br>Practice Note | Six Principles<br>FCG 6<br>Section 1<br>Overview<br>Counter Bribery | UK<br>UK<br>UK<br>UK<br>UK | B<br>B<br>A<br>B<br>B |
| **`CASE-08`**<br>*"What are the public sector bribery offences under Article 3 of Directive (EU) 2026/1021?"* | **1**<br>2<br>3<br>4<br>5 | `RR-EU-01-C01`<br>`RR-UK-01-C01`<br>`RR-EU-02-C01`<br>`RR-UK-02-C01`<br>`RR-UK-04-C01` | **0.8037**<br>0.5427<br>0.5401<br>0.5059<br>0.4998 | Directive (EU) 2026/1021<br>Bribery Act 2010<br>EU Legislation Overview<br>MoJ Guidance<br>Policy Overview | Article 3<br>Section 1<br>Index<br>Six Principles<br>Policy | EU<br>UK<br>EU<br>UK<br>UK | A<br>A<br>A<br>B<br>B |
| **`CASE-13`**<br>*"What are the reporting channels required by Article 19 of Directive (EU) 2019/1937?"* | **1**<br>2<br>3<br>4<br>5 | `RR-EU-03-C01`<br>`RR-EU-05-C01`<br>`RR-EU-01-C01`<br>`RR-EU-02-C01`<br>`RR-EU-06-C01` | **0.7712**<br>0.4857<br>0.4789<br>0.4632<br>0.4491 | Whistleblower Directive<br>Regulation 883/2013<br>Directive (EU) 2026/1021<br>EU Legislation Overview<br>EU Anti-Corruption Strategy | Article 19<br>Article 8<br>Article 3<br>Index<br>Strategic Objectives | EU<br>EU<br>EU<br>EU<br>EU | A<br>A<br>A<br>A<br>C |

---

## 12. Recommendations for Future Retrieval Enhancements

While Week 4 retrieval demonstrates strong performance (MRR 0.9524, Recall@5 1.0000), future development phases may evaluate:
1. **Hybrid Retrieval (BM25 + Dense Semantic):** Adding lexical BM25 indexing fused with Reciprocal Rank Fusion (RRF) to elevate exact section number matches (such as Section 7 or Section 11) where statutory vocabulary is sparse.
2. **Metadata-Aware Query Routing:** Automatically detecting explicit statutory citations in user queries (e.g. `Section \d+`, `Article \d+`) to pre-filter or weight chunks matching those exact fields.
3. **Cross-Encoder Re-Ranking:** Evaluating a secondary cross-encoder scoring stage on top-10 dense candidates to fine-tune subtle semantic distinctions between overview pages and comprehensive guidance.

---

## 13. Test Results & Immutability Audit

### Automated Test Suites Executed:
1. **Targeted Baseline Suite (`tests/test_retrieval_baseline.py`):** **18 passed in 18.19s** (100% pass)
2. **Existing Retrieval Suite (`tests/test_retrieval.py`):** **15 passed in 16.24s** (100% pass)
3. **Existing Evaluation Suite (`tests/test_evaluation.py`):** **29 passed in 135.86s** (100% pass)
4. **Full Repository Regression Suite (`pytest -q`):** **278 passed in 221.81s (0:03:41)** (100% pass, 0 failures, 0 errors)

### Data & Index Immutability Verification:
| File / Resource | Initial Baseline Hash / Count | Post-Evaluation Hash / Count | Audit Status |
| :--- | :--- | :--- | :---: |
| `data/processed/normalized_regulatory_records.json` | `5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d` | `5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d` | **PASS** |
| `data/processed/regulatory_chunks.json` | `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef` | `05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef` | **PASS** |
| `data/raw/ABC shield_Data Dictionary.xlsx` | `57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6` | `57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6` | **PASS** |
| `data/raw/ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx` | `2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b` | `2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b` | **PASS** |
| `data/raw/ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx` | `5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00` | `5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00` | **PASS** |
| `data/raw/ABC_Shield_Source_Register (1).xlsx` | `0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b` | `0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b` | **PASS** |
| `data/raw/ABC_Shield_Source_Register_Reviewed (1).xlsx` | `fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4` | `fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4` | **PASS** |
| ChromaDB `regulatory_records` Vector Count | Exactly 15 vectors | Exactly 15 vectors | **PASS** |
| Production Source Files (`rag/`, `api/`) | Unmodified | 0 production files modified | **PASS** |

---

## 14. Final W4.7 Status Block

```
==================================================
W4.7 STATUS: COMPLETE
==================================================

Benchmark Cases:
34

Applicable Retrieval Cases:
21

Non-Applicable Cases:
13

Precision@1:
0.9048

Precision@3:
0.4444

Precision@5:
0.2762

Recall@1:
0.7381

Recall@3:
0.9762

Recall@5:
1.0000

HitRate@1:
0.9048

HitRate@3:
1.0000

HitRate@5:
1.0000

MRR:
0.9524

Section 1:
Rank 1 (Cosine similarity: 0.8192 for prompt phrasing; 0.7171 for statutory citation)

Approval Filter:
filter_approved_only = True returns 0 results (Fail-closed gating verified)

UK Filter:
5 / 5 chunks UK (100% precision, 0% contamination)

EU Filter:
5 / 5 chunks EU (100% precision, 0% contamination)

Failed Retrieval Cases:
0 total misses; 2 cases with first hit at Rank 2 (CASE-07, CASE-14)

Main Failure Categories:
GENERIC_CONTEXT_OVER_EXACT_PROVISION (CASE-07); LOW_RANK / NEEDS_HUMAN_REVIEW (CASE-14)

Week 3 vs Week 4:
Precision@1: 0.3810 -> 0.9048 (+137.5%)
Recall@5: 0.6429 -> 1.0000 (+55.5%)
HitRate@3: 0.6667 -> 1.0000 (+50.0%)
HitRate@5: 0.7143 -> 1.0000 (+40.0%)
MRR: 0.5016 -> 0.9524 (+89.9%)
Section 1: Rank #4 -> Rank #1

Baseline Recommendations:
1. Future hybrid search (BM25 + dense vector) via RRF
2. Statutory citation regex pre-routing (Section/Article number weighting)
3. Cross-encoder reranking stage for top candidates

Focused Tests:
tests/test_retrieval_baseline.py: 18 / 18 PASSED
tests/test_retrieval.py: 15 / 15 PASSED
tests/test_evaluation.py: 29 / 29 PASSED

Full Regression:
278 / 278 PASSED (0 failures, 0 errors, 221.81s)

ChromaDB:
15 vectors, UNMODIFIED

Canonical Artifacts:
UNMODIFIED (All hashes match baseline)

Report:
data/evaluation/W4_7_retrieval_baseline_report.md
==================================================
```
