"""Tests for Step 1 — Ingestion Loader and Normalizer Adaptation (Madhesh Handover).

Verifies:
1. Safe loading of staged canonical handover workbooks from data/incoming_handover_20261014/:
   - Data Dictionary: 18 entries from 'Data_Dictionary' sheet.
   - Source Register: 15 sources from 'Source Register' sheet with canonical columns.
   - Regulatory Corpus: 25 records from 'Regulatory_Records' sheet.
2. Normalization & Field Mapping Integrity:
   - Structured_Summary maps to requirement and summary.
   - Exact_Source_Extract is preserved separately (never used as fallback for requirement).
   - If requirement/summary is missing, raises clear ValueError.
   - Non-fabrication of metadata, dates, authority levels, URLs, and validation statuses.
3. Approval Gate Security:
   - is_approved_for_rag == False strictly enforced for all 25 incoming records.
   - 'Approved for Extraction' does NOT confer SME approval.
4. Chunker Execution on Staged Records:
   - Evaluates chunking in-memory without writing to disk or ChromaDB.
5. Conflict Overlap Source Determinism:
   - CO-001 through CO-011 verified from deterministic conflict source.
   - Clear failure if target workbook lacks conflict sheet.
6. 100% Backward Compatibility:
   - data/raw/ active workbooks load identically with 15 records, 17 data dictionary entries,
     15 sources, and 11 conflict records.
"""

from pathlib import Path
import pytest

from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator
from rag.ingestion.chunker import RegulatoryRecordChunker
from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
    SourceRegisterRecord,
    DataDictionaryEntry,
    ConflictOverlapRecord,
)

STAGED_HANDOVER_DIR = Path("data/incoming_handover_20261014")
ACTIVE_RAW_DIR = Path("data/raw")


# ---------------------------------------------------------------------------
# 1. Staged Data Loading Tests
# ---------------------------------------------------------------------------

def test_staged_data_dictionary_loaded():
    """Verify loader reads 18 data dictionary entries from staged Data_Dictionary sheet."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    entries = loader.load_data_dictionary()
    assert len(entries) == 18
    assert all(isinstance(e, DataDictionaryEntry) for e in entries)
    
    # Check field names
    field_names = [e.field_name for e in entries]
    assert "Record_ID" in field_names
    assert "Exact_Source_Extract" in field_names
    assert "Structured_Summary" in field_names
    assert "Regulatory_Layer" in field_names


def test_staged_source_register_loaded():
    """Verify loader reads all 15 sources with canonical column mappings from staged workbook."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    assert len(sources) == 15
    assert all(isinstance(s, SourceRegisterRecord) for s in sources)

    source_map = {s.source_id: s for s in sources}
    assert "UK-01" in source_map
    assert "EU-01" in source_map

    # UK-01 checks
    uk01 = source_map["UK-01"]
    assert uk01.source_name == "Bribery Act 2010"
    assert uk01.authority_level == "A"
    assert uk01.source_type == "Primary Legislation"
    assert uk01.status == "Approved for Extraction - Pending SME Validation"
    assert uk01.regulatory_layer == "Primary Law"
    assert uk01.corpus_record_count == 6
    assert uk01.corpus_status_current == "Approved for Extraction"
    assert uk01.abc_shield_relevance == "CORE - Primary UK anti-bribery legislation."
    assert uk01.source_qa_note is not None and "curated corpus" in uk01.source_qa_note


def test_staged_regulatory_records_raw_loaded():
    """Verify loader reads exactly 25 raw records from staged Regulatory_Records sheet."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    raw_records = loader.load_regulatory_records_raw()
    assert len(raw_records) == 25

    record_ids = [r.get("Record_ID") for r in raw_records]
    assert "UK-01-R001" in record_ids
    assert "UK-01-R006" in record_ids
    assert "EU-01-R001" in record_ids
    assert "EU-01-R007" in record_ids
    assert "UK-09-R001" in record_ids


# ---------------------------------------------------------------------------
# 2. Normalization & Requirement/Summary Mapping Tests
# ---------------------------------------------------------------------------

def test_staged_records_normalized_correctly():
    """Verify normalization maps Structured_Summary to requirement and summary without extract fallback."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    assert len(normalized) == 25

    for rec in normalized:
        assert isinstance(rec, NormalizedRegulatoryRecord)
        assert rec.record_id is not None and len(rec.record_id) > 0
        assert rec.source_id in ("UK-01", "UK-02", "UK-03", "EU-01", "UK-09")
        assert rec.requirement is not None and len(rec.requirement) > 0
        assert rec.summary is not None and rec.summary == rec.requirement
        assert rec.regulatory_text is not None and len(rec.regulatory_text) > 0
        assert rec.requirement != rec.regulatory_text
        assert rec.source_type is not None


