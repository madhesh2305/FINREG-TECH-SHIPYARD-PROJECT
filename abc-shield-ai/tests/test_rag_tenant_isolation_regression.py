"""Tenant isolation and zero-retrieval regression test suite.

Proves:
1. Null project_id retrieves eligible public evidence.
2. A matching project_id retrieves only that project's records.
3. A different project_id retrieves no records (fails closed).
4. Null project_id does not expose tenant-private records.
5. Missing database paths fail safely without creating empty directories.
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_configured_vector_store, _resolve_db_path
from api.models.query import QueryRequest
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult, StagedRegulatoryRetriever
from rag.retrieval.embeddings import EmbeddingManager
from rag.output.structured_response import ResponseStatus


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_null_project_id_retrieves_eligible_public_evidence(client):
    """Test 1: Null project_id retrieves eligible public regulatory evidence."""
    # Direct API endpoint test with project_id=None
    res = client.post(
        "/api/v1/query",
        json={
            "query": "What procedures should commercial organisations implement to prevent bribery?",
            "project_id": None,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == ResponseStatus.GROUNDED.value
    assert data["grounded"] is True
    assert len(data["retrieved_evidence"]) > 0
    assert len(data["citations"]) > 0
    assert data["gap"] is None

    # Verify key canonical chunks are present
    retrieved_chunk_ids = [c["chunk_id"] for c in data["retrieved_evidence"]]
    assert "UK-01-R004-C01" in retrieved_chunk_ids  # Section 7

    # Direct retriever test
    store = get_configured_vector_store()
    retriever = RegulatoryRetriever(vector_store=store)
    results = retriever.retrieve(
        "What procedures should commercial organisations implement to prevent bribery?",
        project_id=None,
    )
    assert len(results) >= 1
    assert any(r.chunk_id == "UK-01-R004-C01" for r in results)
    assert all(r.project_id is None for r in results)


def test_matching_project_id_retrieves_only_that_projects_records():
    """Test 2: A matching project_id retrieves only that project's records."""
    mock_store = MagicMock()
    mock_embedding = MagicMock(spec=EmbeddingManager)
    mock_embedding.embed_text.return_value = [0.1] * 384

    # Setup simulated vector store candidates:
    # 2 public chunks (no project_id), 2 tenant ALPHA chunks, 2 tenant BETA chunks
    raw_candidates = [
        {
            "chunk_id": "PUB-01",
            "text": "Public regulation text 1",
            "similarity_score": 0.85,
            "distance": 0.15,
            "metadata": {
                "record_id": "PUB-REC-01",
                "regulation": "Public Act 2020",
                "jurisdiction": "UK",
                "project_id": None,
            },
        },
        {
            "chunk_id": "ALPHA-01",
            "text": "Tenant Alpha private policy",
            "similarity_score": 0.90,
            "distance": 0.10,
            "metadata": {
                "record_id": "ALPHA-REC-01",
                "regulation": "Tenant Alpha Compliance Manual",
                "jurisdiction": "UK",
                "project_id": "PRJ-TENANT-ALPHA",
            },
        },
        {
            "chunk_id": "BETA-01",
            "text": "Tenant Beta private policy",
            "similarity_score": 0.88,
            "distance": 0.12,
            "metadata": {
                "record_id": "BETA-REC-01",
                "regulation": "Tenant Beta Compliance Manual",
                "jurisdiction": "UK",
                "project_id": "PRJ-TENANT-BETA",
            },
        },
    ]

    def mock_query(query_embedding, top_k, where=None):
        # Emulate ChromaDB server-side where filter
        if where and "project_id" in where:
            target_pid = where["project_id"]
            return [c for c in raw_candidates if c["metadata"].get("project_id") == target_pid]
        return raw_candidates

    mock_store.query.side_effect = mock_query

    retriever = RegulatoryRetriever(embedding_manager=mock_embedding, vector_store=mock_store)

    # Query with project_id="PRJ-TENANT-ALPHA"
    results = retriever.retrieve("compliance policy", project_id="PRJ-TENANT-ALPHA")
    assert len(results) == 1
    assert results[0].chunk_id == "ALPHA-01"
    assert results[0].project_id == "PRJ-TENANT-ALPHA"

    # Must NEVER include public records or Tenant Beta records
    chunk_ids = [r.chunk_id for r in results]
    assert "PUB-01" not in chunk_ids
    assert "BETA-01" not in chunk_ids


