# ABC Shield AI / FinRegTech ShipYard

AI/RAG & Conflict Detection Module for **ABC Shield / FinRegTech ShipYard**.

- **Module Lead**: Padma Kumar — AI/RAG & Conflict Detection
- **Data Provider**: Madhesh — Regulatory Data & Knowledge
- **Domain Scope**:
  - UK anti-bribery and corruption framework (e.g., Bribery Act 2010, Ministry of Justice Guidance)
  - EU-level anti-bribery and anti-corruption framework (e.g., EU anti-corruption directives, OLAF regulations)
  - FCA financial-crime systems and controls material where relevant (e.g., FCA Handbook FCG 6, Principle 1)

---

## Task 2: Regulatory Data Ingestion

The ingestion layer (`rag/ingestion/`) parses, normalizes, validates, and chunks regulatory records delivered in Excel workbooks without modifying source files.

### 1. What the Ingestion Module Does
- **Loads** raw regulatory workbooks safely in read-only mode using `openpyxl`.
- **Enriches & Normalizes** individual regulatory records by linking them to their corresponding source in the Source Register.
- **Validates** completeness of mandatory fields, checks URL formats, and audits validation statuses.
- **Guards Validation Status**: Prevents `Candidate - Awaiting Approval` records from being erroneously marked as authoritative approved evidence.
- **Chunks** records along section/article/boundary lines while copying 100% of parent metadata and provenance keys to every chunk.
- **Exports** processed JSON artifacts to `data/processed/` for downstream RAG retrieval preparation.

### 2. The Three Input Excel Files & Their Roles
All original regulatory files are stored in `data/raw/` and are treated as strictly read-only and immutable:
- **`ABC shield_Data Dictionary.xlsx`**: Defines expected regulatory data fields and definitions.
- **`ABC_Shield_Source_Register (1).xlsx`**: Source-level catalog (15 sources: UK-01 to UK-09, EU-01 to EU-06) providing high-level metadata: Source Name, Issuing Authority, Jurisdiction, Source Type, Authority Level (A/B/C/D), Publication/Effective Dates, Canonical URLs, Topics, and Approval Status.
- **`ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx`**: Contains core regulatory provisions (`Regulatory Records` sheet, 15 records), operational validation notes (`Validation Notes`), pre-mapped overlaps/conflicts (`Conflict Overlap`, 11 mappings), and taxonomies (`Conflict Overlap Guide`).

### 3. Connecting Source Register and Regulatory Records
The Regulatory Records are joined to the Source Register using the primary key `Source_ID`. Every record maps 1-to-1 to a valid source entry. Both record-level and source-level fields are retained in the internal representation to avoid silent overwrites or data loss.

### 4. How Normalization Works
`RegulatoryDataNormalizer` maps the raw row dictionaries into typed `NormalizedRegulatoryRecord` Pydantic models with attached source metadata.

### 5. Preserving Validation & Approval Status
All 15 records in the current delivery are marked as **`Candidate - Awaiting Approval`**. The Pydantic model and `RegulatoryDataValidator` enforce that `is_approved_for_rag` evaluates to `False` for any record with `candidate`, `pending`, or `awaiting` in its status. Candidate records are never converted to Approved.

### 6. Distinction: Requirement vs. Regulatory_Text
- **`Requirement`**: A concise, structured paraphrase of the regulatory provision prepared by the knowledge engineer for operational clarity.
- **`Regulatory_Text`**: Verbatim, official legal text directly quoted from the consolidated statute or legal instrument.
- **Current Data Status**: The delivered `Regulatory Records` workbook provides `Requirement` summaries, but does **not** contain verbatim `Regulatory_Text`.
- **Guardrail**: The ingestion pipeline explicitly sets `regulatory_text: null` and logs this distinction. It **never** copies `Requirement` into `regulatory_text`.

### 7. Provenance Preservation
Every generated artifact preserves full lineage: `record_id`, `source_id`, `regulation`, `regulator`, `jurisdiction`, `section_article`, `official_source`, `authority_level`, and `validation_status`.

### 8. Storage of Processed Artifacts
- `data/processed/normalized_regulatory_records.json`: 15 normalized records with joined source metadata.
- `data/processed/regulatory_chunks.json`: 15 chunk representations ready for vector embedding and indexing in Task 3.

---

## Task 3: Embeddings & Vector Storage

The retrieval storage layer (`rag/retrieval/`) embeds the processed regulatory chunks and indexes them in a persistent ChromaDB vector store.

### 1. Embedding Model Used
- **Model**: `all-MiniLM-L6-v2` via `sentence-transformers`.
- **Embedding Dimension**: 384 dimensions.

### 2. Why It Is Used
- **Offline & Local**: Runs entirely locally on CPU without requiring external API keys, tokens, network latency, or incurring per-call costs during development.
- **High Semantic Density**: Optimized for fast sentence and paragraph semantic similarity comparisons.
- **Configurable**: Managed via `EmbeddingManager(model_name=...)` so the model can be updated or swapped to multilingual or larger models if needed later.