def test_requirement_does_not_fall_back_to_extract():
    """Verify that if requirement/Structured_Summary is absent, it fails with ValueError rather than falling back to extract."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    normalizer = RegulatoryDataNormalizer(sources)

    # Malformed record with Exact_Source_Extract but NO Requirement and NO Structured_Summary
    malformed_record = {
        "Record_ID": "TEST-R001",
        "Source_ID": "UK-01",
        "Exact_Source_Extract": "Some exact verbatim statutory extract text.",
        "Requirement": None,
        "Structured_Summary": None,
    }

    with pytest.raises(ValueError, match="Requirement/Structured_Summary is mandatory"):
        normalizer.normalize_record(malformed_record)


# ---------------------------------------------------------------------------
# 3. Approval Gate Security Tests
# ---------------------------------------------------------------------------

def test_all_25_incoming_records_are_candidate_status_and_not_approved():
    """Strictly assert that is_approved_for_rag == False for all 25 records.
    
    'Approved for Extraction' does NOT confer SME approval.
    """
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    assert len(normalized) == 25
    for rec in normalized:
        assert rec.is_approved_for_rag is False, f"Record {rec.record_id} must have is_approved_for_rag=False"
        assert "Pending" in rec.validation_status or "Candidate" in rec.validation_status


def test_staged_validation_report_has_zero_critical_errors():
    """Verify RegulatoryDataValidator validates all 25 records with 0 critical errors."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    validator = RegulatoryDataValidator(sources, require_retrieval_text=True)
    report = validator.validate_records(normalized)

    assert report.total_records == 25
    assert report.candidate_records_count == 25
    assert report.approved_records_count == 0
    assert report.has_critical_errors is False
    assert report.all_source_ids_resolved is True


# ---------------------------------------------------------------------------
# 4. In-Memory Chunking Validation (Zero Disk Writes)
# ---------------------------------------------------------------------------

def test_staged_records_chunking_in_memory():
    """Verify chunker runs on staged normalized records in-memory without disk writes."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(normalized)

    # Actual count produced by chunker
    assert len(chunks) == 25
    for c in chunks:
        assert isinstance(c, RegulatoryChunk)
        assert c.is_approved_for_rag is False
        assert c.text is not None and len(c.text) > 0
        assert c.regulatory_text is not None
        assert c.requirement is not None


# ---------------------------------------------------------------------------
# 5. Deterministic Conflict Overlap Source Tests
# ---------------------------------------------------------------------------

def test_conflict_overlap_loads_co001_through_co011():
    """Verify that CO-001 through CO-011 are deterministically loaded from verified conflict source."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    conflicts = loader.load_conflict_overlap()

    assert len(conflicts) == 11
    conflict_ids = [c.conflict_id for c in conflicts]
    expected_ids = [f"CO-{i:03d}" for i in range(1, 12)]
    assert conflict_ids == expected_ids

    # Verify first conflict
    co001 = conflicts[0]
    assert co001.conflict_id == "CO-001"
    assert co001.source_id_1 == "UK-01"
    assert co001.source_id_2 == "UK-02"
    assert co001.relationship == "Overlap - complementary"


def test_conflict_overlap_fails_clearly_when_sheet_missing():
    """Verify clear ValueError when a file lacking conflict sheets is explicitly passed."""
    loader = ExcelWorkbookLoader(STAGED_HANDOVER_DIR)
    # The canonical 25-record corpus lacks Conflict_Handling
    canonical_corpus_path = loader.regulatory_records_path

    with pytest.raises(ValueError, match="does not contain required conflict sheet"):
        loader.load_conflict_overlap(conflict_path=canonical_corpus_path)


# ---------------------------------------------------------------------------
# 6. Backward Compatibility for Active data/raw/ Pipeline
# ---------------------------------------------------------------------------

def test_active_raw_data_backward_compatibility():
    """Verify loader and normalizer remain 100% backward-compatible with active data/raw/."""
    loader = ExcelWorkbookLoader(
        ACTIVE_RAW_DIR,
        regulatory_records_path=ACTIVE_RAW_DIR / ExcelWorkbookLoader.PREFERRED_RAG_KNOWLEDGE_FILENAME,
        source_register_path=ACTIVE_RAW_DIR / ExcelWorkbookLoader.PREFERRED_SOURCE_REGISTER_FILENAME,
    )
    
    # 1. Data Dictionary
    dd = loader.load_data_dictionary()
    assert len(dd) == 17

    # 2. Source Register
    sources = loader.load_source_register()
    assert len(sources) == 15

    # 3. Raw records
    raw_records = loader.load_regulatory_records_raw()
    assert len(raw_records) == 15

    # 4. Normalized records
    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    assert len(normalized) == 15
    for rec in normalized:
        assert rec.record_id.startswith("RR-")
        assert rec.is_approved_for_rag is False
        assert rec.regulatory_text is None  # Non-fabrication in active corpus
        assert rec.requirement is not None

    # 5. Validation
    validator = RegulatoryDataValidator(sources, require_retrieval_text=True)
    report = validator.validate_records(normalized)
    assert report.total_records == 15
    assert report.candidate_records_count == 15
    assert report.approved_records_count == 0
    assert report.has_critical_errors is False

    # 6. Chunks
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(normalized)
    assert len(chunks) == 15

    # 7. Conflicts
    conflicts = loader.load_conflict_overlap()
    assert len(conflicts) == 11
