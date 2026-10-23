# ABC SHIELD / FINREGTECH SHIPYARD — FINAL RAG INTEGRATION HANDOVER GUIDE

**Document:** AI/RAG Integration Handover Package  
**Author:** Padma Kumar — AI/RAG & Conflict Detection Engineer  
**Recipients:** Vishal (Backend Lead), Harshini (Frontend Lead), Mohan Sir / Compliance Team (Governance)  
**Date:** 2026-10-23  
**Corpus Version:** Canonical 25-Record Regulatory Corpus (`20261021`)  
**Active Knowledge Base Mode:** `canonical`  
**Active Database Directory:** `data/staging/madhesh_handover/step6/chroma_db` (`canonical_regulatory_records`, 25 vectors)  
**Legacy Store:** `data/processed/chroma_db` (`regulatory_records`, 15 vectors — strictly intact & untouched)  
**Integration Status:** **READY FOR HANDOVER** (Provisional RAG Integration Active; Final Legal Validation Gated under `DEC-01`)  

---

## 1. Executive Summary & Governance Baseline

This guide provides the complete, authoritative technical integration contract for connecting Vishal's backend and Harshini's frontend to the source-grounded ABC Shield RAG intelligence engine.

### Governance & Approval Invariant (DEC-01 & RAG-014)
- **Approved for RAG Integration:** The canonical 25-record corpus has been approved by the programme lead for RAG extraction, integration, and evaluation testing.
- **Pending Final SME Validation:** Formal legal compliance sign-off remains **OPEN** under Master Handover Tracker decision **`DEC-01`**. No separate written Compliance SME approval artifact has been supplied.
- **Fail-Closed Safeguard:** All 25 canonical records carry `validation_status = "Approved for RAG Integration - Pending SME Validation"` and `is_approved_for_rag = False`.
  - Queries with `filter_approved_only=False` (default development/research mode) retrieve evidence, generate grounded answers, attach full official citations, and disclose candidate status (`has_candidate_evidence = True`).
  - Queries with `filter_approved_only=True` (strict compliance mode) fail closed with HTTP 200, returning `status = "UNAPPROVED_EVIDENCE"`, 0 citations, 0 candidate evidence chunks, and `requires_human_review = True`.
- **Strict Non-Adjudication:** The advice comparison endpoint (`/api/v1/compare`) identifies factual differences and co-retrieves regulatory evidence, but strictly preserves **`decision = None`** and attaches a mandatory legal disclaimer.

---

## 2. Environment Setup, Dependencies & Service Startup

### 2.1 Python Environment & Dependencies
The service runs on Python 3.12+ (tested on Windows Server / PowerShell with Python 3.12.10).

From the project root (`abc-shield-ai/`):
```powershell
# 1. Create or activate virtual environment
& "..\.venv\Scripts\Activate.ps1"

# 2. Install dependencies
pip install -r requirements.txt
```

#### Core Dependencies ([`requirements.txt`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/requirements.txt)):
- `fastapi>=0.111.0` & `uvicorn>=0.30.0` (REST API layer)
- `pydantic>=2.7.0` & `pydantic-settings>=2.2.0` (Data models & settings)
- `chromadb>=0.5.0` (Vector storage & querying)
- `sentence-transformers>=3.0.0` (Dense neural embeddings: `all-MiniLM-L6-v2`)
- `openai>=1.30.0` (Pluggable LLM interface with MockLLMProvider default)
- `pytest>=8.2.0` & `httpx>=0.27.0` (Automated testing & test clients)

### 2.2 Active Configuration ([`config/settings.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/config/settings.py))
The service defaults out-of-the-box to the canonical 25-record knowledge base:
```python
rag_knowledge_base_mode: str = "canonical"
canonical_chroma_persist_dir: Path = Path("data/staging/madhesh_handover/step6/chroma_db")
canonical_chroma_collection_name: str = "canonical_regulatory_records"
legacy_chroma_persist_dir: Path = Path("data/processed/chroma_db")
legacy_chroma_collection_name: str = "regulatory_records"
chroma_persist_dir: Path = Path("data/staging/madhesh_handover/step6/chroma_db")
chroma_collection_name: str = "canonical_regulatory_records"
embedding_model_name: str = "all-MiniLM-L6-v2"
api_host: str = "127.0.0.1"
api_port: int = 8000
cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
query_max_length: int = 2000
```