### 3. ChromaDB Purpose
- Serves as the embedded, zero-infrastructure vector store for dense retrieval.
- Organizes embeddings into collections with Cosine distance indexing (`hnsw:space: cosine`).
- Supports exact scalar metadata filtering (e.g., `is_approved_for_rag == True`, `jurisdiction == "UK"`), allowing regulatory guardrails to be enforced directly in the database.

### 4. Vector Storage Location
- **Path**: `data/processed/chroma_db/`
- **Collection Name**: `regulatory_records`
- **Persistence**: Managed via ChromaDB's `PersistentClient`, ensuring vector indexes and metadata persist across restarts.

### 5. Metadata Preserved in ChromaDB
Every vector entry retains scalar metadata corresponding to the regulatory chunk:
- `chunk_id`: Unique chunk identifier (document ID in ChromaDB, e.g. `RR-UK-01-C01`)
- `record_id`: Parent regulatory record ID (e.g. `RR-UK-01`)
- `source_id`: Parent source ID (e.g. `UK-01`)
- `regulation`: Instrument title (e.g. `Bribery Act 2010`)
- `regulator`: Governing authority (e.g. `UK Parliament / legislation.gov.uk`)
- `jurisdiction`: Jurisdiction (`UK`, `EU`)
- `section_article`: Legal section or article reference (e.g. `Section 1`)
- `title`: Section or requirement title
- `topic`: Regulatory taxonomy topic
- `official_source`: Canonical URL
- `version_date`: Version timestamp
- `effective_date`: Effective date
- `validation_status`: `"Candidate - Awaiting Approval"`
- `is_approved_for_rag`: `False` (boolean flag)
- `text_type`: `"requirement_paraphrase"`
- `authority_level`: Authority level (`A`, `B`, `C`, `D`)
- `source_type`: Source classification (e.g. `Primary Legislation`)
- `chunk_index`: 0-indexed position within record
- `total_chunks`: Total chunks for record

### 6. Approval-Status Handling & Guardrail Design
- All 15 stored chunks have `is_approved_for_rag = False` and `validation_status = "Candidate - Awaiting Approval"`.
- The retrieval interface (`RegulatoryRetriever`) accepts an optional `filter_approved_only: bool = False` parameter. When set to `True`, it queries ChromaDB with `where={"is_approved_for_rag": True}`.
- When `filter_approved_only=True` is queried against the current knowledge base, it returns zero records, correctly reflecting that no approved authoritative records exist yet and preventing hallucinated or unapproved legal advice.

### 7. How Retrieval Works
1. Query input is embedded into a 384-dimensional vector using `EmbeddingManager.embed_text(query)`.
2. ChromaDB evaluates cosine similarity across the collection.
3. Relevant chunks within `top_k` are retrieved along with cosine distances.
4. Results are wrapped in structured `RetrievalResult` models displaying:
   - Chunk ID and complete provenance lineage
   - Matched requirement text and `text_type`
   - Cosine similarity score (`1.0 - distance`)
   - Explicit `validation_status` and `is_approved_for_rag` flags
5. **No LLM generation is performed** — the output is purely verifiable evidence.

### 8. Current Data Limitation
All 15 regulatory records delivered by the Regulatory Data & Knowledge module are currently `Candidate - Awaiting Approval`. Therefore, all retrieved evidence must be treated as candidate material pending SME validation, and cannot be cited as final authoritative compliance conclusions.

---

## Task 4: Vector Retrieval Layer

Task 4 implements and verifies the semantic retrieval layer connecting the persistent vector store to downstream analysis and RAG generation without calling any LLM.

### 1. Responsibilities of Retrieval Components
- **`EmbeddingManager`** (`rag/retrieval/embeddings.py`): Encodes input natural-language queries into 384-dimensional normalized dense vectors using `all-MiniLM-L6-v2`.
- **`ChromaVectorStore`** (`rag/retrieval/vector_store.py`): Reuses the existing persistent ChromaDB database (`data/processed/chroma_db/`) and executes cosine similarity searches against the `regulatory_records` collection.
- **`RegulatoryRetriever`** (`rag/retrieval/retriever.py`): High-level retrieval interface that:
  - Generates query vectors.
  - Applies optional metadata filters (`jurisdiction`, `filter_approved_only`).
  - Converts database results into structured `RetrievalResult` objects preserving complete provenance.
  - Strictly returns evidence only (zero LLM hallucinations or legal advice).

### 2. Guardrail Enforcement
- **Approved-Only Filtering**: `RegulatoryRetriever.retrieve(..., filter_approved_only=True)` queries ChromaDB with `where={"is_approved_for_rag": True}`. Since all 15 records in the knowledge base are currently `Candidate - Awaiting Approval` (`is_approved_for_rag = False`), this query safely returns **0 records**, preventing unapproved evidence from being fed into authoritative generation.
- **Provenance Retention**: Every retrieved result includes `chunk_id`, `record_id`, `source_id`, `regulation`, `regulator`, `jurisdiction`, `section_article`, `title`, `topic`, `official_source`, `validation_status`, `is_approved_for_rag`, `text_type`, `distance`, and `similarity_score`.

