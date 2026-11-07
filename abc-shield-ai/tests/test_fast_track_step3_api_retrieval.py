"""Automated test suite for ABC Shield Fast-Track Step 3: API & Retrieval Integration.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Configuration defaults to canonical knowledge base mode and paths.
2. Shared dependency injection wires ChromaVectorStore to canonical_regulatory_records (25 vectors).
3. Missing canonical persist directory fails closed with FileNotFoundError (no silent fallback).
4. Health endpoints (/health and /api/v1/health) return HTTP 200 with zero internal path leaks.
5. Representative UK query retrieves canonical Bribery Act evidence, UK official URLs,
   provisional validation status, and candidate approval warnings.
6. Representative EU query retrieves canonical Directive (EU) 2026/1021 evidence from EUR-Lex with EU jurisdiction filter.
7. Approved-only query (filter_approved_only=True) fails closed: 0 citations, 0 approved advice,
   UNAPPROVED_EVIDENCE gap status, and human review required.
8. Compare endpoint (/api/v1/compare) retrieves supporting evidence, identifies CO-001, and preserves decision=None.
9. Active production stores (data/processed/ and data/raw/) remain strictly unmodified.
"""

from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import (
    get_grounded_generator,
    get_configured_vector_store,
    reset_grounded_generator,
    check_chromadb_connectivity,
)
from config.settings import settings
from rag.output.structured_response import StructuredAIResponse, ResponseStatus
from rag.generation.gap_handler import GapType, GapHandler
from rag.retrieval.vector_store import ChromaVectorStore


