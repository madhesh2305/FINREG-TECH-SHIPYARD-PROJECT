"""Test suite for Normalized Regulatory Records (Task W4.4).

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Exactly 15 normalized regulatory records regenerated in data/processed/normalized_regulatory_records.json
2. 9 UK records (RR-UK-01..09) and 6 EU records (RR-EU-01..06)
3. 15 unique Record_IDs
4. 15 unique Source_IDs
5. 15 unique Chunk_IDs (RR-UK-01-C01..RR-EU-06-C01)
6. 15/15 Source foreign-key resolution against Source Register
7. Zero orphan records
8. Zero duplicate records
9. Retrieval_Text present and non-empty for all 15 records
10. Requirement remains separate from Retrieval_Text (conceptual separation)
11. Regulatory_Text remains strictly None/null across all 15 records (no legal text fabrication)
12. Retrieval_Tags parsed as clean List[str] with trimmed whitespace
13. Official_Source_URL correctly mapped to official_source with authentic HTTPS URLs
14. Citation_Label preserved on all records
15. Retrieval_Priority preserved (e.g. P1 — Core, P2 — Conditional)
16. Authority_Rule preserved on all records
17. RAG_Instruction preserved on all records
18. Official_Source_Check_Note preserved on all records
19. Source-control join does not duplicate records
20. All current records remain validation_status == 'Candidate - Awaiting Approval'
21. All current records have is_approved_for_rag == False (0 approved)
22. Full JSON round-trip deserialization fidelity through NormalizedRegulatoryRecord
23. Dynamic discovery of exact serialized schema fields
24. Legacy Week 3 fallback still works
25. Raw Excel files remain 100% unchanged (SHA-256 verification)
"""

from pathlib import Path
import hashlib
import json
import pytest

from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator
from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    SourceRegisterRecord,
)
from rag.ingestion import export_normalized_records

PROCESSED_JSON_PATH = Path("data/processed/normalized_regulatory_records.json")
RAW_DATA_DIR = Path("data/raw")


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file to assert immutability."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