### 2.3 Service Startup Command
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Expected Startup Log Output:
```text
INFO:     Started server process [7784]
INFO:     Waiting for application startup.
INFO:     Initializing shared GroundedGenerator and RAG components...
INFO:     Loading embedding model 'all-MiniLM-L6-v2' on CPU...
INFO:     Shared GroundedGenerator initialized successfully with collection 'canonical_regulatory_records' at 'data\staging\madhesh_handover\step6\chroma_db'.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 3. API Endpoints & Request/Response Contracts

### Endpoint Summary Table

| Method | Endpoint | Consumer | Primary Schema | Status Code Policy |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health`<br>`/health` | Backend / Frontend / LB | `HealthResponse` | 200 (connected), 200 degraded (disconnected) |
| `POST` | `/api/v1/query` | Backend (Vishal) / UI (Harshini) | In: `QueryRequest`<br>Out: `StructuredAIResponse` | 200 (all lifecycle states: GROUNDED, GAPs), 422 (validation), 500 (internal) |
| `POST` | `/api/v1/compare` | Backend (Vishal) / UI (Harshini) | In: `AdviceComparisonRequest`<br>Out: `AdviceComparisonResult` | 200 (differences/conflicts), 422 (validation), 500 (internal) |
| `GET` | `/docs` / `/redoc` | Developers | OpenAPI / Swagger UI | 200 |

---

### 3.1 Endpoint 1: Health Check (`GET /api/v1/health`)

#### Request:
```http
GET /api/v1/health HTTP/1.1
Host: 127.0.0.1:8000
Accept: application/json
```

#### Real Live Response (HTTP 200):
```json
{
  "status": "ok",
  "app_name": "ABC Shield FinRegTech API",
  "version": "1.0.0",
  "rag_pipeline_initialized": true,
  "chromadb_status": "connected",
  "environment": "development"
}
```
*Note:* Leak-free; reveals zero internal filesystem paths or secret connection strings.

---

### 3.2 Endpoint 2: Regulatory Query (`POST /api/v1/query`)

#### Request Schema (`QueryRequest`):
```json
{
  "query": "string (1-2000 chars, required)",
  "id": "string (optional client correlation ID)",
  "project_id": "string (optional tenant/project filter)",
  "requirement_ids": ["string (optional requirement IDs)"],
  "advisor_advice_ids": ["string (optional advice IDs)"],
  "context": {
    "jurisdiction": "UK | EU (optional filter)",
    "filter_approved_only": "boolean (optional, default false)",
    "regulatory_area": "string (optional area hint)"
  }
}
```
*Security Invariant:* `extra="forbid"`. Any client attempt to inject unauthorized metadata returns HTTP 422.

---

### 3.3 Real Live JSON Examples for `POST /api/v1/query`