@pytest.fixture(scope="module")
def client():
    """Shared FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# 1. Configuration & Dependency Defaults
# ---------------------------------------------------------------------------

def test_default_settings_mode_is_canonical():
    """Test 1: Configuration defaults to canonical knowledge base mode and 25-vector collection."""
    assert settings.rag_knowledge_base_mode == "canonical"
    assert settings.chroma_collection_name == "canonical_regulatory_records"
    assert Path(settings.chroma_persist_dir) == Path("data/staging/madhesh_handover/step6/chroma_db")
    assert Path(settings.canonical_chroma_persist_dir) == Path("data/staging/madhesh_handover/step6/chroma_db")
    assert settings.canonical_chroma_collection_name == "canonical_regulatory_records"
    assert Path(settings.legacy_chroma_persist_dir) == Path("data/processed/chroma_db")
    assert settings.legacy_chroma_collection_name == "regulatory_records"


def test_dependency_injection_wires_canonical_vector_store():
    """Test 2: get_configured_vector_store() returns canonical store with exactly 25 vectors."""
    reset_grounded_generator()
    store = get_configured_vector_store()
    assert store.collection_name == "canonical_regulatory_records"
    assert Path(store.persist_dir) == Path("data/staging/madhesh_handover/step6/chroma_db")
    stats = store.get_collection_stats()
    assert stats["total_vectors"] == 25


def test_fail_closed_when_canonical_store_missing(monkeypatch):
    """Test 3: Missing canonical persist directory raises FileNotFoundError and fails closed."""
    non_existent = Path("data/staging/non_existent_chroma_dir_abc123")
    monkeypatch.setattr(settings, "canonical_chroma_persist_dir", non_existent)
    monkeypatch.setattr(settings, "chroma_persist_dir", non_existent)

    with pytest.raises(FileNotFoundError) as exc_info:
        get_configured_vector_store()

    assert "Failing closed to prevent silent fallback" in str(exc_info.value)
    assert str(non_existent) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 2. Health Endpoints Verification
# ---------------------------------------------------------------------------

def test_health_endpoints_live_connectivity_and_zero_path_leaks(client):
    """Test 4: /health and /api/v1/health return HTTP 200 with connected status and no leaked paths."""
    reset_grounded_generator()
    for endpoint in ["/health", "/api/v1/health"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app_name"] == "ABC Shield FinRegTech API"
        assert data["rag_pipeline_initialized"] is True
        assert data["chromadb_status"] == "connected"
        assert "data/staging" not in str(data)
        assert "data/processed" not in str(data)
        assert "madhesh" not in str(data)
        assert "path" not in data


# ---------------------------------------------------------------------------
# 3. Live Query: Representative UK Regulatory Evidence
# ---------------------------------------------------------------------------

def test_live_query_uk_bribery_act_retrieval_citations_and_candidate_warning(client):
    """Test 5: Representative UK query retrieves canonical Bribery Act evidence with candidate warning."""
    reset_grounded_generator()
    query_payload = {
        "query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption",
        },
    }
    response = client.post("/api/v1/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    # Adheres to StructuredAIResponse schema
    resp_obj = StructuredAIResponse(**data)
    assert resp_obj.status == ResponseStatus.GROUNDED
    assert resp_obj.grounded is True
    assert len(resp_obj.citations) > 0

    # Verify canonical chunk and official source
    c0 = resp_obj.citations[0]
    assert c0.chunk_id.startswith("UK-01-")
    assert c0.official_source == "https://www.legislation.gov.uk/ukpga/2010/23/section/1"
    assert c0.validation_status == "Approved for RAG Integration - Pending SME Validation"
    assert c0.is_approved_for_rag is False

    # Verify candidate metadata and human review requirement
    assert resp_obj.metadata.has_candidate_evidence is True
    assert resp_obj.metadata.requires_human_review is True
    assert resp_obj.metadata.approved_evidence_count == 0


# ---------------------------------------------------------------------------
# 4. Live Query: Representative EU Regulatory Evidence
# ---------------------------------------------------------------------------

def test_live_query_eu_directive_retrieval_citations(client):
    """Test 6: Representative EU query retrieves canonical Directive (EU) 2026/1021 evidence."""
    reset_grounded_generator()
    query_payload = {
        "query": "What does Directive (EU) 2026/1021 establish regarding private-sector bribery?",
        "context": {
            "jurisdiction": "EU",
            "regulatory_area": "Anti-Corruption",
        },
    }
    response = client.post("/api/v1/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    resp_obj = StructuredAIResponse(**data)
    assert resp_obj.status == ResponseStatus.GROUNDED
    assert resp_obj.grounded is True
    assert len(resp_obj.citations) > 0

    # Ensure EU citations map to EUR-Lex official sources and EU-01 chunks
    eu_cits = [c for c in resp_obj.citations if c.chunk_id.startswith("EU-01-")]
    assert len(eu_cits) > 0
    for cit in eu_cits:
        assert "europa.eu" in cit.official_source or "eur-lex" in cit.official_source
        assert cit.validation_status == "Approved for RAG Integration - Pending SME Validation"
        assert cit.is_approved_for_rag is False
        assert cit.jurisdiction == "EU-level"

    assert resp_obj.metadata.has_candidate_evidence is True


# ---------------------------------------------------------------------------
# 5. Approved-Only Query Fails Closed (Zero Candidate Advice)
# ---------------------------------------------------------------------------

def test_approved_only_query_fails_closed_zero_candidate_advice(client):
    """Test 7: Approved-only query (filter_approved_only=True) returns UNAPPROVED_EVIDENCE and zero citations."""
    reset_grounded_generator()
    query_payload = {
        "query": "What procedures should commercial organisations implement to prevent bribery?",
        "context": {
            "filter_approved_only": True,
            "jurisdiction": "UK",
        },
    }
    response = client.post("/api/v1/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()

    resp_obj = StructuredAIResponse(**data)
    # Fail closed: must NOT be grounded, must NOT serve unapproved candidate evidence
    assert resp_obj.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert resp_obj.grounded is False
    assert len(resp_obj.citations) == 0
    assert len(resp_obj.retrieved_evidence) == 0
    assert resp_obj.metadata.retrieved_count == 0
    assert resp_obj.metadata.approved_evidence_count == 0

    # Gap structure must indicate candidate evidence exists in corpus but cannot be queried
    assert resp_obj.gap is not None
    assert resp_obj.gap.gap_type == GapType.UNAPPROVED_EVIDENCE
    assert resp_obj.gap.has_candidate_evidence is True
    assert resp_obj.metadata.requires_human_review is True


# ---------------------------------------------------------------------------
# 6. Advice Compare Endpoint Integration
# ---------------------------------------------------------------------------

def test_advice_compare_endpoint_with_canonical_corpus_and_conflict_co001(client):
    """Test 8: POST /api/v1/compare retrieves canonical evidence, flags CO-001, and preserves decision=None."""
    reset_grounded_generator()
    payload = {
        "comparison_id": "CMP-CANONICAL-001",
        "requirement_ids": ["REQ-UK-01"],
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
        },
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption",
        },
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["comparison_id"] == "CMP-CANONICAL-001"
    assert data["decision"] is None
    assert data["human_review_required"] is True
    assert len(data["differences"]) >= 1

    # Conflict detection over retrieved canonical chunks: CO-001 (Bribery Act vs MoJ Guidance)
    conflict_ids = [rel["conflict_id"] for rel in data.get("relationships", [])]
    assert "CO-001" in conflict_ids

    # Supporting evidence traces to canonical chunks
    assert len(data["citations"]) > 0
    for cit in data["citations"]:
        assert cit["validation_status"] == "Approved for RAG Integration - Pending SME Validation"
        assert cit["is_approved_for_rag"] is False


# ---------------------------------------------------------------------------
# 7. Immutability of Production Store and Raw Files
# ---------------------------------------------------------------------------

def test_active_production_store_and_raw_files_unmodified():
    """Test 9: Verify active production store (15 vectors/chunks) and raw files remain untouched."""
    active_store = ChromaVectorStore(
        persist_dir=Path("data/processed/chroma_db"),
        collection_name="regulatory_records",
    )
    assert active_store.get_collection_stats()["total_vectors"] == 15

    active_chunks = Path("data/processed/regulatory_chunks.json")
    with open(active_chunks, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
    assert len(chunks_data) == 15

    active_norm = Path("data/processed/normalized_regulatory_records.json")
    with open(active_norm, "r", encoding="utf-8") as f:
        norm_data = json.load(f)
    assert len(norm_data) == 15

    raw_files = list(Path("data/raw").glob("*.xlsx"))
    assert len(raw_files) == 7