### 3. Test Queries & Relevance Differentiation
- **Query 1** (*"What does the Bribery Act 2010 say about bribing another person?"*):
  - Returns in-scope UK anti-bribery materials (e.g. `RR-UK-07-C01`, `RR-UK-05-C01`, `RR-UK-04-C01`, `RR-UK-01-C01`) with moderate-to-high similarity (0.45 - 0.58).
- **Query 2** (*"What are practical anti-bribery controls?"*):
  - Strongly matches practical control guidance `RR-UK-07-C01` (similarity: 0.6935) and FCA control expectations `RR-UK-08-C01` (similarity: 0.6372).
- **Query 3** (*"What cybersecurity requirements apply?"*):
  - Out-of-scope query testing relevance boundaries. Cosine similarity drops dramatically (< 0.30; distance > 0.70), demonstrating that out-of-scope queries can be detected and flagged before generation.

---

## Task 5: Grounded LLM Generation Layer

Task 5 implements the provider-independent grounded generation layer on top of Task 4 vector retrieval.

### 1. Architecture Flow
```text
User Question
    │
    ▼
Task 4 RegulatoryRetriever (semantic retrieval over existing ChromaDB)
    │
    ▼
Retrieved Regulatory Evidence (1-5 chunks with full provenance metadata)
    │
    ▼
Task 5 GroundedGenerator (deterministic context building & safety guardrails)
    │
    ▼
Provider-Independent LLM (Mock / OpenAI / Ollama)
    │
    ▼
Structured GroundedResponse (answer, evidence_used, status, approval warning)
```

### 2. Responsibilities of Generation Components
- **`prompts.py`** (`rag/generation/prompts.py`):
  - `SYSTEM_GROUNDING_PROMPT`: Strictly confines answers to supplied evidence, prohibits hallucinations, enforces prompt-injection defense (treating evidence as untrusted data), and forbids compliance determinations.
  - `build_evidence_context`: Deterministically formats chunks with Chunk ID, Record ID, Source ID, Regulation, Section/Article, Title, Jurisdiction, Status, and Text.
  - `build_user_prompt`: Assembles user question and evidence block with explicit citation instructions.
- **`llm_interface.py`** (`rag/generation/llm_interface.py`):
  - `BaseLLMProvider`: Abstract base interface.
  - `MockLLMProvider`: Deterministic provider for repeatable offline unit testing.
  - `OpenAILLMProvider`: OpenAI and OpenAI-compatible client (using `openai` / `httpx`).
  - `OllamaLLMProvider`: Local Ollama HTTP API provider.
  - `get_llm_provider`: Dynamic factory resolving provider from configuration.
- **`grounded_generator.py`** (`rag/generation/grounded_generator.py`):
  - `GroundedGenerator`: Coordinates retrieval, safety checks, context building, and LLM calls.
  - `GroundedResponse`: Structured Pydantic model returning answer, evidence IDs, grounded status, and approval warnings.

### 3. Safety Guardrails Implemented
- **Empty Retrieval Guardrail**: If zero evidence is retrieved (e.g. approved-only filter on unapproved data), the LLM is **never called**. A controlled `INSUFFICIENT_EVIDENCE` response is returned immediately.
- **Approval Warning Guardrail**: If any chunk has `is_approved_for_rag = False`, an explicit warning is attached:
  > *"Development evidence only: the retrieved regulatory records are currently marked Candidate - Awaiting Approval and have not been approved for authoritative RAG use."*
- **Prompt-Injection Defense**: The system prompt explicitly designates all evidence as untrusted data, preventing adversarial payload instructions inside documents from overriding generation rules.
- **True Evidence Grounding**: The generator (including `MockLLMProvider`) parses prompt evidence dynamically and references strictly the supplied chunks and metadata. It never injects external or unretrieved provisions, and honestly returns `INSUFFICIENT_EVIDENCE` when specific statutory sections requested by the user are missing from retrieved context.

---

## Task 6: Citation & Provenance Layer

Task 6 implements a deterministic citation and provenance layer on top of Task 5 grounded generation.

### 1. Primary Architecture
```text
User Question
    │
    ▼
Task 4 RegulatoryRetriever (semantic vector search against ChromaDB)
    │
    ▼
Retrieved Regulatory Evidence (1-5 chunks with complete provenance)
    │
    ▼
Task 5 GroundedGenerator (guardrails & provider-independent LLM)
    │
    ▼
Grounded Answer
    │
    ▼
Task 6 CitationBuilder (retrieved-evidence provenance & whitelist validation)
    │
    ▼
Structured GroundedResponse with verified Citations & Provenance
```

### 2. Complete Provenance Chain
Every citation exposes an auditable lineage:
```text
AI Answer
  ↓
Retrieved Chunk (e.g. RR-UK-01-C01)
  ↓
Record ID (e.g. RR-UK-01)
  ↓
Source ID (e.g. UK-01)
  ↓
Regulation (e.g. Bribery Act 2010)
  ↓
Section/Article (e.g. Section 1)
  ↓
Official Source URL (e.g. https://www.legislation.gov.uk/ukpga/2010/23/contents)
  ↓
Version/Date (e.g. Current official version)
  ↓
Effective Date (e.g. 8 April 2010)
  ↓
Validation Status (Candidate - Awaiting Approval)
  ↓
Approval Status (is_approved_for_rag = False)
```

