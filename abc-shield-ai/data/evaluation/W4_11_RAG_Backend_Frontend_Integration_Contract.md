# W4.11 RAG → Backend / Frontend Integration Contract

---

## 1. Document Control

| Attribute | Specification |
| :--- | :--- |
| **Task Reference** | **TASK W4.11 — Phase 2: Integration Contract Documentation** |
| **Document Version** | **1.0.0-DRAFT** |
| **Status** | **DRAFT — Awaiting Team Confirmation (Vishal / Harshini)** |
| **Owner / Lead Author** | **Padma Kumar** — AI/RAG & Conflict Detection Engineer |
| **Target Reviewers** | **Vishal** (Backend Lead), **Harshini** (Frontend Lead) |
| **Date** | **October 1, 2026** |
| **Project** | **ABC Shield / FinRegTech ShipYard AI/RAG** |
| **Scope** | Formal technical specification defining the bidirectional data contract, schema mappings, processing lifecycle, status models, and governance boundaries between the Client/Frontend, FastAPI Backend, and AI/RAG Engine. |

---

## 2. Purpose

This document constitutes the formal, binding **RAG Integration Contract** for the ABC Shield regulatory intelligence platform. It establishes an explicit, machine-readable technical agreement between:
1. **The Frontend Layer (Harshini):** User interface requiring predictable state flags, source evidence citations, conflict/relationship banners, gap explanations, and prominent human-review notices.
2. **The FastAPI Backend Layer (Vishal):** API routing, request validation, persistence, schema transformation, and service orchestration layer requiring strongly typed JSON payloads without free-form LLM string parsing.
3. **The AI/RAG Core Layer (Padma):** Retrieval-Augmented Generation engine encompassing dense vector search (ChromaDB), deterministic citation assembly, fail-closed approval gating, evidence-gap analysis, documented relationship detection, and non-adjudicative response assembly.

This contract directly satisfies **Compulsory Deliverable E of the Week 4 Blueprint** by formalizing:
- **Input:** What the RAG layer receives from the backend/frontend.
- **Processing:** How the RAG layer executes retrieval, filtering, grounding, and detection.
- **Output:** What structured fields, metadata, and audit records the RAG layer returns.
- **Integration:** How the backend and frontend consume, display, and audit these structures.

---

## 3. Integration Architecture