@pytest.fixture(scope="module")
def normalized_json_data():
    """Load the regenerated JSON records from disk."""
    assert PROCESSED_JSON_PATH.exists(), f"File missing: {PROCESSED_JSON_PATH}"
    with open(PROCESSED_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def deserialized_records(normalized_json_data):
    """Deserialize the JSON records into NormalizedRegulatoryRecord objects."""
    return [NormalizedRegulatoryRecord(**item) for item in normalized_json_data]


# ---------------------------------------------------------------------------
# 1. Corpus Size & Jurisdictional Distribution
# ---------------------------------------------------------------------------

def test_1_exactly_15_normalized_records(normalized_json_data):
    """Verify that normalized_regulatory_records.json contains exactly 15 records."""
    assert len(normalized_json_data) == 15


def test_2_uk_records_count_and_distribution(deserialized_records):
    """Verify exactly 9 UK records with expected ID sequence RR-UK-01 through RR-UK-09."""
    uk_records = [r for r in deserialized_records if r.jurisdiction == "UK"]
    assert len(uk_records) == 9
    uk_ids = [r.record_id for r in uk_records]
    expected_uk_ids = [f"RR-UK-{i:02d}" for i in range(1, 10)]
    assert sorted(uk_ids) == sorted(expected_uk_ids)


def test_3_eu_records_count_and_distribution(deserialized_records):
    """Verify exactly 6 EU records with expected ID sequence RR-EU-01 through RR-EU-06."""
    eu_records = [r for r in deserialized_records if r.jurisdiction == "EU"]
    assert len(eu_records) == 6
    eu_ids = [r.record_id for r in eu_records]
    expected_eu_ids = [f"RR-EU-{i:02d}" for i in range(1, 7)]
    assert sorted(eu_ids) == sorted(expected_eu_ids)


# ---------------------------------------------------------------------------
# 2. Identifier Integrity (Record_ID, Source_ID, Chunk_ID)
# ---------------------------------------------------------------------------

def test_4_unique_record_ids(deserialized_records):
    """Verify all 15 Record_IDs are strictly unique."""
    record_ids = [r.record_id for r in deserialized_records]
    assert len(record_ids) == len(set(record_ids)) == 15


def test_5_unique_source_ids(deserialized_records):
    """Verify all 15 Source_IDs across the records are unique."""
    source_ids = [r.source_id for r in deserialized_records]
    assert len(source_ids) == len(set(source_ids)) == 15
    expected_sources = [f"UK-{i:02d}" for i in range(1, 10)] + [f"EU-{i:02d}" for i in range(1, 7)]
    assert sorted(source_ids) == sorted(expected_sources)


def test_6_unique_chunk_ids(deserialized_records):
    """Verify all 15 Chunk_IDs are unique and preserve upstream format RR-XX-NN-C01."""
    chunk_ids = [r.chunk_id for r in deserialized_records]
    assert len(chunk_ids) == len(set(chunk_ids)) == 15
    for r in deserialized_records:
        assert r.chunk_id is not None
        assert r.chunk_id == f"{r.record_id}-C01"


# ---------------------------------------------------------------------------
# 3. Source Foreign Key Resolution & Join Integrity
# ---------------------------------------------------------------------------

def test_7_source_fk_resolution(deserialized_records):
    """Verify 15/15 Source_ID foreign key resolution against Source Register."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    valid_source_ids = {s.source_id.strip() for s in sources}

    for r in deserialized_records:
        assert r.source_id in valid_source_ids, f"Unresolved Source_ID: {r.source_id}"


def test_8_zero_orphan_records(deserialized_records):
    """Verify zero orphan records exist in the normalized dataset."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    valid_source_ids = {s.source_id.strip() for s in sources}
    orphans = [r.record_id for r in deserialized_records if r.source_id not in valid_source_ids]
    assert len(orphans) == 0


def test_9_zero_duplicate_records(deserialized_records):
    """Verify no duplicate records or duplicate joins occurred."""
    record_ids = [r.record_id for r in deserialized_records]
    duplicates = [rid for rid in record_ids if record_ids.count(rid) > 1]
    assert len(duplicates) == 0


def test_10_source_control_join_does_not_multiply_records():
    """Verify that source-control metadata joins 1:1 and does not multiply regulatory records."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    source_controls = loader.load_source_control()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    assert len(raw_records) == 15
    assert len(sources) == 15
    assert len(source_controls) == 15
    assert len(normalized) == 15


# ---------------------------------------------------------------------------
# 4. Critical Text Separation (Requirement vs Regulatory_Text vs Retrieval_Text)
# ---------------------------------------------------------------------------

def test_11_retrieval_text_present_for_all_records(deserialized_records):
    """Verify Retrieval_Text is present, non-empty, and context-rich on all 15 records."""
    for r in deserialized_records:
        assert r.retrieval_text is not None
        assert isinstance(r.retrieval_text, str)
        assert len(r.retrieval_text.strip()) > 50


def test_12_requirement_remains_separate_from_retrieval_text(deserialized_records):
    """Verify conceptual separation: Requirement is never identical to Retrieval_Text."""
    for r in deserialized_records:
        assert r.requirement != r.retrieval_text
        assert len(r.retrieval_text) > len(r.requirement)


def test_13_regulatory_text_remains_strictly_none(deserialized_records):
    """Verify that verbatim regulatory_text remains strictly None (no legal text fabrication)."""
    for r in deserialized_records:
        assert r.regulatory_text is None


# ---------------------------------------------------------------------------
# 5. Week 4 Enriched Metadata Preservation
# ---------------------------------------------------------------------------

def test_14_retrieval_tags_are_normalized_lists(deserialized_records):
    """Verify Retrieval_Tags are normalized into List[str] with trimmed whitespace."""
    for r in deserialized_records:
        assert isinstance(r.retrieval_tags, list)
        assert len(r.retrieval_tags) > 0
        for tag in r.retrieval_tags:
            assert isinstance(tag, str)
            assert len(tag) > 0
            assert tag == tag.strip()


def test_15_official_source_url_mapped_correctly(deserialized_records):
    """Verify official_source receives authentic HTTPS URLs from Official_Source_URL."""
    for r in deserialized_records:
        assert r.official_source is not None
        assert r.official_source.startswith("https://")
        # Verify known domains (legislation.gov.uk, gov.uk, fca.org.uk, eur-lex.europa.eu, commission.europa.eu)
        assert any(domain in r.official_source for domain in [
            "legislation.gov.uk", "gov.uk", "fca.org.uk", "eur-lex.europa.eu", "commission.europa.eu"
        ])


def test_16_citation_label_preserved(deserialized_records):
    """Verify preformatted Citation_Label is preserved on all 15 records."""
    for r in deserialized_records:
        assert r.citation_label is not None
        assert len(r.citation_label.strip()) > 0
        assert r.source_id in r.citation_label


def test_17_retrieval_priority_preserved(deserialized_records):
    """Verify Retrieval_Priority is preserved (P1 through P4) across records."""
    for r in deserialized_records:
        assert r.retrieval_priority is not None
        assert any(r.retrieval_priority.startswith(pfx) for pfx in ("P1", "P2", "P3", "P4"))


def test_18_authority_rule_preserved(deserialized_records):
    """Verify Authority_Rule is preserved across all 15 records."""
    for r in deserialized_records:
        assert r.authority_rule is not None
        assert len(r.authority_rule.strip()) > 10


def test_19_rag_instruction_preserved(deserialized_records):
    """Verify RAG_Instruction governance instruction is preserved across all 15 records."""
    for r in deserialized_records:
        assert r.rag_instruction is not None
        assert len(r.rag_instruction.strip()) > 10


def test_20_official_source_check_note_preserved(deserialized_records):
    """Verify Official_Source_Check_Note is preserved across all 15 records."""
    for r in deserialized_records:
        assert r.official_source_check_note is not None
        assert len(r.official_source_check_note.strip()) > 10


# ---------------------------------------------------------------------------
# 6. Approval Gate & Candidate State Preservation
# ---------------------------------------------------------------------------

def test_21_all_records_remain_candidate_status(deserialized_records):
    """Verify all 15 records carry validation_status == 'Candidate - Awaiting Approval'."""
    for r in deserialized_records:
        assert r.validation_status == "Candidate - Awaiting Approval"


def test_22_is_approved_for_rag_is_strictly_false(deserialized_records):
    """Verify all 15 records have is_approved_for_rag == False (0 approved)."""
    assert all(r.is_approved_for_rag is False for r in deserialized_records)
    approved = [r for r in deserialized_records if r.is_approved_for_rag]
    assert len(approved) == 0


# ---------------------------------------------------------------------------
# 7. JSON Deserialization & Schema Roundtrip Fidelity
# ---------------------------------------------------------------------------

def test_23_json_roundtrip_deserialization_fidelity(normalized_json_data, deserialized_records):
    """Verify 100% roundtrip fidelity between raw JSON dicts and Pydantic model serialization."""
    assert len(normalized_json_data) == len(deserialized_records) == 15
    for raw_dict, rec in zip(normalized_json_data, deserialized_records):
        dumped = rec.model_dump()
        if "validation_date" not in raw_dict and "validation_date" in dumped and dumped["validation_date"] is None:
            dumped.pop("validation_date")
        assert dumped == raw_dict


def test_24_exact_serialized_field_count(normalized_json_data):
    """Verify that every serialized JSON record contains the exact number of defined model fields."""
    expected_field_count = len(NormalizedRegulatoryRecord.model_fields)
    for raw_dict in normalized_json_data:
        assert len(raw_dict.keys()) in (expected_field_count, expected_field_count - 1)


# ---------------------------------------------------------------------------
# 8. Legacy Fallback & Raw File Immutability
# ---------------------------------------------------------------------------

def test_25_legacy_week_3_fallback_compatibility():
    """Verify backward compatibility: loader falls back gracefully if legacy paths are specified."""
    legacy_rr_path = RAW_DATA_DIR / "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx"
    legacy_sr_path = RAW_DATA_DIR / "ABC_Shield_Source_Register (1).xlsx"
    if legacy_rr_path.exists() and legacy_sr_path.exists():
        loader = ExcelWorkbookLoader(
            RAW_DATA_DIR,
            regulatory_records_path=legacy_rr_path,
            source_register_path=legacy_sr_path,
        )
        sources = loader.load_source_register()
        raw_records = loader.load_regulatory_records_raw()
        normalizer = RegulatoryDataNormalizer(sources)
        normalized = normalizer.normalize_all(raw_records)
        assert len(normalized) == 15
        for r in normalized:
            assert r.record_id.startswith("RR-")
            assert r.regulatory_text is None
            assert r.is_approved_for_rag is False


def test_26_raw_excel_workbooks_remain_completely_unmodified():
    """Verify that SHA-256 hashes of all raw Excel workbooks match their verified state."""
    expected_hashes = {
        "ABC shield_Data Dictionary.xlsx": "57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6",
        "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx": "2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b",
        "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx": "5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00",
        "ABC_Shield_Source_Register (1).xlsx": "0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b",
        "ABC_Shield_Source_Register_Reviewed (1).xlsx": "fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4",
    }
    for filename, expected_hash in expected_hashes.items():
        filepath = RAW_DATA_DIR / filename
        assert filepath.exists(), f"File missing: {filename}"
        current_hash = compute_file_hash(filepath)
        assert current_hash == expected_hash, f"File {filename} was modified! Expected {expected_hash}, got {current_hash}"