### 3. Core Citation Integrity Rules
- **Retrieved-Evidence Provenance**: Citations represent the retrieved evidence chunks supplied as grounding context, not sentence-level LLM attribution.
- **Whitelist Verification**: A citation may **ONLY** reference a chunk where `citation.chunk_id ∈ retrieved_chunk_ids`. Any unretrieved chunk is strictly rejected.
- **LLM Independence**: Citations, URLs, and section numbers are constructed deterministically from `RetrievalResult` metadata outside the LLM. The LLM is never asked to generate citations.
- **Empty / Insufficient Evidence Guard**: When `is_grounded = False` or `status = "INSUFFICIENT_EVIDENCE"` (or empty retrieval), `citations = []` and `provenance = []`.
- **Human-Readable Format**: Generates standardized strings: `[Chunk ID | Record ID | Regulation | Section/Article]` (e.g. `[RR-UK-01-C01 | RR-UK-01 | Bribery Act 2010 | Section 1]`).
- **Candidate Status Retention**: Citations faithfully preserve `validation_status = "Candidate - Awaiting Approval"` and `is_approved_for_rag = False`.

---

## Task 7: GAP / No-Source Handling Layer

Task 7 implements a deterministic **GAP / No-Source Handling layer** that analyzes, categorizes, and discloses evidence deficiencies when the available regulatory data is insufficient to answer a query.

### 1. Architectural Scope
```text
User Question
    │
    ▼
Task 4 RegulatoryRetriever (semantic vector search against ChromaDB)
    │
    ▼
Retrieved Regulatory Evidence (1-5 chunks with complete provenance)
    │
    ▼
Task 5 GroundedGenerator (guardrails & provider-independent LLM)
    │
    ▼
Task 6 CitationBuilder (retrieved-evidence provenance & whitelist validation)
    │
    ▼
Task 7 GapHandler (deterministic GAP analysis & safe action guidance)
    │
    ▼
Structured GroundedResponse with verified Citations, Provenance & GAP Diagnostics
```

> [!IMPORTANT]
> **Scope Distinction**: This layer performs **regulatory evidence gap handling** (deficiencies in available regulatory sources). It is **NOT** company readiness or compliance gap analysis.

### 2. Gap Taxonomy (`GapType`)
1. **`NO_RETRIEVED_EVIDENCE`**: Zero chunks retrieved from the knowledge base for this query.
2. **`INSUFFICIENT_RETRIEVED_EVIDENCE`**: Chunks were retrieved, but lack the depth or provisions needed to address the query.
3. **`OUT_OF_SCOPE`**: The requested topic falls outside the ABC Shield project scope (UK/EU anti-bribery & corruption and relevant FCA controls), such as cybersecurity, general AML, sanctions, or tax evasion.
4. **`MISSING_SPECIFIC_PROVISION`**: The user explicitly asked for a specific section, article, or provision (e.g. Bribery Act 2010 Section 1), which is absent from the retrieved chunks.
5. **`UNAPPROVED_EVIDENCE`**: Relevant evidence was retrieved, but all matching records have `validation_status = "Candidate - Awaiting Approval"` and cannot be queried authoritatively under approved-only mode.
6. **`UNKNOWN_EVIDENCE_GAP`**: Fallback classification.

### 3. Core Safety & Disclosure Principles
- **No Extrapolation**: The system never uses LLM general training knowledge or assumptions to guess or fill missing regulatory requirements.
- **Retrieved Evidence vs. Knowledge Base**: When a provision is missing from retrieved chunks (e.g. Bribery Act Section 1 at `top_k=3`), the disclosure states:
  > *"The requested Section 1 provision is not present in the retrieved evidence."*
  It never claims that the section does not exist in law or in the knowledge base.
- **Separation of Concepts**: Relevance, sufficiency, and approval status are evaluated independently. Candidate status does not automatically mark evidence as irrelevant or nonexistent.

---

## Task 8: Conflict / Overlap Detection

The conflict and overlap detection layer (`rag/conflict/`) deterministically identifies whether retrieved regulatory sources participate in any known conflict or overlap relationships recorded in the controlled dataset.

> *"Task 8 identifies documented regulatory conflict/overlap relationships in retrieved evidence. It does not determine legal applicability, resolve conflicts, or decide which source controls."*

### 1. Why Conflict Detection Is Needed
In anti-bribery and corruption compliance, multiple regulatory instruments frequently address the same topic with different legal standing, scopes, and procedural depths. For example, primary legislation (e.g. the UK Bribery Act 2010) defines statutory offences, while departmental guidance (Ministry of Justice) details preventive procedures and the Six Principles, and regulator handbooks (FCA FCG 6) specify internal governance expectations. Compliance officers and RAG systems need transparent visibility into how retrieved sources interact without assuming that one source invalidates or supersedes another.

