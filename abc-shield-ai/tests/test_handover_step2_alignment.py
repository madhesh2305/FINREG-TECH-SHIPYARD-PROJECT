"""Tests for Step 2: Canonical Source Register Alignment.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. ExcelWorkbookLoader selects canonical source register from data/raw/
2. Exactly 15 sources loaded: UK-01..UK-09 and EU-01..EU-06
3. Zero missing, zero duplicate source IDs
4. Source metadata preservation (URLs, authority, jurisdiction, level, version, status)
5. 100% resolution of 25-record corpus source IDs (EU-01, UK-01, UK-02, UK-03, UK-09)
6. Normalized records have 0 critical validator errors
7. Candidate gating: 25 Candidate / 0 Approved (is_approved_for_rag = False)
8. Active processed data & ChromaDB remain strictly untouched (15 records, 15 chunks, 15 vectors)
"""

from pathlib import Path
import json
import pytest

from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator
from rag.retrieval.vector_store import ChromaVectorStore

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


def test_loader_selects_canonical_source_register():
    """Verify ExcelWorkbookLoader directly selects ABC_Shield_Canonical_Source_Register.xlsx."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    expected_path = RAW_DATA_DIR / ExcelWorkbookLoader.CANONICAL_SOURCE_REGISTER_FILENAME
    assert loader.source_register_path.resolve() == expected_path.resolve()
    assert loader.source_register_path.exists()


def test_source_register_count_and_expected_ids():
    """Verify exactly 15 sources are loaded with IDs UK-01..UK-09 and EU-01..EU-06."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()

    assert len(sources) == 15
    source_ids = [s.source_id for s in sources]

    # No duplicates
    assert len(source_ids) == len(set(source_ids))

    # No missing/empty IDs
    assert all(bool(sid and sid.strip()) for sid in source_ids)

    # Exactly UK-01..UK-09 and EU-01..EU-06
    expected_uk = [f"UK-{i:02d}" for i in range(1, 10)]
    expected_eu = [f"EU-{i:02d}" for i in range(1, 7)]
    expected_ids = set(expected_uk + expected_eu)
    assert set(source_ids) == expected_ids


def test_source_metadata_preservation():
    """Verify source metadata fields are preserved from the canonical sheet without invention."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    sources_by_id = {s.source_id: s for s in sources}

    # UK-01: Bribery Act 2010 (Primary Law)
    uk01 = sources_by_id["UK-01"]
    assert uk01.source_name == "Bribery Act 2010"
    assert uk01.issuing_authority == "UK Parliament / legislation.gov.uk"
    assert uk01.jurisdiction == "UK"
    assert uk01.authority_level == "A"
    assert uk01.source_type == "Primary Legislation"
    assert uk01.official_link_reference == "https://www.legislation.gov.uk/ukpga/2010/23/contents"
    assert uk01.corpus_record_count == 6

    # UK-03: FCA FCG 6
    uk03 = sources_by_id["UK-03"]
    assert "FCA Financial Crime Guide" in uk03.source_name
    assert uk03.issuing_authority == "Financial Conduct Authority"
    assert uk03.jurisdiction == "UK"
    assert uk03.authority_level == "C"
    assert uk03.corpus_record_count == 5

    # EU-01: Directive (EU) 2026/1021
    eu01 = sources_by_id["EU-01"]
    assert "Directive (EU) 2026/1021" in eu01.source_name
    assert eu01.jurisdiction == "EU"
    assert eu01.authority_level == "A"
    assert eu01.corpus_record_count == 7


def test_corpus_source_id_reconciliation():
    """Verify all 25 corpus records reference valid Source IDs from the canonical register."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    source_ids = {s.source_id for s in sources}

    raw_records = loader.load_regulatory_records_raw()
    assert len(raw_records) == 25

    corpus_source_ids = {r.get("Source_ID") for r in raw_records}
    assert corpus_source_ids == {"UK-01", "UK-02", "UK-03", "UK-09", "EU-01"}

    # Zero unresolved source IDs
    unresolved = corpus_source_ids - source_ids
    assert len(unresolved) == 0


def test_normalization_and_validation_with_canonical_sources():
    """Verify normalizer and validator succeed with 0 critical errors using canonical sources."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    assert len(normalized) == 25

    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records(normalized)

    assert report.total_records == 25
    assert report.valid_records_count == 25
    assert report.all_source_ids_resolved is True
    assert report.has_critical_errors is False
    assert len(report.issues) == 0


def test_candidate_gating_preserved_across_all_25_records():
    """Verify all 25 records remain Candidate / 0 Approved."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        assert rec.is_approved_for_rag is False
        assert rec.validation_status in ("Candidate - Awaiting Approval", "Pending SME Validation")


def test_active_processed_data_and_chromadb_immutability():
    """Verify active processed JSON and active ChromaDB remain strictly untouched at 15 items."""
    norm_path = PROCESSED_DATA_DIR / "normalized_regulatory_records.json"
    chunk_path = PROCESSED_DATA_DIR / "regulatory_chunks.json"

    assert norm_path.exists()
    assert chunk_path.exists()

    with open(norm_path, "r", encoding="utf-8") as f:
        norm_data = json.load(f)
    with open(chunk_path, "r", encoding="utf-8") as f:
        chunk_data = json.load(f)

    assert len(norm_data) == 15
    assert len(chunk_data) == 15

    # Check ChromaDB
    chroma_store = ChromaVectorStore(persist_dir=PROCESSED_DATA_DIR / "chroma_db")
    assert chroma_store._get_collection().count() == 15