#### Example A: GROUNDED Response (UK Bribery Act Section 7)
*Request:*
```json
{
  "query": "Under UK Bribery Act 2010, what does Section 7 cover regarding failure of commercial organisations to prevent bribery?",
  "context": {
    "jurisdiction": "UK"
  }
}
```
*Real Response (HTTP 200):*
```json
{
  "request_id": "REQ-f598c9ad-bc34-4eb4-b255-3de155a8c7e0",
  "query": "Under UK Bribery Act 2010, what does Section 7 cover regarding failure of commercial organisations to prevent bribery?",
  "status": "GROUNDED",
  "answer": "Under the Bribery Act 2010 (Section 7), Source: UK-01 - Bribery Act 2010\nReference: Section 7\nTopic: Failure of commercial organisations to prevent bribery\nRequirement: A relevant commercial organisation can commit an offence when an associated person bribes another person intending to obtain or retain business or a business advantage for the organisation.\nNotes: Programme-approved for extraction; final legal applicability remains subject to authorised Compliance SME validation. (Chunk ID: UK-01-R004-C01, Source ID: UK-01). Section 8 defines an 'associated person' as a person who performs services for or on behalf of the commercial organisation (Chunk ID: UK-01-R005-C01, Source ID: UK-01).",
  "grounded": true,
  "gap": null,
  "citations": [
    {
      "citation_id": "CIT-UK-01-R004-C01",
      "chunk_id": "UK-01-R004-C01",
      "record_id": "UK-01-R004",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "regulator": "UK Parliament / legislation.gov.uk",
      "jurisdiction": "UK",
      "section_article": "Section 7",
      "title": "Failure of commercial organisations to prevent bribery",
      "topic": "Failure of commercial organisations to prevent bribery",
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/section/7",
      "version_date": "Latest available revised text",
      "effective_date": "8 April 2010",
      "validation_status": "Approved for RAG Integration - Pending SME Validation",
      "validation_date": "20 October 2026",
      "is_approved_for_rag": false,
      "text_type": "retrieval_text",
      "formatted_citation": "[UK-01-R004-C01 | UK-01-R004 | Bribery Act 2010 | Section 7]"
    }
  ],
  "provenance": [
    {
      "provenance_id": "PROV-UK-01-R004-C01",
      "chunk_id": "UK-01-R004-C01",
      "record_id": "UK-01-R004",
      "source_id": "UK-01",
      "source_file": "ABC_Shield_Canonical_25_Record_Corpus.xlsx",
      "worksheet": "Regulatory_Records",
      "row_number": 5,
      "source_text_hash": "4392fae2e8f1caec0db85f67e4dd3bc7efd75ff3eb6aeb482a0d1e57c8bfbc4c",
      "source_url": "https://www.legislation.gov.uk/ukpga/2010/23/section/7",
      "validation_status": "Approved for RAG Integration - Pending SME Validation",
      "is_approved_for_rag": false
    }
  ],
  "conflicts": [],
  "retrieved_evidence": [
    {
      "chunk_id": "UK-01-R004-C01",
      "record_id": "UK-01-R004",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "section_article": "Section 7",
      "title": "Failure of commercial organisations to prevent bribery",
      "text": "Source: UK-01 - Bribery Act 2010\nReference: Section 7\nTopic: Failure of commercial organisations to prevent bribery\nRequirement: A relevant commercial organisation is guilty of an offence if an associated person bribes another person intending to obtain or retain business or a business advantage.\nNotes: Exact wording verified against legislation.gov.uk Section 7.",
      "similarity_score": 0.8142,
      "similarity": 0.8142,
      "distance": 0.1858,
      "validation_status": "Approved for RAG Integration - Pending SME Validation",
      "is_approved_for_rag": false,
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/section/7",
      "version_date": "Latest available revised text",
      "effective_date": "8 April 2010"
    }
  ],
  "metadata": {
    "retrieved_count": 5,
    "approved_evidence_count": 0,
    "citation_count": 5,
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

#### Example B: UNAPPROVED_EVIDENCE Response (`filter_approved_only=True`)
*Request:*
```json
{
  "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
  "context": {
    "filter_approved_only": true
  }
}
```
*Real Response (HTTP 200):*
```json
{
  "request_id": "REQ-0683ebce-0e42-4eb4-b6ef-14ce34927160",
  "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
  "status": "UNAPPROVED_EVIDENCE",
  "answer": "The available regulatory evidence is insufficient to answer this question. No matching regulatory records were found in the approved knowledge base. (Note: Matching candidate evidence exists in the repository with status 'Approved for RAG Integration - Pending SME Validation', but cannot be used because approved_only filter was requested. Compliance SME approval is required before this content can be cited as approved).",
  "grounded": false,
  "gap": {
    "is_gap": true,
    "gap_type": "UNAPPROVED_EVIDENCE",
    "message": "Matching regulatory evidence was found, but all retrieved records are Candidate records awaiting Compliance SME validation.",
    "user_safe_message": "Retrieved regulatory evidence has candidate status ('Approved for RAG Integration - Pending SME Validation') and cannot be used because filter_approved_only is enabled.",
    "retrieved_chunk_ids": [],
    "retrieved_record_ids": [],
    "relevant_evidence_count": 0,
    "approved_evidence_count": 0,
    "has_candidate_evidence": true,
    "requires_human_review": true,
    "coverage_nature": "RETRIEVAL_LIMITATION",
    "recommended_next_action": "Submit unapproved candidate records to the Compliance SME for formal validation."
  },
  "citations": [],
  "provenance": [],
  "conflicts": [],
  "retrieved_evidence": [],
  "metadata": {
    "retrieved_count": 0,
    "approved_evidence_count": 0,
    "citation_count": 0,
    "conflict_count": 0,
    "has_gap": true,
    "gap_type": "UNAPPROVED_EVIDENCE",
    "requires_human_review": true,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

#### Example C: OUT_OF_SCOPE Response (Sanctions Screening)
*Request:*
```json
{
  "query": "What are ABC Shield's sanctions screening obligations under OFAC and UK sanctions regimes?"
}
```
*Real Response (HTTP 200):*
```json
{
  "request_id": "REQ-99c51206-ba9d-4786-81cf-71a25db8e622",
  "query": "What are ABC Shield's sanctions screening obligations under OFAC and UK sanctions regimes?",
  "status": "OUT_OF_SCOPE",
  "answer": "The current ABC Shield scope does not provide sufficient evidence for economic and financial sanctions. (Scope is strictly limited to UK and EU anti-bribery and anti-corruption frameworks, and relevant FCA financial-crime systems and controls).",
  "grounded": false,
  "gap": {
    "is_gap": true,
    "gap_type": "OUT_OF_SCOPE",
    "message": "Query topic matches out-of-scope domain: 'economic and financial sanctions'.",
    "user_safe_message": "The current ABC Shield scope does not provide sufficient evidence for economic and financial sanctions. (Scope is strictly limited to UK and EU anti-bribery and anti-corruption frameworks, and relevant FCA financial-crime systems and controls).",
    "retrieved_chunk_ids": ["UK-03-R005-C01", "EU-01-R001-C01", "EU-01-R007-C01", "EU-01-R004-C01", "UK-03-R001-C01"],
    "retrieved_record_ids": ["UK-03-R005", "EU-01-R001", "EU-01-R007", "EU-01-R004", "UK-03-R001"],
    "relevant_evidence_count": 5,
    "approved_evidence_count": 0,
    "has_candidate_evidence": true,
    "requires_human_review": false,
    "coverage_nature": "CORPUS_COVERAGE_LIMITATION",
    "recommended_next_action": "Refer to an approved knowledge source covering this regulatory domain."
  },
  "citations": [],
  "provenance": [],
  "conflicts": [],
  "retrieved_evidence": [],
  "metadata": {
    "retrieved_count": 5,
    "approved_evidence_count": 0,
    "citation_count": 0,
    "conflict_count": 0,
    "has_gap": true,
    "gap_type": "OUT_OF_SCOPE",
    "requires_human_review": false,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

#### Example D: INSUFFICIENT_EVIDENCE Response (French Transposition)
*Request:*
```json
{
  "query": "What are the specific transposition provisions under French national law for the EU Whistleblower Directive?"
}
```
*Real Response (HTTP 200):*
```json
{
  "request_id": "REQ-6ce04185-9a10-4925-bf92-78e5fb51107c",
  "query": "What are the specific transposition provisions under French national law for the EU Whistleblower Directive?",
  "status": "INSUFFICIENT_EVIDENCE",
  "answer": "The available regulatory evidence is insufficient to answer what exact national law implements the requested provisions in France. The ABC Shield regulatory corpus covers EU-level Directive provisions and UK anti-bribery legislation, but does not contain member-state national transposing laws. National transposition details require specific local legal sources and authorised Compliance SME verification.",
  "grounded": false,
  "gap": {
    "is_gap": true,
    "gap_type": "DATA_COVERAGE_LIMITATION",
    "message": "Query requests national transposing legislation in France, which is outside the canonical ABC Shield corpus.",
    "user_safe_message": "The ABC Shield regulatory corpus covers EU-level Directive provisions and UK legislation, but does not contain national transposing legislation for France. Member-state transposition requires specific national legal sources and Compliance SME verification.",
    "retrieved_chunk_ids": ["EU-01-R001-C01", "EU-01-R007-C01", "EU-01-R003-C01", "EU-01-R006-C01", "EU-01-R002-C01"],
    "retrieved_record_ids": ["EU-01-R001", "EU-01-R007", "EU-01-R003", "EU-01-R006", "EU-01-R002"],
    "relevant_evidence_count": 5,
    "approved_evidence_count": 0,
    "has_candidate_evidence": true,
    "requires_human_review": true,
    "coverage_nature": "CORPUS_COVERAGE_LIMITATION",
    "recommended_next_action": "Obtain and verify the official member-state transposition source for France."
  },
  "citations": [],
  "provenance": [],
  "conflicts": [],
  "retrieved_evidence": [],
  "metadata": {
    "retrieved_count": 5,
    "approved_evidence_count": 0,
    "citation_count": 0,
    "conflict_count": 0,
    "has_gap": true,
    "gap_type": "DATA_COVERAGE_LIMITATION",
    "requires_human_review": true,
    "has_candidate_evidence": true,
    "response_version": "1.0"
  }
}
```

---

### 3.4 Endpoint 3: Advice Comparison (`POST /api/v1/compare`)

#### Request Schema (`AdviceComparisonRequest`):
```json
{
  "comparison_id": "string (optional)",
  "request_id": "string (optional correlation ID)",
  "project_id": "string (optional tenant filter)",
  "requirement_ids": ["string (optional)"],
  "advisor_1": {
    "advice_id": "string (e.g. ADV-001, required)",
    "advice_text": "string (1-4000 chars, required)",
    "advisor_name": "string (optional)",
    "source_reference": "string (optional)"
  },
  "advisor_2": {
    "advice_id": "string (e.g. ADV-002, required)",
    "advice_text": "string (1-4000 chars, required)",
    "advisor_name": "string (optional)",
    "source_reference": "string (optional)"
  },
  "context": {
    "jurisdiction": "UK | EU (optional)",
    "regulatory_area": "string (optional)"
  }
}
```

#### Real Live Response (HTTP 200):
*Request:*
```json
{
  "comparison_id": "CMP-CANONICAL-001",
  "requirement_ids": ["REQ-UK-01"],
  "advisor_1": {
    "advice_id": "ADV-001",
    "advisor_name": "Senior Compliance Counsel",
    "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
    "source_reference": "UK Bribery Act 2010 Section 1"
  },
  "advisor_2": {
    "advice_id": "ADV-002",
    "advisor_name": "External Consultant",
    "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    "source_reference": "MoJ Guidance on Bribery Act 2010"
  },
  "context": {
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption"
  }
}
```
*Real Response (HTTP 200):*
```json
{
  "comparison_id": "CMP-CANONICAL-001",
  "advisor_1": {
    "advice_id": "ADV-001",
    "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
    "advisor_name": "Senior Compliance Counsel",
    "source_reference": "UK Bribery Act 2010 Section 1"
  },
  "advisor_2": {
    "advice_id": "ADV-002",
    "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    "advisor_name": "External Consultant",
    "source_reference": "MoJ Guidance on Bribery Act 2010"
  },
  "differences": [
    {
      "difference_type": "SCOPE_DIFFERENCE",
      "summary": "Scope difference identified: one advisor addresses statutory criminal offences while the other addresses commercial prevention procedures.",
      "advisor_1_position": "Bribery Act 2010 Section 1 offences of bribing another person.",
      "advisor_2_position": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
      "is_contradiction": false
    },
    {
      "difference_type": "AUTHORITY_DIFFERENCE",
      "summary": "Authority difference identified: advisors rely on different tiers of regulatory authority (primary Parliamentary legislation vs executive guidance).",
      "advisor_1_position": "Bribery Act 2010 Section 1 offences of bribing another person.",
      "advisor_2_position": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
      "is_contradiction": false
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
      "requirement_comparison": "Act creates legal offences; guidance explains procedures organisations can use to prevent bribery and describes six core principles.",
      "scope_difference": "Law applies to relevant offences/organisations; guidance is explanatory and procedural.",
      "authority_difference": "Parliamentary legislation vs Ministry of Justice guidance.",
      "version_effective_date_difference": "Act: 2010; guidance published 2012 and updated 22 Jan 2025.",
      "conflict_status": "No direct conflict identified",
      "rag_use": "Retrieve binding Act requirement first; use guidance as implementation context.",
      "retrieved_source_ids": ["UK-01", "UK-02"],
      "retrieved_chunk_ids": [
        "UK-01-R001-C01",
        "UK-01-R006-C01",
        "UK-02-R001-C01",
        "UK-02-R006-C01",
        "UK-02-R003-C01"
      ],
      "both_sources_retrieved": true,
      "source_1_validation_status": "Approved for RAG Integration - Pending SME Validation",
      "source_2_validation_status": "Approved for RAG Integration - Pending SME Validation",
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
  "supporting_evidence": [
    {
      "advice_id": "ADV-001",
      "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
      "supporting_chunk_ids": [
        "UK-01-R001-C01",
        "UK-01-R006-C01",
        "UK-02-R001-C01",
        "UK-02-R006-C01",
        "UK-02-R003-C01"
      ],
      "supporting_source_ids": ["UK-01", "UK-02"],
      "evidence_status": "CONFIRMED_SUPPORT",
      "notes": "Advice text is grounded in co-retrieved regulatory sources UK-01 and UK-02."
    }
  ],
  "citations": [
    {
      "citation_id": "CIT-UK-01-R001-C01",
      "chunk_id": "UK-01-R001-C01",
      "record_id": "UK-01-R001",
      "source_id": "UK-01",
      "regulation": "Bribery Act 2010",
      "regulator": "UK Parliament / legislation.gov.uk",
      "jurisdiction": "UK",
      "section_article": "Section 1",
      "title": "Bribing another person",
      "topic": "Bribing another person",
      "official_source": "https://www.legislation.gov.uk/ukpga/2010/23/section/1",
      "version_date": "Latest available revised text",
      "effective_date": "8 April 2010",
      "validation_status": "Approved for RAG Integration - Pending SME Validation",
      "validation_date": "20 October 2026",
      "is_approved_for_rag": false,
      "text_type": "retrieval_text",
      "formatted_citation": "[UK-01-R001-C01 | UK-01-R001 | Bribery Act 2010 | Section 1]"
    }
  ],
  "provenance": [
    {
      "provenance_id": "PROV-UK-01-R001-C01",
      "chunk_id": "UK-01-R001-C01",
      "record_id": "UK-01-R001",
      "source_id": "UK-01",
      "source_file": "ABC_Shield_Canonical_25_Record_Corpus.xlsx",
      "worksheet": "Regulatory_Records",
      "row_number": 2,
      "source_text_hash": "2f406ec040f936173ea58ff453ad2594411139e80e463a56cf91d17d12a64010",
      "source_url": "https://www.legislation.gov.uk/ukpga/2010/23/section/1",
      "validation_status": "Approved for RAG Integration - Pending SME Validation",
      "is_approved_for_rag": false
    }
  ],
  "evidence_gaps": [],
  "human_review_required": true,
  "decision": null,
  "disclaimer": "This comparison provides source-grounded regulatory analysis and factual difference identification. It does not constitute formal legal or professional advice. It does NOT determine which advisor is legally or professionally correct. Final legal determinations and compliance disposition remain the exclusive responsibility of a qualified compliance professional.",
  "traceability": {
    "comparison_id": "CMP-CANONICAL-001",
    "request_id": "CMP-CANONICAL-001",
    "project_id": null,
    "requirement_ids": ["REQ-UK-01"],
    "advisor_1_id": "ADV-001",
    "advisor_2_id": "ADV-002",
    "jurisdiction": "UK",
    "regulatory_area": "Anti-Bribery and Corruption",
    "timestamp": "2026-10-23T10:22:24.801676+00:00"
  }
}
```

---

## 4. Consumer Requirements Breakdown

### 4.1 What Vishal Needs (Backend Integration)

Vishal can connect to the RAG module in either of two modes:
1. **Direct HTTP Microservice (Recommended):** Run the FastAPI service on `http://127.0.0.1:8000` and proxy calls from the backend gateway to `/api/v1/query` and `/api/v1/compare`.
2. **In-Process Python Package:** Mount `api.routes.query.router` and `api.routes.compare.router` directly into Vishal's FastAPI app using `app.include_router()`.

#### Exact Python Modules Vishal Requires:
- [`api/main.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/main.py): Application entrypoint & CORS configuration.
- [`api/dependencies.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/dependencies.py): Shared singletons (`get_configured_vector_store()`, `get_grounded_generator()`, `get_advice_comparator()`).
- [`api/routes/`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/routes/): `health.py`, `query.py`, `compare.py`.
- [`api/models/`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/api/models/): `health.py`, `query.py`.
- [`rag/`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/rag/):
  - `retrieval/`: `retriever.py`, `vector_store.py`, `embeddings.py`.
  - `generation/`: `grounded_generator.py`, `gap_handler.py`, `citations.py`, `llm_interface.py`.
  - `conflict/`: `conflict_detector.py` (CO-001 through CO-011 definitions).
  - `output/`: `structured_response.py`, `response_builder.py`.
  - `pipeline/`: `advice_comparator.py`, `advice_adapter.py`.
- [`config/settings.py`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/config/settings.py): Application environment settings.
- [`data/staging/madhesh_handover/step6/chroma_db/`](file:///d:/FInregTech%20Shipyard/abc-shield-ai/data/staging/madhesh_handover/step6/chroma_db/): Staged canonical vector database (25 vectors).

---

### 4.2 What Harshini Needs (Frontend Integration)

Harshini's UI interacts exclusively via JSON over HTTP.

#### CORS Settings:
- The API is pre-configured to accept requests from `http://localhost:3000` and `http://127.0.0.1:3000`.

#### Key UI Fields to Render from `StructuredAIResponse`:
- **Answer Banner & Text:** `response.answer`
- **Response Status Badge:** `response.status` (`GROUNDED` = green badge; `UNAPPROVED_EVIDENCE` = yellow warning; `OUT_OF_SCOPE` / `INSUFFICIENT_EVIDENCE` = info banner; `ERROR` = red).
- **Candidate Notice:** If `response.metadata.has_candidate_evidence === true`, render:
  > *"Notice: Evidence contains candidate records awaiting formal Compliance SME validation."*
- **Clickable Citations List (`response.citations`):**
  - Title & Reference: `${cit.regulation} — ${cit.section_article}: ${cit.title}`
  - Verified URL: Link `cit.official_source` (opens official `legislation.gov.uk` or `eur-lex.europa.eu` in new tab).
  - Pinpoint Citation Label: `cit.formatted_citation`
  - Approval Status Badge: `cit.validation_status`
- **Audit Provenance Modal / Accordion (`response.provenance`):**
  - Source File: `prov.source_file` (Worksheet: `prov.worksheet`, Row: `prov.row_number`)
  - Cryptographic Hash: `prov.source_text_hash` (SHA-256 integrity verification)
- **Conflict / Overlap Findings (`response.conflicts`):**
  - Relationship ID: `conf.conflict_id` (e.g. `CO-001`)
  - Sources: `${conf.source_1} vs ${conf.source_2}`
  - Relationship Type: `conf.relationship` (e.g. `Overlap - complementary`)
  - Guidance Note: `conf.rag_use`
- **Advice Comparison View (`AdviceComparisonResult`):**
  - Side-by-side view of `advisor_1` and `advisor_2`.
  - Discrepancy highlights from `differences` array (with `is_contradiction` flag).
  - Supporting citations per advisor from `supporting_evidence`.
  - Final Decision: Display *"Pending Human SME Review"* (always reflects `decision === null`).
  - Mandatory Disclaimer: Render `disclaimer` text verbatim.

---

## 5. Automated Verification & Test Evidence

### Recorded Regression Suite Results

| Test Suite | File | Count | Execution Time | Result |
| :--- | :--- | :---: | :---: | :---: |
| **Fast-Track Step 2 KB** | `tests/test_fast_track_step2_knowledge_base.py` | 12 | ~1.5s | **12 / 12 PASS (100%)** |
| **Fast-Track Step 3 API** | `tests/test_fast_track_step3_api_retrieval.py` | 9 | ~1.8s | **9 / 9 PASS (100%)** |
| **Fast-Track Step 4 Acceptance** | `tests/test_fast_track_step4_acceptance.py` | 15 | ~2.5s | **15 / 15 PASS (100%)** |
| **Fast-Track Step 6 Smoke** | `tests/test_fast_track_step6_smoke.py` | 8 | ~1.2s | **8 / 8 PASS (100%)** |
| **Combined Fast-Track Suite** | All 4 fast-track test files | **44** | **10.19s** | **44 / 44 PASS (100%)** |

### How to Run Tests
```powershell
# Run the complete fast-track regression suite
& "..\.venv\Scripts\python.exe" -m pytest tests/test_fast_track_step2_knowledge_base.py tests/test_fast_track_step3_api_retrieval.py tests/test_fast_track_step4_acceptance.py tests/test_fast_track_step6_smoke.py -v

# Run the live integration smoke test runner
& "..\.venv\Scripts\python.exe" scripts/run_integration_smoke_tests.py
```

---

## 6. Troubleshooting & Operational Guidance

### 1. Vector Store Missing Error (`FileNotFoundError`)
- **Symptom:** API returns HTTP 500; logs show `Canonical ChromaDB persist directory ... does not exist`.
- **Cause:** `data/staging/madhesh_handover/step6/chroma_db` is missing or relative path is incorrect.
- **Fix:** Ensure current working directory is `abc-shield-ai/` or set absolute path in `.env`:
  ```ini
  CANONICAL_CHROMA_PERSIST_DIR="D:/FInregTech Shipyard/abc-shield-ai/data/staging/madhesh_handover/step6/chroma_db"
  ```

### 2. HTTP 422 Unprocessable Entity
- **Symptom:** Query returns HTTP 422.
- **Cause:** Request payload includes unauthorized fields (e.g. attempting to inject `is_approved_for_rag` from the client) or query is empty.
- **Fix:** Remove unauthorized fields from client JSON. Schema strictly enforces `extra='forbid'`.

### 3. Unexpected `UNAPPROVED_EVIDENCE` Status
- **Symptom:** Query returns HTTP 200 with `status="UNAPPROVED_EVIDENCE"` and 0 citations.
- **Cause:** Client passed `"filter_approved_only": true` in `context`.
- **Fix:** All 25 canonical records are provisional pending SME sign-off (`DEC-01`). For research and prototype testing, omit `filter_approved_only` or set it to `false`.

### 4. Port 8000 Already in Use
- **Symptom:** `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`.
- **Fix:** Run on alternative port or kill existing process:
  ```powershell
  python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
  ```

---

## 7. Handover File-by-File Manifest

| Relative Path | Size / Lines | Purpose & Role in Handover | Recipient |
| :--- | :---: | :--- | :--- |
| **`api/main.py`** | 73 lines | FastAPI application entrypoint, CORS, exception handling | Vishal |
| **`api/dependencies.py`** | 118 lines | Singleton wiring for retriever, generator, comparator | Vishal |
| **`api/routes/health.py`** | 34 lines | Health endpoints (`/health`, `/api/v1/health`) | Vishal / Harshini |
| **`api/routes/query.py`** | 96 lines | RAG query endpoint (`/api/v1/query`) | Vishal / Harshini |
| **`api/routes/compare.py`** | 52 lines | Advice comparison endpoint (`/api/v1/compare`) | Vishal / Harshini |
| **`api/models/health.py`** | 18 lines | Health response schema | Vishal / Harshini |
| **`api/models/query.py`** | 74 lines | Query request schema with `extra='forbid'` | Vishal / Harshini |
| **`rag/output/structured_response.py`** | 106 lines | Pydantic model for `StructuredAIResponse` | Vishal / Harshini |
| **`rag/generation/citations.py`** | 224 lines | Deterministic Citation & Provenance builders | Vishal |
| **`rag/generation/gap_handler.py`** | 461 lines | Deterministic Gap & Abstention classification | Vishal |
| **`rag/conflict/conflict_detector.py`** | 258 lines | CO-001 through CO-011 conflict overlap detector | Vishal |
| **`rag/pipeline/advice_comparator.py`** | 633 lines | Non-adjudicative advisor comparison engine | Vishal |
| **`rag/retrieval/retriever.py`** | 268 lines | Regulatory retriever with provision re-ranking | Vishal |
| **`rag/retrieval/vector_store.py`** | 231 lines | ChromaDB interface wrapper | Vishal |
| **`rag/retrieval/embeddings.py`** | 82 lines | Process-level cached `all-MiniLM-L6-v2` manager | Vishal |
| **`config/settings.py`** | 63 lines | Pydantic application settings | Vishal |
| **`requirements.txt`** | 27 lines | Python library dependencies | Vishal |
| **`data/staging/madhesh_handover/step6/chroma_db/`** | 25 vectors | Staged ChromaDB canonical vector store | Vishal (Backend only) |
| **`data/evaluation/ABC_SHIELD_RAG_HANDOVER_GUIDE.md`** | Complete | This integration handover guide | Vishal & Harshini |

### Items Explicitly Excluded from Handover:
- **`.venv/`**: Local Python virtual environment (must not be committed to Git).
- **Secrets / `.env`**: Environment configuration templates provided via `.env.example`.
- **`data/raw/*.xlsx`**: Historical Excel workbooks remain archived in data repository.
- **`data/processed/chroma_db/`**: Legacy 15-vector DB remains isolated.
- **ChromaDB binaries in frontend**: Harshini's repository must not contain ChromaDB files.

---

## 8. Recommended Git Branch & Pull Request Workflow

Because the local workspace currently operates directly on local filesystem paths without an initialized `.git` working tree, the team should execute the following branching workflow upon repository synchronization:

```
feature/padma-rag-fast-track (Current work: Step 1-6 complete)
              │
              ├── Pull Request: "ABC Shield Fast-Track Canonical RAG Integration"
              │   - Reviewers: Vishal (Backend), Harshini (Frontend), Mohan (Governance)
              │   - CI Checks: Fast-Track Suite (44/44 passing)
              ▼
    integration / develop (Unified Shipyard staging branch)
              │
              ├── Vishal backend connects to /api/v1/query & /api/v1/compare
              ├── Harshini frontend connects to http://localhost:8000
              │
              ▼
             main (Production release branch — gated on DEC-01 SME validation)
```

1. **Feature Branch:** Maintain current work on `feature/padma-rag-fast-track`.
2. **Pull Request Target:** Open PR against `develop` or `integration`.
3. **Reviewers:**
   - **Vishal:** Verify dependency injection and endpoint invocation via backend services.
   - **Harshini:** Verify field bindings (`status`, `answer`, `citations`, `provenance`, `differences`).
   - **Mohan Sir:** Review open decision `DEC-01` for formal legal SME sign-off.
4. **Authoritative Promotion:** Merge to `main` and set `is_approved_for_rag = True` only after `DEC-01` is closed with signed compliance documentation.