### 2. Controlled Data Source
Detection is based strictly on the 11 pre-mapped pairs in the `Conflict Overlap` worksheet of `data/raw/ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx`. The system treats this register as the authoritative catalogue of known relationships:
- **`CO-001`**: UK-01 (Bribery Act 2010) ↔ UK-02 (Bribery Act 2010 Guidance) — *Overlap - complementary*
- **`CO-002`**: UK-01 (Bribery Act 2010) ↔ UK-03 (FCA FCG 6) — *Overlap - complementary*
- **`CO-003`**: UK-03 (FCA FCG 6) ↔ UK-09 (FCA Principle 1) — *Overlap - complementary*
- **`CO-004`**: UK-01 (Bribery Act 2010) ↔ UK-05 (Trade Risk Guidance) — *Overlap - complementary*
- **`CO-005`**: UK-06 (PSFA Professional Standard) ↔ UK-07 (Practice Note) — *Overlap - complementary*
- **`CO-006`**: UK-03 (FCA FCG 6) ↔ UK-08 (FCA Bribery & Corruption page) — *Overlap - same regulator, different presentation*
- **`CO-007`**: EU-01 (Directive (EU) 2026/1021) ↔ EU-02 (EU Legislation Index) — *Overlap - legal act plus explanatory index*
- **`CO-008`**: EU-01 (Directive (EU) 2026/1021) ↔ EU-06 (EU Anti-Corruption Strategy) — *Overlap - policy alignment, not same legal level*
- **`CO-009`**: EU-03 (Whistleblower Directive) ↔ EU-01 (Directive (EU) 2026/1021) — *Partial thematic overlap*
- **`CO-010`**: EU-04 (OLAF Regulation 883/2013) ↔ EU-05 (Amending Regulation 2020/2223) — *Direct legal relationship - amendment, not conflict*
- **`CO-011`**: EU-01 (Directive (EU) 2026/1021) ↔ EU-04 (OLAF Regulation 883/2013) — *Partial thematic overlap*

### 3. Purely Deterministic Matching Rules
- **Both Sources Required**: A conflict/overlap is reported only when **both** `Source_ID_1` and `Source_ID_2` are present in the retrieved evidence chunks.
- **One-Sided Retrieval**: If only one source of a documented pair is retrieved (e.g. UK-01 retrieved without UK-02), no active conflict finding is reported. The system never assumes the unretrieved source applies to the query.
- **Zero Invented Conflicts**: Semantic similarity alone never creates a conflict. Two retrieved sources lacking an entry in the controlled register (e.g. UK-01 and EU-03) produce zero findings.
- **Deduplication**: Multiple chunks from the same source (e.g. 2 chunks from UK-01 and 1 from UK-02) produce exactly one `ConflictFinding` per `Conflict_ID`, preserving retrieval chunk order.

### 4. Preservation of Documented Differences
The detector preserves all documented distinctions from the controlled dataset:
- `relationship`: Exact string from Excel (e.g. "Overlap - complementary").
- `conflict_type`: Normalized taxonomy (`OVERLAP`, `VERSION_DIFFERENCE`, `SCOPE_DIFFERENCE`, `AUTHORITY_DIFFERENCE`, `CONFLICT`, `UNKNOWN_RELATIONSHIP`).
- `requirement_comparison`: Documented operational/legal requirement comparison.
- `scope_difference`: Documented scope boundaries.
- `authority_difference`: Issuing authority differences (e.g. Parliament vs. Ministry of Justice).
- `version_effective_date_difference`: Effective publication and amendment timelines.
- `conflict_status`: Register status (e.g. "No direct conflict identified", "No conflict; version/amendment relationship").
- `rag_use`: Prescribed retrieval usage guidelines.

### 5. Legal Neutrality & Approval Separation
- **No Adjudication**: The detector never declares that one source overrides another, which regulation wins, or which regulation controls. Every finding outputs a neutral system message:
  > *"Retrieved evidence contains a documented relationship between [Source 1] and [Source 2]... No legal conflict resolution is made by this system."*
- **Approval Separation**: The detector reports `source_1_validation_status`, `source_2_validation_status`, `source_1_is_approved_for_rag`, and `source_2_is_approved_for_rag`. The aggregate `is_approved_for_rag` evaluates to `True` only when both sources are independently approved. Candidate status is strictly preserved.

### 6. Pipeline Architecture
```
Madhesh Excel Data
        ↓
Task 2 Ingestion & Normalization
        ↓
Task 3 Embeddings & ChromaDB
        ↓
Task 4 Semantic Retrieval
        ↓
 ┌──────────────────────────────────────┐
 │ Retrieved Evidence (RetrievalResult) │
 └──────────────────┬───────────────────┘
                    ↓
        ┌───────────┴────────────┐
        ↓                        ↓
   GAP Handler           Conflict Detector (Task 8)
        ↓                        ↓
   GapResult             Conflict Findings (List[ConflictFinding])
        ↓                        ↓
        └───────────┬────────────┘
                    ↓
            Grounded Generator (Task 5)
                    ↓
            Citation Builder (Task 6)
                    ↓
            GroundedResponse (answer, citations, provenance, gap, conflicts)
                    ↓
            Task 9 Structured AI Output
```

---

## Task 9: Structured AI Output Contract

