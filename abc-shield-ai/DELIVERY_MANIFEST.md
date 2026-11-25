# ABC SHIELD AI/RAG MODULE – DELIVERY MANIFEST

**Project:** FINREGTECH SHIPYARD – ABC Shield
**Module:** AI/RAG Microservice & Regulatory Intelligence Engine
**Module Lead:** Padma Kumar
**Delivery Date:** November 25, 2026
**Archive:** `ABC_Shield_AI_RAG_Delivery.zip`
**Git Branch:** `ai-rag`

---

## 1. Included Files and Folders

The deliverable includes all necessary source code, configuration templates, documentation, canonical vector databases, and automated test suites for the AI/RAG module:

```
abc-shield-ai/
├── api/                                <-- FastAPI service layer (Port 8001)
│   ├── dependencies.py                 <-- Vector count threshold & singleton dependencies
│   ├── main.py                         <-- Application entrypoint & lifespan startup warm-up
│   ├── models/
│   │   ├── health.py                   <-- Health response model
│   │   └── query.py                    <-- QueryRequest (with Builder aliases prompt/text)
│   └── routes/
│       ├── compare.py                  <-- Dual-format comparison & Gateway route /projects/{projectId}/compare-advice
│       ├── health.py                   <-- /health & /api/v1/health endpoints
│       └── query.py                    <-- /api/v1/query, /api/v1/rag/analyze, /api/v1/analyze endpoints
├── config/                             <-- Configuration layer
│   └── settings.py                     <-- Pydantic BaseSettings, 8 CORS origins, Port 8001
├── data/                               <-- Controlled regulatory data & canonical vector store
│   ├── raw/                            <-- Controlled raw Excel workbooks (25-record corpus, source registers)
│   ├── staging/madhesh_handover/step6/chroma_db/ <-- Canonical ChromaDB store (25 records)
│   └── evaluation/                     <-- Historical evaluation reports & handover guides
├── rag/                                <-- Core RAG intelligence engine
│   ├── conflict/                       <-- Conflict detector with CO-001..CO-011 registered rules
│   ├── generation/                     <-- GroundedGenerator, CitationBuilder, GapHandler
│   ├── ingestion/                      <-- Excel loaders, normalizers, validators, chunkers
│   ├── output/                         <-- StructuredAIResponse and response builders
│   ├── pipeline/                       <-- AdviceComparator and AdviceRAGAdapter
│   ├── retrieval/                      <-- RegulatoryRetriever, VectorStore, EmbeddingManager
│   └── security/                       <-- Runtime security policy & prompt-injection defense
├── scripts/                            <-- Utility & seeding scripts
│   └── seed_canonical_vectors.py       <-- Idempotent ChromaDB seeder
├── tests/                              <-- Complete automated test suite (887 tests, 100% pass)
│   ├── test_builder_integration.py     <-- Builder integration & /api/v1/rag/analyze tests
│   ├── test_second_integration_audit.py<-- 8 CORS origins & Format B 409 tests
│   ├── test_audit_corrections_vishal.py<-- Extra-field & vector threshold tests
│   └── ...                             <-- Baseline unit, security, and integration tests
├── .env.example                        <-- Safe configuration template (no secrets)
├── .gitignore                          <-- Standard python exclusions
├── pytest.ini                          <-- Pytest configuration
├── README.md                           <-- Comprehensive system documentation & setup guide
└── requirements.txt                    <-- Complete dependency manifest
```

---

## 2. Modified & Newly Created Files

### Newly Created Files:
- `abc-shield-ai/tests/test_builder_integration.py` – Test suite covering `POST /api/v1/rag/analyze`, Builder aliases (`prompt`/`text`), and Gateway route `/projects/{projectId}/compare-advice`.
- `abc-shield-ai/tests/test_second_integration_audit.py` – Test suite covering 8 CORS origins, Format B 409 Conflict, and tenant isolation.
- `abc-shield-ai/tests/test_audit_corrections_vishal.py` – Test suite covering first audit corrections (CORS 6 origins, vector threshold `>= 25`, Pydantic `extra="ignore"`).
- `abc-shield-ai/DELIVERY_MANIFEST.md` – This delivery manifest.

### Modified Files:
- `abc-shield-ai/api/models/query.py` – Added `@model_validator(mode="before")` to support Builder query aliases (`prompt`, `text`, `question`, `message`).
- `abc-shield-ai/api/routes/query.py` – Registered `@router.post("/rag/analyze")` and `@router.post("/analyze")` to directly resolve Builder and Backend HTTP 503 connection errors.
- `abc-shield-ai/api/routes/compare.py` – Added `@router.post("/projects/{projectId}/compare-advice")` and `@router.post("/compare-advice")` matching the Backend Gateway proxy route.
- `abc-shield-ai/api/main.py` – Registered root-level fallback routes `/rag/analyze` and `/analyze`.
- `abc-shield-ai/config/settings.py` – Configured all 8 approved CORS origins and port 8001.
- `abc-shield-ai/rag/pipeline/advice_comparator.py` – Implemented dual-format comparison request validation.
- `abc-shield-ai/api/dependencies.py` – Vector count threshold check updated to `>= 25`.

---

## 3. Excluded Files & Artifacts

The following transient, machine-specific, and secret-containing files were strictly excluded:
- `.venv/` and `venv/` (Python virtual environments)
- `__pycache__/` and `*.pyc`, `*.pyo` (Compiled bytecode)
- `.git/` (Git metadata directory)
- `node_modules/` (Frontend packages)
- `.pytest_cache/` and `.coverage` (Test caches and coverage files)
- Temporary files, log files, real database credentials, and secrets

---

## 4. Configuration & Startup Instructions (Windows)

### Environment Setup:
```powershell
# 1. Navigate to RAG service root
cd "D:\FInregTech Shipyard\abc-shield-ai"

# 2. Activate virtual environment
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Exact Startup Command:
```powershell
python -m api.main
```
Or with uvicorn directly:
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

### Simultaneous Operation:
- **Main Backend:** Runs on `http://127.0.0.1:8000`
- **AI/RAG Microservice:** Runs on `http://127.0.0.1:8001`

---

## 5. API Endpoints & URLs

- **Health Check URL:** `http://127.0.0.1:8001/health` and `http://127.0.0.1:8001/api/v1/health`
- **Builder RAG Analysis URL:** `http://127.0.0.1:8001/api/v1/rag/analyze` (and `http://127.0.0.1:8001/api/v1/query`)
- **Comparison URL:** `http://127.0.0.1:8001/api/v1/compare` and `http://127.0.0.1:8001/api/v1/projects/{projectId}/compare-advice`
- **Swagger Documentation:** `http://127.0.0.1:8001/docs`

---

## 6. Test Results Summary

- **Total Tests Collected:** **887**
- **Total Tests Passed:** **887**
- **Total Tests Failed:** **0**
- **Pass Rate:** **100%**
- **Execution Time:** ~2 minutes