def test_different_project_id_retrieves_no_records(client):
    """Test 3: A different/unassigned project_id retrieves no records (fails closed)."""
    # 1. API endpoint with foreign project_id
    res = client.post(
        "/api/v1/query",
        json={
            "query": "What procedures should commercial organisations implement to prevent bribery?",
            "project_id": "PRJ-FOREIGN-TENANT-XYZ",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == ResponseStatus.INSUFFICIENT_EVIDENCE.value
    assert data["grounded"] is False
    assert len(data["retrieved_evidence"]) == 0
    assert len(data["citations"]) == 0
    assert data["gap"]["gap_type"] == "NO_RETRIEVED_EVIDENCE"

    # 2. Direct retriever call with foreign project_id
    store = get_configured_vector_store()
    retriever = RegulatoryRetriever(vector_store=store)
    results = retriever.retrieve(
        "What procedures should commercial organisations implement to prevent bribery?",
        project_id="PRJ-FOREIGN-TENANT-XYZ",
    )
    assert len(results) == 0


def test_null_project_id_does_not_expose_tenant_private_records():
    """Test 4: Null project_id does not expose tenant-private records."""
    mock_store = MagicMock()
    mock_embedding = MagicMock(spec=EmbeddingManager)
    mock_embedding.embed_text.return_value = [0.1] * 384

    # Raw results containing a mix of public and tenant-private chunks
    mock_store.query.return_value = [
        {
            "chunk_id": "PUB-CHUNK-01",
            "text": "Public regulation text",
            "similarity_score": 0.80,
            "distance": 0.20,
            "metadata": {
                "record_id": "PUB-01",
                "regulation": "Public Act 2020",
                "jurisdiction": "UK",
                "project_id": None,
            },
        },
        {
            "chunk_id": "TENANT-CHUNK-01",
            "text": "Confidential Tenant Private Procedure",
            "similarity_score": 0.95,
            "distance": 0.05,
            "metadata": {
                "record_id": "TENANT-01",
                "regulation": "Private Internal Policy",
                "jurisdiction": "UK",
                "project_id": "PRJ-CONFIDENTIAL-001",
            },
        },
    ]

    retriever = RegulatoryRetriever(embedding_manager=mock_embedding, vector_store=mock_store)

    # Query with project_id=None
    results = retriever.retrieve("procedure", project_id=None)

    # Must only return public chunks; tenant-private chunk must be filtered out
    assert len(results) == 1
    assert results[0].chunk_id == "PUB-CHUNK-01"
    assert results[0].project_id is None

    # Verify no tenant-private chunk was exposed
    exposed_ids = [r.chunk_id for r in results]
    assert "TENANT-CHUNK-01" not in exposed_ids


def test_missing_database_paths_fail_safely():
    """Test 5: Missing database paths fail safely without creating empty directories."""
    nonexistent = Path("data/staging/definitely_nonexistent_test_db_dir_xyz")
    # Ensure it definitely does not exist
    assert not nonexistent.exists()

    # 1. _resolve_db_path returns the original path when neither cwd nor PROJECT_ROOT has it
    resolved = _resolve_db_path(nonexistent)
    assert not resolved.exists()

    # 2. StagedRegulatoryRetriever must fail closed with FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        StagedRegulatoryRetriever(persist_dir=nonexistent)
    assert "Staging ChromaDB directory not found" in str(exc_info.value)

    # 3. Verify no empty directory was accidentally created on disk
    assert not nonexistent.exists()


def test_execution_from_parent_working_directory(monkeypatch):
    """Test 6: Execution from parent working directory resolves paths deterministically."""
    from rag.retrieval.retriever import PROJECT_ROOT as RET_PROJ_ROOT
    from api.dependencies import PROJECT_ROOT as DEP_PROJ_ROOT

    # Verify project root calculations match
    assert RET_PROJ_ROOT == DEP_PROJ_ROOT
    assert RET_PROJ_ROOT.name == "abc-shield-ai"

    # Simulate running from parent directory (D:\FInregTech Shipyard)
    parent_dir = RET_PROJ_ROOT.parent
    monkeypatch.chdir(parent_dir)
    assert Path.cwd() == parent_dir

    # 1. StagedRegulatoryRetriever resolves path deterministically from parent CWD
    retriever = StagedRegulatoryRetriever()
    assert retriever.vector_store.persist_dir.exists()
    assert (retriever.vector_store.persist_dir / "chroma.sqlite3").exists()

    # 2. get_configured_vector_store resolves path deterministically from parent CWD
    store = get_configured_vector_store()
    assert store.persist_dir.exists()
    assert (store.persist_dir / "chroma.sqlite3").exists()