The structured output layer (`rag/output/`) provides a single, predictable, machine-readable JSON response contract (`StructuredAIResponse`) that unifies the outputs of Tasks 4 through 8.

> *"Task 9 is strictly an output composition layer. It does not create new regulatory knowledge, make legal decisions, resolve conflicts, or generate citations independently."*

### 1. Why a Structured Output Contract Is Needed
In multi-stage regulatory RAG pipelines, disparate components produce diverse artifacts: vector retrieval returns chunk records, the grounded generator produces synthesized answers and grounding flags, the citation builder produces whitelisted citations and audit provenance chains, the GAP handler classifies evidence deficiencies, and the conflict detector surfaces documented relationships between sources. 

Downstream consumers—such as Vishal's backend/FastAPI service (Task 11) and Harshini's compliance UI/frontend—require a unified, schema-validated, and stable contract rather than having to coordinate multiple independent modules.

### 2. How Tasks 4–8 Feed into Task 9
`StructuredResponseBuilder` performs purely deterministic assembly:
- **Task 4 (Retrieval)**: Formats retrieved chunks into `retrieved_evidence: List[RetrievedEvidenceItem]` with exact similarity scores, distances, and approval statuses preserved.
- **Task 5 (Grounded Generation)**: Supplies `answer: Optional[str]` and `grounded: bool`.
- **Task 6 (Citations & Provenance)**: Supplies whitelisted `citations: List[Citation]` and traceable `provenance: List[ProvenanceRecord]`.
- **Task 7 (GAP Handling)**: Supplies `gap: Optional[GapResult]` when evidence is insufficient or missing.
- **Task 8 (Conflict Detection)**: Supplies documented `conflicts: List[ConflictFinding]`.
- **Metadata**: Calculates deterministic `ResponseMetadata` counts (`retrieved_count`, `approved_evidence_count`, `citation_count`, `conflict_count`, `has_gap`, `response_version = "1.0"`).

### 3. Response Status Mapping (`ResponseStatus`)
Task 9 does **not** independently classify GAPs or query an LLM for status. It maps deterministic lifecycle statuses directly from Task 7's `GapType` and Task 5's `grounded` state:
1. **`OUT_OF_SCOPE`**: Assigned when Task 7 detects an out-of-scope query domain (e.g. cybersecurity, DORA, general AML).
2. **`UNAPPROVED_EVIDENCE`**: Assigned when Task 7 detects that relevant evidence exists but is gated under candidate approval status.
3. **`INSUFFICIENT_EVIDENCE`**: Assigned when Task 7 detects missing specific provisions, empty retrieval, or general insufficient evidence.
4. **`GROUNDED`**: Assigned when Task 5 confirms successful grounding on retrieved evidence with zero evidence gaps.
5. **`ERROR`**: Reserved exclusively for unexpected pipeline execution failures.

### 4. Integration Boundaries & Safety Guardrails
- **Zero Intelligence Addition**: The builder does not perform second-stage reasoning, summarize, or alter text.
- **No Hallucinated Citations or Conflicts**: Citation whitelist rules from Task 6 and controlled register bindings from Task 8 are strictly maintained.
- **Null Safety**: List fields default to empty lists (`[]`), never `null`. `gap` is `null` when the response is grounded.
- **Clean Separation from API/UI**: Task 9 defines the data contract only. FastAPI endpoints and frontend components remain isolated to Tasks 11+.

---

## Directory Tree