The ABC Shield end-to-end integration topology follows a unidirectional data flow with strict boundary isolation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. Frontend Layer (Harshini)                    │
│  - User Prompt Input                                                   │
│  - Regulatory Requirement / Advisor Advice Context Binding             │
│  - Render Grounded Answer, Citations, Conflicts, Gaps, Review Banners  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP POST /api/v1/query (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        2. FastAPI Backend Layer (Vishal)               │
│  - Request Schema Validation (Pydantic / QueryRequest)                 │
│  - Correlation ID Generation (request_id = "REQ-<uuid>")               │
│  - Context Extraction (project_id, requirement_ids, context)           │
│  - Service Orchestration & Logging                                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Python In-Process Dependency Injection
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        3. AI / RAG Engine (Padma)                      │
│                                                                        │
│  [A. Embeddings & Dense Retrieval]                                     │
│      Sentence Transformers (all-MiniLM-L6-v2) → ChromaDB (15 vectors)  │
│      Approval Filtering (filter_approved_only=True/False)              │
│                                                                        │
│  [B. Grounded Generation & Citation Assembly]                          │
│      Context Construction → Provider-Independent LLM (or Mock)        │
│      Deterministic Citation Whitelisting & Provenance Lineage          │
│                                                                        │
│  [C. Evidence Gap & Boundary Engine] (W4.9)                            │
│      Corpus Coverage vs Retrieval Limitation vs Out-of-Scope Detection │
│                                                                        │
│  [D. Conflict & Overlap Detector] (W4.10)                              │
│      11 Documented Controlled Pairs (CO-001..CO-011)                   │
│      Both-Source Requirement & Strict Non-Adjudication Integrity       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Unified Pydantic StructuredAIResponse
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        4. FastAPI Backend Layer (Vishal)               │
│  - Response Schema Conformity Verification                             │
│  - External Status Mapping (SUCCESS, GAP_DETECTED, CONFLICT_DETECTED)  │
│  - Audit Logging & Session Persistence                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP 200 OK (Application/JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        5. Frontend Layer (Harshini)                    │
│  - Display Status Badges & Candidate Warning Banners                   │
│  - Render Grounded Regulatory Answer                                   │
│  - Render Traceable Citation Badges & Provenance Audit Drawer          │
│  - Render Documented Overlap / Amendment Cards                         │
│  - Render Missing Provision / Scope Limitation Guidance                │
│  - Trigger Compliance Officer SME Review Workflows                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Request Contract (Input Specification)

The request payload is submitted by the client/frontend to the FastAPI endpoint `POST /api/v1/query`.

### A. Formal JSON Schema
```json
{
  "project_id": "PRJ-ABC-001",
  "query": "What systems and controls does FCA FCG 6 recommend for bribery and corruption?",
  "requirement_ids": ["REQ-001", "REQ-002"],
  "advisor_advice_ids": ["ADV-UK-001"],
  "context": {
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption"
  }
}
```

### B. Field Specifications & Constraints

| Field Name | Type | Presence | Description & Constraints |
| :--- | :--- | :--- | :--- |
| `query` | `string` | **Required** | Natural language regulatory or compliance question. Must be non-empty, non-whitespace-only. Min length: 1 char, Max length: 2000 chars (configured in `settings.query_max_length`). |
| `project_id` | `string` | **Optional** | Client-side project or workspace identifier (e.g. `"PRJ-ABC-001"`). Useful for audit trails and session logging. |
| `requirement_ids` | `array[string]` | **Optional** | Upstream business or system requirement identifiers related to the query (e.g. `["REQ-001"]`). When supplied, backend links retrieval results to these requirements. |
| `advisor_advice_ids` | `array[string]` | **Optional** | Legal/compliance advisor advisory note IDs when the query evaluates specific external advice against the regulatory corpus. |
| `context` | `object` | **Optional** | Filtering metadata context dictionary. |
| `context.jurisdiction` | `string` | **Optional** | Scope filter restricting vector retrieval: `"UK"` or `"EU"`. If omitted, retrieval spans both jurisdictions. |
| `context.regulatory_area` | `string` | **Optional** | Topic filter hint (e.g. `"Anti-Bribery and Corruption"`). |

---

## 5. Processing Contract (Lifecycle Specification)

When a request enters the RAG pipeline, the system executes 8 deterministic stages:

1. **Request Sanitization & Trace ID Generation:**
   - FastAPI assigns a globally unique correlation identifier: `request_id = "REQ-<uuid4>"`.
   - The query is stripped and validated against prompt-injection controls.
2. **Dense Vector Retrieval (Task 4 / W4.6 / W4.7):**
   - The query is embedded locally on CPU via `sentence-transformers/all-MiniLM-L6-v2` into a 384-dimensional dense vector.
   - ChromaDB collection `regulatory_records` is queried using cosine similarity (`top_k=5`, default).
   - If `context.jurisdiction` is provided, vector retrieval applies a metadata filter (`{"jurisdiction": context.jurisdiction}`).
3. **Approval Gating (W4.3 / W4.8 / W4.9):**
   - If `filter_approved_only=True` is requested, the system retrieves only records with `is_approved_for_rag=True`. Because all 15 canonical records are currently `Candidate - Awaiting Approval`, approved-only retrieval returns 0 chunks and completely bypasses the LLM (`call_count == 0`), directly outputting `UNAPPROVED_EVIDENCE`.
   - In standard development mode (`filter_approved_only=False`), candidate chunks are retrieved and accompanied by the mandatory candidate warning banner.
4. **Context Construction & Grounded LLM Generation (W4.8):**
   - Retrieved chunks are assembled into a structured `[REGULATORY EVIDENCE]` context block with exact chunk IDs, record IDs, titles, and text.
   - Provider-independent LLM (`BaseLLMProvider`) is invoked under `SYSTEM_GROUNDING_PROMPT`, strictly forbidding extrapolation, legal adjudication, and outside knowledge.
5. **Deterministic Citation & Provenance Lineage (W4.8):**
   - If the response is grounded, `CitationBuilder` generates citations strictly for chunks actually present in the retrieved evidence set.
   - Zero citations are fabricated. If evidence is insufficient, citations and provenance are suppressed to empty lists (`[]`).
6. **Deterministic Conflict & Overlap Detection (W4.10):**
   - `ConflictDetector` examines unique source IDs in the retrieved chunks against the 11 registered pairs (`CO-001` through `CO-011`).
   - Applies the **Both-Source Requirement**: a relationship is surfaced if and only if BOTH sources are present. Single-source presence suppresses the finding.
   - Preserves canonical taxonomy: distinguishes `OVERLAP` (10 pairs) and `VERSION_DIFFERENCE` (`CO-010`) from substantive `CONFLICT` (0 pairs).
   - Enforces strict non-adjudication: zero override claims, zero compliance declarations.
7. **Deterministic Evidence Gap Analysis (W4.9):**
   - If evidence is missing, out-of-scope, or insufficient, `GapHandler` analyzes the gap deterministically outside the LLM.
   - Distinguishes `RETRIEVAL_LIMITATION` (provision exists in corpus but omitted from top-$k$) from `CORPUS_COVERAGE_LIMITATION` (provision absent from ABC Shield corpus).
   - Uses precise phrasing: *"The requested provision is not represented in the current ABC Shield regulatory evidence corpus."*
8. **Structured Response Assembly (W4.9 / W4.10):**
   - `StructuredResponseBuilder` synthesizes `GroundedResponse`, retrieved chunks, citations, conflicts, and gap into the unified `StructuredAIResponse` schema.

---

## 6. Response Contract (Output Specification)

The RAG engine returns the unified `StructuredAIResponse` schema.

### A. Top-Level Schema Definition

| Field Name | Type | Mandatory? | Description |
| :--- | :--- | :---: | :--- |
| `request_id` | `string` | **Yes** | Server-generated unique request correlation identifier (e.g. `"REQ-d6e4b2a1-..."`). |
| `query` | `string` | **Yes** | Echo of original user query string. |
| `status` | `string (Enum)` | **Yes** | Lifecycle outcome status: `GROUNDED`, `INSUFFICIENT_EVIDENCE`, `OUT_OF_SCOPE`, `UNAPPROVED_EVIDENCE`, `CONFLICTING_EVIDENCE`, `NEEDS_HUMAN_REVIEW`, or `ERROR`. |
| `answer` | `string \| null` | Conditional | Grounded answer text synthesized from retrieved evidence. Present on successful answers; contains safe abstention guidance on gaps. |
| `grounded` | `boolean` | **Yes** | `true` if the answer is fully supported by retrieved evidence; `false` on evidence gaps, unapproved queries, or out-of-scope requests. |
| `gap` | `object \| null` | Conditional | Structured `GapResult` object when an evidence gap exists; `null` when `grounded=true`. |
| `citations` | `array[Citation]` | **Yes** | List of deterministic citation references tied to specific retrieved chunks. Empty list `[]` on gaps. |
| `provenance` | `array[ProvenanceRecord]` | **Yes** | Complete audit trail for each cited chunk (official source, dates, regulator, authority level). Empty `[]` on gaps. |
| `conflicts` | `array[ConflictFinding]` | **Yes** | List of documented regulatory overlaps, version differences, or conflicts surfaced among retrieved chunks. Empty `[]` when no registered pair is co-retrieved. |
| `retrieved_evidence` | `array[RetrievedEvidenceItem]` | **Yes** | List of raw evidence chunks returned by vector retrieval. Empty `[]` on zero-retrieval / approved-only gating. |
| `metadata` | `object (ResponseMetadata)` | **Yes** | Operational counts, schema version, and review/candidate flags. |

---

## 7. Status Contract & External API Mapping

To satisfy Vishal's backend and Harshini's frontend requirements while preserving the internal safety granularity established in W4.8, W4.9, and W4.10, the platform defines an explicit mapping between **Internal RAG Status** and **External Integration Status**:

### A. Status Matrix

| Internal RAG Status (`ResponseStatus`) | Proposed External API Status | Answer Present? | Citations Present? | Gap Object? | Conflicts Present? | Requires Human Review? | Trigger Condition |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `GROUNDED` (no conflicts) | **`SUCCESS`** | Yes | Yes | `null` | No (`[]`) | `false` | Sufficient evidence retrieved; answer fully supported. |
| `GROUNDED` (with conflicts) | **`CONFLICT_DETECTED`** | Yes | Yes | `null` | Yes (`len > 0`) | **`true`** | Sufficient evidence retrieved, but documented overlap or amendment difference detected between sources. |
| `CONFLICTING_EVIDENCE` | **`CONFLICT_DETECTED`** | Safe Notice | No (`[]`) | Yes | Yes (`len > 0`) | **`true`** | Ungrounded query due to contradictory or conflicting regulatory evidence. |
| `INSUFFICIENT_EVIDENCE` | **`GAP_DETECTED`** | Safe Notice | No (`[]`) | Yes | Optional | **`true`** | Chunks retrieved but lack specific facts required to answer query. |
| `OUT_OF_SCOPE` | **`GAP_DETECTED`** | Scope Notice | No (`[]`) | Yes | No (`[]`) | `false` | Query falls outside UK/EU anti-bribery & AML scope (e.g. DORA, GDPR, NIS2). |
| `UNAPPROVED_EVIDENCE` | **`NO_SOURCE_FOUND`** | Policy Notice | No (`[]`) | Yes | No (`[]`) | **`true`** | `filter_approved_only=True` requested on candidate corpus; fail-closed zero retrieval. |
| `NO_RETRIEVED_EVIDENCE` | **`NO_SOURCE_FOUND`** | Safe Notice | No (`[]`) | Yes | No (`[]`) | `false` | Zero chunks retrieved from vector store for query. |
| `ERROR` | **`ERROR`** | `null` | No (`[]`) | `null` | No (`[]`) | **`true`** | Unhandled pipeline exception, vector database connection failure, or internal crash. |

> [!IMPORTANT]
> `NO_SOURCE_FOUND` is strictly distinguished from technical `ERROR`:
> - `NO_SOURCE_FOUND` represents a legitimate business outcome where the regulatory vector search returned zero matching records or approved records. HTTP status is `200 OK`.
> - `ERROR` represents an unexpected system or infrastructure failure. HTTP status is `500 Internal Server Error`.

---

## 8. Citation Contract

Citations are generated 100% deterministically by `CitationBuilder` from retrieved evidence chunks.

### A. Schema (`Citation`)
```json
{
  "chunk_id": "RR-UK-01-C01",
  "record_id": "RR-UK-01",
  "source_id": "UK-01",
  "citation_key": "CIT-RR-UK-01-C01",
  "citation_format": "[Bribery Act 2010, Section 1]",
  "is_approved_for_rag": false,
  "validation_status": "Candidate - Awaiting Approval"
}
```

### B. Guarantee & Whitelisting Rules
1. **Zero Hallucination:** A citation is generated if and only if its underlying chunk is present in `retrieved_evidence`.
2. **Suppression on Gaps:** When `status != GROUNDED`, `citations` is strictly `[]`.
3. **Traceability:** Every citation carries both the fine-grained `chunk_id` and the parent `source_id`.

---

## 9. Provenance Contract

Provenance records provide compliance officers and auditors with complete regulatory lineage for every chunk cited in an answer.

### A. Schema (`ProvenanceRecord`)
```json
{
  "chunk_id": "RR-UK-01-C01",
  "record_id": "RR-UK-01",
  "source_id": "UK-01",
  "regulation": "Bribery Act 2010",
  "section_article": "Section 1",
  "title": "Offences of bribing another person",
  "jurisdiction": "UK",
  "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
  "version_date": "2010-04-08",
  "effective_date": "2011-07-01",
  "validation_status": "Candidate - Awaiting Approval",
  "is_approved_for_rag": false,
  "retrieval_rank": 1,
  "similarity_score": 0.7171
}
```

### B. Lineage Chain
```
Record ID (RR-UK-01)
  └── Source ID (UK-01)
       └── Section / Article (Section 1)
            └── Official Canonical URL (legislation.gov.uk)
                 └── Temporal Lineage (Effective: 2011-07-01)
                      └── Audit Approval Flag (is_approved_for_rag: false)
```

---

## 10. Evidence Gap Contract

When retrieved evidence is absent or insufficient, the engine emits a structured `GapResult`.

### A. Schema (`GapResult`)
```json
{
  "is_gap": true,
  "gap_type": "MISSING_SPECIFIC_PROVISION",
  "message": "The query requested 'Section 7 (Failure of commercial organisations to prevent bribery)', which is not represented in the canonical ABC Shield corpus (corpus coverage limitation).",
  "user_safe_message": "The requested Section 7 (Failure of commercial organisations to prevent bribery) provision is not represented in the current ABC Shield regulatory evidence corpus. The retrieved evidence contains: RR-UK-01-C01.",
  "retrieved_chunk_ids": ["RR-UK-01-C01"],
  "retrieved_record_ids": ["RR-UK-01"],
  "relevant_evidence_count": 1,
  "approved_evidence_count": 0,
  "has_candidate_evidence": true,
  "requires_human_review": false,
  "coverage_nature": "CORPUS_COVERAGE_LIMITATION",
  "recommended_next_action": "Retrieve additional regulatory evidence containing Section 7 or refine the retrieval query."
}
```

### B. Core Principles from W4.9
1. **Corpus vs. Retrieval Limitation:**
   - `RETRIEVAL_LIMITATION`: Provision exists in the 15-record corpus but was missed by vector retrieval.
   - `CORPUS_COVERAGE_LIMITATION`: Provision is not present in the 15-record canonical ABC Shield corpus.
2. **Safe Regulatory Phrasing:** The system NEVER says *"The law does not contain this section."* It says: *"The requested provision is not represented in the current ABC Shield regulatory evidence corpus."*
3. **No Hallucinated Answers:** When an evidence gap is declared, the LLM is prevented from extrapolating.

---

## 11. Conflict & Relationship Contract

When retrieved evidence contains multiple sources with documented relationships, the engine emits `ConflictFinding` objects.

### A. Schema (`ConflictFinding`)
```json
{
  "conflict_id": "CO-001",
  "topic": "Anti-Bribery / Preventive Procedures",
  "source_id_1": "UK-01",
  "source_1": "Bribery Act 2010",
  "source_id_2": "UK-02",
  "source_2": "Bribery Act 2010 Guidance",
  "relationship": "Overlap - complementary",
  "conflict_type": "OVERLAP",
  "requirement_comparison": "Act creates legal offences; guidance explains procedures organisations can use to prevent bribery and describes six core principles.",
  "scope_difference": "Law applies to relevant offences/organisations; guidance is explanatory and procedural.",
  "authority_difference": "Parliamentary legislation vs Ministry of Justice guidance.",
  "version_effective_date_difference": "Act: 2010; guidance published 2012 and updated 22 Jan 2025.",
  "conflict_status": "No direct conflict identified",
  "rag_use": "Retrieve binding Act requirement first; use guidance as implementation context.",
  "retrieved_source_ids": ["UK-01", "UK-02"],
  "retrieved_chunk_ids": ["RR-UK-01-C01", "RR-UK-02-C01"],
  "both_sources_retrieved": true,
  "source_1_validation_status": "Candidate - Awaiting Approval",
  "source_2_validation_status": "Candidate - Awaiting Approval",
  "source_1_is_approved_for_rag": false,
  "source_2_is_approved_for_rag": false,
  "is_approved_for_rag": false,
  "requires_human_review": true,
  "source_1_jurisdiction": "UK",
  "source_2_jurisdiction": "UK",
  "source_1_authority_level": "A",
  "source_2_authority_level": "B",
  "message": "Retrieved evidence contains a documented regulatory overlap between UK-01 (Bribery Act 2010) and UK-02 (Bribery Act 2010 Guidance). The Conflict Overlap register identifies the relationship as: 'Overlap - complementary'. Documented differences in scope, authority, and version are reported as registered. No legal conflict resolution is made by this system."
}
```

### B. Core Principles from W4.10
1. **Taxonomy Integrity:** Differentiates `OVERLAP` (complementary guidance) and `VERSION_DIFFERENCE` (e.g. OLAF amendments in `CO-010`) from substantive `CONFLICT`.
2. **Both-Source Requirement:** Reported only when BOTH Source A and Source B are present in `retrieved_evidence`.
3. **Zero Legal Adjudication:** Forbidden from declaring legal precedence, declaring a regulation invalid, or declaring compliance.
4. **Severity Clarification:** Severity is **NOT CURRENTLY DETERMINED BY THE RAG LAYER**. To prevent fabricated risk scores, `severity` is omitted or exposed as `null` until a legally verified severity framework is established.

---

## 12. Human Review Contract

Human review by a qualified compliance SME is triggered deterministically via boolean flags:

### A. Review Triggers
`metadata.requires_human_review = true` is set whenever:
1. `len(response.conflicts) > 0`: Any documented regulatory overlap, scope divergence, or version difference is present.
2. `gap.requires_human_review == true`: An ambiguous provision retrieval or unapproved evidence state occurs.
3. `status == ResponseStatus.CONFLICTING_EVIDENCE`: Retrieved evidence presents ungrounded contradictions.
4. `status == ResponseStatus.UNAPPROVED_EVIDENCE`: A query attempts to use candidate records as authoritative.

### B. Frontend / Backend Action
- **Vishal (Backend):** Flags the record in the database as `pending_sme_review = true` and queues a task for compliance officers.
- **Harshini (Frontend):** Renders an amber alert banner: *"Compliance SME Review Required: Documented Regulatory Overlap / Evidence Ambiguity Detected"*.

---

## 13. Metadata Contract

Metadata provides operational context and governance signals.

### A. Schema (`ResponseMetadata`)
```json
{
  "retrieved_count": 5,
  "approved_evidence_count": 0,
  "citation_count": 2,
  "conflict_count": 1,
  "has_gap": false,
  "gap_type": null,
  "requires_human_review": true,
  "has_candidate_evidence": true,
  "response_version": "1.0"
}
```

### B. Critical Safety Distinctions
1. **Confidence Score:** **NOT CURRENTLY PROVIDED / NOT DEFINED**.
   - The RAG engine computes cosine `similarity_score` on individual retrieved chunks (e.g. `0.7171`), but vector similarity is **not** an overall probability or answer confidence score. No fabricated overall confidence score will be emitted.
2. **Execution Time / Latency:** Requested integration field — implementation pending in FastAPI middleware (not currently exposed in core RAG schema).
3. **Model Name:** Sourced from `settings.embedding_model_name` (`"all-MiniLM-L6-v2"`). Can be formally exposed in `ResponseMetadata` in Phase 3.
4. **Retrieval Method:** Dense embedding vector retrieval (`"dense_semantic_chromadb"`). It is NOT keyword retrieval.

---

## 14. Backend Responsibilities — Vishal (FastAPI Lead)

The FastAPI backend must:
1. **Validate Client Requests:** Enforce Pydantic validation on incoming `QueryRequest` payloads (reject empty queries, enforce max length).
2. **Inject Context Safely:** Pass optional client context (`project_id`, `requirement_ids`, `context.jurisdiction`) into the RAG pipeline.
3. **Preserve Complete Provenance:** Store the entire `StructuredAIResponse` without stripping citation keys, chunk IDs, or official URLs.
4. **Enforce Non-Adjudication:** Never attempt to programmatically resolve conflicts, override regulatory differences, or compute automated compliance decisions.
5. **Map External Statuses:** Map internal RAG lifecycle statuses to the agreed external API contract (`SUCCESS`, `GAP_DETECTED`, `CONFLICT_DETECTED`, `NO_SOURCE_FOUND`, `ERROR`).
6. **Mask Internal Errors:** In case of pipeline exceptions, return clean HTTP 500 responses without exposing local filesystem paths, database URIs, or stack traces.

---

## 15. Frontend Responsibilities — Harshini (UI/UX Lead)

The Frontend web application must:
1. **Render Grounded Answers:** Display `answer` text with clear typographic hierarchy.
2. **Display Candidate Development Warnings:** Whenever `metadata.has_candidate_evidence == true`, prominently display:
   > *"Development evidence only: the retrieved regulatory records are currently marked Candidate - Awaiting Approval and have not been approved for authoritative RAG use."*
3. **Render Traceable Citation Badges:** Display clickable citation keys (`[Bribery Act 2010, Section 1]`) that open the evidence provenance drawer displaying official URLs and effective dates.
4. **Render Documented Overlap / Amendment Cards:** Whenever `conflicts` is non-empty, render dedicated cards displaying:
   - Pair Topic & Type: `[CO-001] Anti-Bribery / Preventive Procedures (OVERLAP)`
   - Scope & Authority Differences
   - Disclaimer: *"No legal conflict resolution is made by this system."*
5. **Display Evidence Gap Guidance:** When `gap` is present, display `user_safe_message` and `recommended_next_action` without claiming the law does not exist.
6. **Render Human Review Alerts:** Display an amber review badge whenever `metadata.requires_human_review == true`.
7. **Prohibit UI Adjudication:** Never offer UI toggles that purport to declare one regulation "legally superior" or declare an entity "compliant".

---

## 16. AI / RAG Responsibilities — Padma (RAG Lead)

The AI/RAG engine must:
1. **Guarantee 100% Deterministic Lineage:** Maintain bit-for-bit traceability from query to chunk IDs, source IDs, and canonical records.
2. **Enforce Zero Hallucination on Insufficient Evidence:** Suppress citations and provenance on gaps; abstain safely rather than guessing provisions.
3. **Maintain Fail-Closed Approval Gating:** Restrict approved-only queries strictly to approved records (`filter_approved_only=True` yields 0 candidate chunks).
4. **Preserve Corpus Immutability:** Never modify canonical JSON records, ChromaDB vectors (15 vectors), or raw Excel workbooks during inference.
5. **Execute In-Memory Conflict Detection:** Detect documented pairs deterministically based strictly on the controlled register without LLM adjudication.
6. **Maintain Contract Stability:** Return stable, schema-conforming Pydantic objects across all 34 evaluation cases.

---

## 17. Example JSON — Successful Grounded Response (`SUCCESS`)

Query: *"What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?"*

```json
{
  "request_id": "REQ-7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
  "status": "GROUNDED",
  "answer": "Under Section 1 of the Bribery Act 2010, an individual or commercial organisation commits an offence of bribing another person where they offer, promise, or give a financial or other advantage to another person, intending the advantage to induce or reward the improper performance of a relevant function or activity, or knowing or believing that the acceptance of the advantage itself constitutes improper performance [Bribery Act 2010, Section 1].",
  "grounded": true,
  "gap": null,
  "citations": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "citation_key": "CIT-RR-UK-01-C01",
      "citation_format": "[Bribery Act 2010, Section 1]",
      "is_approved_for_rag": false,
      "validation_status": "Candidate - Awaiting Approval"
    }
  ],
  "provenance": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "jurisdiction": "UK",
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "version_date": "2010-04-08",
      "effective_date": "2011-07-01",
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "retrieval_rank": 1,
      "similarity_score": 0.7171
    }
  ],
  "conflicts": [],
  "retrieved_evidence": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "text": "1. Offences of bribing another person (1) A person (\"P\") is guilty of an offence if P offers, promises or gives a financial or other advantage to another person...",
      "similarity_score": 0.7171,
      "similarity": 0.7171,
      "distance": 0.2829,
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "version_date": "2010-04-08",
      "effective_date": "2011-07-01"
    }
  ],
  "metadata": {
    "retrieved_count": 1,
    "approved_evidence_count": 0,
    "citation_count": 1,
    "conflict_count": 0,
    "has_gap": false,
    "gap_type": null,
    "requires_human_review": false,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

## 18. Example JSON — Evidence Gap Response (`GAP_DETECTED`)

Query: *"What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?"*

```json
{
  "request_id": "REQ-31b8a95f-9204-46f3-a21b-8736d5e1e5cc",
  "query": "What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?",
  "status": "INSUFFICIENT_EVIDENCE",
  "answer": "The available regulatory evidence is insufficient to answer this question. The requested Section 7 provision is not represented in the current ABC Shield regulatory evidence corpus.",
  "grounded": false,
  "gap": {
    "is_gap": true,
    "gap_type": "MISSING_SPECIFIC_PROVISION",
    "message": "The query requested 'Section 7 (Failure of commercial organisations to prevent bribery)', which is not represented in the canonical ABC Shield corpus (corpus coverage limitation).",
    "user_safe_message": "The requested Section 7 (Failure of commercial organisations to prevent bribery) provision is not represented in the current ABC Shield regulatory evidence corpus. The retrieved evidence contains: RR-UK-01-C01.",
    "retrieved_chunk_ids": ["RR-UK-01-C01"],
    "retrieved_record_ids": ["RR-UK-01"],
    "relevant_evidence_count": 1,
    "approved_evidence_count": 0,
    "has_candidate_evidence": true,
    "requires_human_review": false,
    "coverage_nature": "CORPUS_COVERAGE_LIMITATION",
    "recommended_next_action": "Retrieve additional regulatory evidence containing Section 7 or refine the retrieval query."
  },
  "citations": [],
  "provenance": [],
  "conflicts": [],
  "retrieved_evidence": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "text": "1. Offences of bribing another person...",
      "similarity_score": 0.6521,
      "similarity": 0.6521,
      "distance": 0.3479,
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "version_date": "2010-04-08",
      "effective_date": "2011-07-01"
    }
  ],
  "metadata": {
    "retrieved_count": 1,
    "approved_evidence_count": 0,
    "citation_count": 0,
    "conflict_count": 0,
    "has_gap": true,
    "gap_type": "MISSING_SPECIFIC_PROVISION",
    "requires_human_review": false,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

## 19. Example JSON — Documented Relationship / Overlap Response (`CONFLICT_DETECTED`)

Query: *"How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?"*

```json
{
  "request_id": "REQ-84c2f61a-09bb-4f32-8418-4061eb0d5071",
  "query": "How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?",
  "status": "GROUNDED",
  "answer": "The UK Bribery Act 2010 establishes criminal offences for active bribery, passive bribery, and bribery of foreign public officials [Bribery Act 2010, Section 1]. In complementary guidance, the Ministry of Justice outlines Six Principles to assist commercial organisations in designing proportionate bribery prevention procedures [Bribery Act 2010 Guidance, Principle 1].",
  "grounded": true,
  "gap": null,
  "citations": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "citation_key": "CIT-RR-UK-01-C01",
      "citation_format": "[Bribery Act 2010, Section 1]",
      "is_approved_for_rag": false,
      "validation_status": "Candidate - Awaiting Approval"
    },
    {
      "chunk_id": "RR-UK-02-C01",
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "citation_key": "CIT-RR-UK-02-C01",
      "citation_format": "[Bribery Act 2010 Guidance, Principle 1]",
      "is_approved_for_rag": false,
      "validation_status": "Candidate - Awaiting Approval"
    }
  ],
  "provenance": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "jurisdiction": "UK",
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "version_date": "2010-04-08",
      "effective_date": "2011-07-01",
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "retrieval_rank": 1,
      "similarity_score": 0.7410
    },
    {
      "chunk_id": "RR-UK-02-C01",
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "regulation": "Bribery Act 2010 Guidance",
      "section_article": "Principle 1",
      "title": "Proportionate procedures",
      "jurisdiction": "UK",
      "official_source": "https://www.justice.gov.uk/downloads/legislation/bribery-act-2010-guidance.pdf",
      "version_date": "2011-03-30",
      "effective_date": "2011-07-01",
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "retrieval_rank": 2,
      "similarity_score": 0.7185
    }
  ],
  "conflicts": [
    {
      "conflict_id": "CO-001",
      "topic": "Anti-Bribery / Preventive Procedures",
      "source_id_1": "UK-01",
      "source_1": "Bribery Act 2010",
      "source_id_2": "UK-02",
      "source_2": "Bribery Act 2010 Guidance",
      "relationship": "Overlap - complementary",
      "conflict_type": "OVERLAP",
      "requirement_comparison": "Act creates legal offences; guidance explains procedures organisations can use to prevent bribery and describes six core principles.",
      "scope_difference": "Law applies to relevant offences/organisations; guidance is explanatory and procedural.",
      "authority_difference": "Parliamentary legislation vs Ministry of Justice guidance.",
      "version_effective_date_difference": "Act: 2010; guidance published 2012 and updated 22 Jan 2025.",
      "conflict_status": "No direct conflict identified",
      "rag_use": "Retrieve binding Act requirement first; use guidance as implementation context.",
      "retrieved_source_ids": ["UK-01", "UK-02"],
      "retrieved_chunk_ids": ["RR-UK-01-C01", "RR-UK-02-C01"],
      "both_sources_retrieved": true,
      "source_1_validation_status": "Candidate - Awaiting Approval",
      "source_2_validation_status": "Candidate - Awaiting Approval",
      "source_1_is_approved_for_rag": false,
      "source_2_is_approved_for_rag": false,
      "is_approved_for_rag": false,
      "requires_human_review": true,
      "source_1_jurisdiction": "UK",
      "source_2_jurisdiction": "UK",
      "source_1_authority_level": "A",
      "source_2_authority_level": "B",
      "message": "Retrieved evidence contains a documented regulatory overlap between UK-01 (Bribery Act 2010) and UK-02 (Bribery Act 2010 Guidance). The Conflict Overlap register identifies the relationship as: 'Overlap - complementary'. Documented differences in scope, authority, and version are reported as registered. No legal conflict resolution is made by this system."
    }
  ],
  "retrieved_evidence": [
    {
      "chunk_id": "RR-UK-01-C01",
      "record_id": "RR-UK-01",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 1",
      "title": "Offences of bribing another person",
      "text": "1. Offences of bribing another person...",
      "similarity_score": 0.7410,
      "similarity": 0.7410,
      "distance": 0.2590,
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/contents",
      "version_date": "2010-04-08",
      "effective_date": "2011-07-01"
    },
    {
      "chunk_id": "RR-UK-02-C01",
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "regulation": "Bribery Act 2010 Guidance",
      "section_article": "Principle 1",
      "title": "Proportionate procedures",
      "text": "Principle 1: Proportionate procedures...",
      "similarity_score": 0.7185,
      "similarity": 0.7185,
      "distance": 0.2815,
      "validation_status": "Candidate - Awaiting Approval",
      "is_approved_for_rag": false,
      "official_source": "https://www.justice.gov.uk/downloads/legislation/bribery-act-2010-guidance.pdf",
      "version_date": "2011-03-30",
      "effective_date": "2011-07-01"
    }
  ],
  "metadata": {
    "retrieved_count": 2,
    "approved_evidence_count": 0,
    "citation_count": 2,
    "conflict_count": 1,
    "has_gap": false,
    "gap_type": null,
    "requires_human_review": true,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

## 20. Versioning & Backward Compatibility

- **Current Contract Version:** `schema_version = "1.0"` (stamped in `metadata.response_version = "1.0"`).
- **SemVer Specification:** The contract adheres to Semantic Versioning (`MAJOR.MINOR.PATCH`).
  - *Patch (1.0.x):* Documentation clarification, internal bug fixes that do not modify JSON keys.
  - *Minor (1.x.0):* Backward-compatible additive changes (e.g. adding optional `model_name` or `latency_ms` to `metadata`).
  - *Major (2.0.0):* Breaking structural alterations (e.g. renaming fields, altering nesting hierarchies, or deprecating status enums).
- **Backward Compatibility Guarantee:** Existing consumers parsing version 1.0 will not break upon additive metadata fields. Extra unknown fields on client requests are strictly rejected via Pydantic `extra="forbid"` to prevent payload pollution.

---

## 21. Acceptance Criteria

This integration contract is formally accepted by the engineering team when all the following criteria are validated:

- [x] **Input Contract Defined:** Supported and optional fields (`query`, `project_id`, `requirement_ids`, `context`) specified with exact constraints.
- [x] **Processing Lifecycle Defined:** 8-stage RAG processing workflow clearly documented.
- [x] **Output Contract Defined:** Complete top-level `StructuredAIResponse` schema specified.
- [x] **Status Mapping Formulated:** Bidirectional mapping between internal RAG statuses and external API statuses (`SUCCESS`, `GAP_DETECTED`, `CONFLICT_DETECTED`, `NO_SOURCE_FOUND`, `ERROR`) documented.
- [x] **Citation & Provenance Contract Formalized:** Deterministic generation, chunk-level keys, and full lineage chains documented.
- [x] **Evidence Gap Handling Formalized:** W4.9 distinctions (`CORPUS_COVERAGE_LIMITATION` vs `RETRIEVAL_LIMITATION`) and accurate non-hallucinatory language preserved.
- [x] **Conflict / Relationship Handling Formalized:** W4.10 taxonomy (`OVERLAP`, `VERSION_DIFFERENCE`), both-source rule, and single-source suppression preserved.
- [x] **Human Review Contract Formalized:** Exact deterministic conditions triggering `requires_human_review = true` defined.
- [x] **No Fabricated Scores:** `confidence` and `severity` explicitly designated as not currently provided by the RAG layer.
- [x] **No Legal Adjudication:** Mandatory disclaimers and forbidden phrases enforced.
- [x] **Role Boundaries Agreed:** Distinct responsibilities for Vishal (backend), Harshini (frontend), and Padma (RAG) established.
- [x] **Zero Production/Data Mutations:** Verified that no code, databases, or raw files are modified in Phase 2.

---

## 22. Open Questions & Team Confirmation Required

Before moving to implementation (Phase 3), confirmation is requested from Vishal and Harshini on the following points:

1. **Status Mapping Adoption (Vishal / Harshini):**
   - Does the proposed mapping in Section 7 cleanly satisfy backend routing and frontend UI state machines?
   - Confirm whether `CONFLICT_DETECTED` on grounded answers should return HTTP 200 with `status: "CONFLICT_DETECTED"` (recommended) or `status: "SUCCESS"` with `conflicts: [...]`.
2. **Context Binding Fields (Vishal):**
   - Confirm whether `project_id`, `requirement_ids`, and `advisor_advice_ids` should be accepted directly in the request body as optional attributes in Phase 3.
3. **Execution Latency & Metadata (Vishal / Harshini):**
   - Should `latency_ms` (execution time) and `model_name` be added to `ResponseMetadata` in Phase 3? (Padma recommends adding them under `metadata` in a backward-compatible minor revision).
4. **Treatment of Severity (Vishal):**
   - Vishal requested `severity: LOW | MEDIUM | HIGH`. Because the regulatory corpus does not currently define legal severity, confirm that `severity` should remain `null` or be deferred until legal compliance establishes a scoring rubric.
5. **Session & Feedback Storage (Vishal):**
   - Will the backend persist each `request_id` and complete `StructuredAIResponse` in PostgreSQL / MongoDB, or will caching be handled via Redis?

---

## 23. Phase Status

- **Task Status:** **W4.11 Phase 2 — DRAFT CONTRACT CREATED.**
- **Governance:** **Awaiting formal confirmation from Vishal (Backend Lead) and Harshini (Frontend Lead).**
- **Execution Boundary:** In strict compliance with instructions, **zero production API or RAG code was modified, ChromaDB was untouched, and no further phases have been executed.**