```text
abc-shield-ai/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── analysis/
│   ├── __init__.py
│   ├── conflict/
│   │   └── __init__.py
│   └── gap/
│       └── __init__.py
├── api/
│   └── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── processed/
│   │   ├── .gitkeep
│   │   ├── chroma_db/
│   │   │   └── chroma.sqlite3
│   │   ├── normalized_regulatory_records.json
│   │   └── regulatory_chunks.json
│   └── raw/
│       ├── .gitkeep
│       ├── ABC shield_Data Dictionary.xlsx
│       ├── ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx
│       └── ABC_Shield_Source_Register (1).xlsx
---

## Task 10: RAG Evaluation and Safety Testing

The evaluation framework (`rag/evaluation/`) provides an empirical, reproducible benchmarking suite that rigorously measures the performance, groundedness, citation validity, GAP classification accuracy, conflict detection, and safety/adversarial robustness of the ABC Shield regulatory RAG pipeline without relying on an LLM as the sole evaluator.

> *"Task 10 measures real system behavior against controlled benchmarks. It does not invent accuracy figures, modify ChromaDB, re-index data, or alter candidate validation statuses."*

### 1. Key Evaluation Dimensions & Results

| Dimension | Measured Metric | Result | Operational Significance |
| :--- | :--- | :--- | :--- |
| **Retrieval Performance** | Precision@1 / @3 / @5 | **0.3810 / 0.2857 / 0.1810** | Record-level deduplicated precision across 21 applicable cases |
| | Recall@1 / @3 / @5 | **0.2619 / 0.5952 / 0.6429** | Multi-source recall expands significantly from K=1 to K=5 |
| | Hit Rate@1 / @3 / @5 | **0.3810 / 0.6667 / 0.7143** | >71% chance of retrieving relevant authority within top 5 |
| | MRR (Mean Reciprocal Rank) | **0.5016** | Average rank of first relevant chunk is ~2.0 |
| **Exact Provision Analysis** | Bribery Act Section 1 Rank | **Rank #4 (Score: 0.5028)** | Top rank retrieved generic guidance (`RR-UK-07-C01`); confirms recommendation for hybrid BM25 + dense vector search |
| **Groundedness Rubric** | Deterministic Groundedness | **22 Supported, 2 SME Review, 10 Abstentions** | Zero hallucinated citations or fabricated source IDs |
| **Citation Quality** | Whitelist Validity Rate | **100.0% (140/140 valid)** | Zero citations generated outside retrieved evidence chunks |
| | Sentence-Level Attribution | *NOT_EVALUATED* | Task 6 operates on chunk-level provenance, not claim-level markup |
| **GAP Classification** | Taxonomy Accuracy | **23.1% (3/13 correct)** | Identifies missing provisions & unapproved evidence; highlights prompt tuning needs for mock provider |
| **Conflict Detection** | Pair Precision / Recall | **7.3% / 50.0%** | Deterministic detection against 11-pair register; surfaces overlaps when both sources retrieved |
| **Safety & Gating** | Candidate Status Preservation | **True (15/15 records)** | Zero candidate records promoted to approved without governance |
| | Approved-Only Gating | **True (0 chunks, UNAPPROVED)** | Clean abstention when filtering for approved records |
| | Non-Adjudication Integrity | **True (0 violations)** | Zero phrases declaring legal override or declaring a winning regulation |
| | Prompt Injection Resilience | **3/3 Attacks Defended (100%)** | Resists instruction ignore, privilege escalation, and citation fabrication |

### 2. Failure Analysis & Architectural Recommendations
1. **Statutory Provision Precision**: Dense semantic search (`all-MiniLM-L6-v2`) ranks broad conceptual guidance ahead of exact statutory provisions (e.g. Practice Note ranked ahead of Section 1).  
   *Recommendation*: Implement hybrid lexical (BM25) and dense vector retrieval with Reciprocal Rank Fusion (RRF).
2. **Abstention Prompt Optimization**: Mock LLM provider generates generic responses on out-of-scope prompts without explicitly emitting "insufficient evidence" tokens.  
   *Recommendation*: Couple GapHandler classification heuristics directly with system prompts to force standardized abstention phrasing.
3. **External LLM Validation**: Safety testing confirmed architecture-level defenses under `MockLLMProvider`. Production deployment with external models (OpenAI, Ollama) will inherit these deterministic Python guardrails.

---

---

## Task 11: FastAPI Backend Integration

The backend integration layer (`api/`) exposes the existing source-grounded RAG pipeline (Tasks 4–9) through a production-grade, typed FastAPI REST API without duplicating retrieval, vector storage, generation, citation, or conflict logic.

> *"Task 11 is strictly an integration and exposure layer. It connects Vishal's backend and Harshini's frontend directly to the unified StructuredAIResponse contract while enforcing regulatory metadata immutability."*

### 1. API Architecture & Request Flow

```text
Frontend (Harshini) / External Clients
                  │
                  ▼ HTTP / JSON
          FastAPI Backend (Vishal)
        ├── GET  /health
        ├── GET  /api/v1/health
        ├── GET  /docs & /redoc (Swagger/OpenAPI)
        └── POST /api/v1/query
                  │
                  ▼ Dependency Injection (Reusable Singleton)
         GroundedGenerator
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
Retrieval    GAP Handler   Conflict Detector
(Task 4)      (Task 7)         (Task 8)
    │             │             │
    ▼             └──────┬──────┘
Generator (Task 5)       │
    │                    │
    ▼                    │
Citations (Task 6)       │
    │                    │
    └─────────────┬──────┘
                  ▼
      StructuredResponseBuilder (Task 9)
                  │
                  ▼
         StructuredAIResponse
                  │
                  ▼ HTTP 200 JSON
Frontend (Harshini) / External Clients
```

### 2. Available Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Root Service Health | Returns high-level service status, RAG pipeline readiness, and vector store connectivity without leaking internal paths. |
| `GET` | `/api/v1/health` | Versioned Health Check | Health endpoint for API v1 consumers and load balancer monitoring. |
| `POST` | `/api/v1/query` | Regulatory Query | Executes the full RAG pipeline and returns the unified `StructuredAIResponse` schema. |
| `GET` | `/docs` | Swagger UI | Interactive API documentation and schema exploration. |
| `GET` | `/redoc` | ReDoc UI | Comprehensive API reference documentation. |

### 3. Example Request & Response

#### Request
`POST http://127.0.0.1:8000/api/v1/query`
```json
{
  "query": "What procedures should commercial organisations implement to prevent bribery?"
}
```

#### Response (HTTP 200)
```json
{
  "request_id": "REQ-d432a95d-e871-421b-b641-d4e3cde3b80a",
  "query": "What procedures should commercial organisations implement to prevent bribery?",
  "status": "GROUNDED",
  "answer": "Based on Ministry of Justice Guidance (Six Principles) and FCA Financial Crime Guide (FCG 6), commercial organisations should put in place proportionate bribery prevention procedures informed by six principles: proportionality, top-level commitment, risk assessment, due diligence, communication/training, and monitoring/review...",
  "grounded": true,
  "gap": null,
  "citations": [
    {
      "citation_id": "CIT-RR-UK-02-C01",
      "chunk_id": "RR-UK-02-C01",
      "record_id": "RR-UK-02",
      "source_id": "UK-02",
      "regulation": "Bribery Act 2010 – Guidance to help commercial organisations prevent bribery",
      "section_article": "Six Principles",
      "title": "Bribery prevention procedures",
      "formatted_citation": "[RR-UK-02-C01 | RR-UK-02 | Bribery Act 2010 – Guidance to help commercial organisations prevent bribery | Six Principles]"
    }
  ],
  "provenance": [ ... ],
  "conflicts": [ ... ],
  "retrieved_evidence": [ ... ],
  "metadata": {
    "retrieved_count": 5,
    "approved_evidence_count": 0,
    "citation_count": 5,
    "conflict_count": 2,
    "has_gap": false,
    "response_version": "1.0"
  }
}
```

### 4. Regulatory Safety & Gating Guarantees
- **Approval Flag Immutability**: Clients cannot alter `is_approved_for_rag` or `validation_status`. The `QueryRequest` model enforces `extra='forbid'`, returning HTTP 422 if client-side approval tampering is attempted.
- **Normal Evidence Gaps Return HTTP 200**: Requests encountering evidence gaps (`OUT_OF_SCOPE`, `INSUFFICIENT_EVIDENCE`, `UNAPPROVED_EVIDENCE`) return HTTP 200 with the corresponding `ResponseStatus` enum. HTTP error codes are reserved exclusively for request malformation (422) or server execution failures (500).
- **Leak-Free Error Handling**: Server exceptions return safe HTTP 500 responses with generic error details. Internal filesystem paths, database connection strings, and Python tracebacks are never exposed to the client.
- **Configurable CORS**: CORS headers are configured via `settings.cors_origins` to enable secure development with Harshini's frontend on `http://localhost:3000`.

---

## Directory Tree

```text
abc-shield-ai/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── analysis/
│   ├── __init__.py
│   ├── conflict/
│   │   └── __init__.py
│   └── gap/
│       └── __init__.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── query.py
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       └── query.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── evaluation/
│   │   ├── evaluation_cases.json
│   │   └── results/
│   │       ├── evaluation_results.json
│   │       └── evaluation_summary.md
│   ├── processed/
│   │   ├── .gitkeep
│   │   ├── chroma_db/
│   │   │   └── chroma.sqlite3
│   │   ├── normalized_regulatory_records.json
│   │   └── regulatory_chunks.json
│   └── raw/
│       ├── .gitkeep
│       ├── ABC shield_Data Dictionary.xlsx
│       ├── ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx
│       └── ABC_Shield_Source_Register (1).xlsx
├── evaluation/
│   └── __init__.py
├── rag/
│   ├── __init__.py
│   ├── conflict/
│   │   ├── __init__.py
│   │   └── conflict_detector.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── evaluation_dataset.py
│   │   ├── evaluation_models.py
│   │   ├── evaluation_runner.py
│   │   ├── generation_evaluator.py
│   │   ├── retrieval_evaluator.py
│   │   └── safety_evaluator.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── citations.py
│   │   ├── gap_handler.py
│   │   ├── grounded_generator.py
│   │   ├── llm_interface.py
│   │   └── prompts.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── excel_loader.py
│   │   ├── normalizer.py
│   │   ├── schemas.py
│   │   └── validator.py
│   ├── output/
│   │   ├── __init__.py
│   │   ├── response_builder.py
│   │   └── structured_response.py
│   ├── pipeline/
│   │   └── __init__.py
│   └── retrieval/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── vector_store.py
├── scripts/
│   ├── demo_conflicts.py
│   ├── demo_generation.py
│   ├── demo_retrieval.py
│   ├── demo_structured_output.py
│   └── run_evaluation.py
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_citations.py
    ├── test_conflict_detector.py
    ├── test_evaluation.py
    ├── test_gap_handler.py
    ├── test_generation.py
    ├── test_ingestion.py
    ├── test_retrieval.py
    └── test_structured_output.py
```

---

## Execution & Testing

### Start the FastAPI Server (Port 8001):
```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8001
```
*Note: The AI/RAG service runs on port `8001` by default to avoid conflict with the main backend service running on port `8000`.*

Interactive documentation is available at:
- Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc UI: `http://127.0.0.1:8001/redoc`

### Primary Verification Suites:
```bash
# 1. Source-Control Approval & Fail-Closed Guardrails (25 tests)
pytest tests/test_source_control_approval.py -v

# 2. Fast-Track Step 6 Integration Smoke Tests (8 tests)
pytest tests/test_fast_track_step6_smoke.py -v

# 3. Fast-Track Step 4 Canonical RAG Acceptance Tests (15 tests)
pytest tests/test_fast_track_step4_acceptance.py -v
```

### Run Full Regression Suite (810 tests across all milestones):
```bash
pytest -q
```

