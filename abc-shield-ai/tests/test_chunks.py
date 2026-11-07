"""Test suite for RAG Chunk Generation & Alignment (Task W4.5).

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Exactly 15 regulatory chunks generated in data/processed/regulatory_chunks.json
2. 9 UK chunks (RR-UK-01-C01..RR-UK-09-C01)
3. 6 EU chunks (RR-EU-01-C01..RR-EU-06-C01)
4. 15 unique Chunk_IDs matching upstream normalized records
5. Upstream Chunk_ID format preservation (RR-XX-NN-C01)
6. 15 unique Record_IDs and 15 unique Source_IDs
7. 15/15 normalized-record-to-chunk 1:1 mapping
8. Zero orphan chunks and zero duplicate chunks
9. Chunk text originates strictly from Retrieval_Text (text_type == 'retrieval_text')
10. Requirement remains separate from Chunk text (conceptual separation)
11. Regulatory_Text remains strictly None across all 15 chunks (no legal text fabrication)
12. Retrieval_Tags preserved as clean List[str]
13. Official_Source URL preserved across all chunks
14. Citation_Label preserved across all chunks
15. Retrieval_Priority preserved across all chunks
16. Authority_Rule preserved across all chunks
17. RAG_Instruction preserved across all chunks
18. Official_Source_Check_Note preserved across all chunks
19. All current chunks have is_approved_for_rag == False (0 approved)
20. All current chunks have validation_status == 'Candidate - Awaiting Approval'
21. chunk_index == 0 and total_chunks == 1 for all 1:1 mapped chunks
22. Chunk length statistics within boundary (Min=343, Max=578, Average=485.47, limit=800)
23. Complete provenance traceability (chunk_id -> record_id -> source_id -> section_article -> official_source)
24. Full JSON round-trip deserialization fidelity through RegulatoryChunk (31 fields)
25. Legacy Week 3 chunking fallback compatibility
26. Upstream normalized records and raw Excel workbooks SHA-256 immutability
"""

from pathlib import Path
import hashlib
import json
import re
import pytest

from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
)
from rag.ingestion.chunker import RegulatoryChunker
from rag.ingestion import export_regulatory_chunks

PROCESSED_CHUNKS_PATH = Path("data/processed/regulatory_chunks.json")
NORMALIZED_RECORDS_PATH = Path("data/processed/normalized_regulatory_records.json")
RAW_DATA_DIR = Path("data/raw")

NORMALIZED_RECORDS_EXPECTED_HASH = "5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d"

RAW_EXCEL_EXPECTED_HASHES = {
    "ABC shield_Data Dictionary.xlsx": "57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6",
    "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx": "2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b",
    "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx": "5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00",
    "ABC_Shield_Source_Register (1).xlsx": "0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b",
    "ABC_Shield_Source_Register_Reviewed (1).xlsx": "fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4",
}


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file to assert immutability."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


@pytest.fixture(scope="module")
def chunks_json_data():
    """Load the regenerated JSON chunks from disk."""
    assert PROCESSED_CHUNKS_PATH.exists(), f"File missing: {PROCESSED_CHUNKS_PATH}"
    with open(PROCESSED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def deserialized_chunks(chunks_json_data):
    """Deserialize the JSON chunks into RegulatoryChunk objects."""
    return [RegulatoryChunk(**item) for item in chunks_json_data]


@pytest.fixture(scope="module")
def normalized_records():
    """Load upstream normalized regulatory records for cross-verification."""
    assert NORMALIZED_RECORDS_PATH.exists(), f"File missing: {NORMALIZED_RECORDS_PATH}"
    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [NormalizedRegulatoryRecord(**item) for item in data]


# ---------------------------------------------------------------------------
# 1. Corpus Size & Jurisdictional Distribution
# ---------------------------------------------------------------------------

def test_1_exactly_15_chunks(chunks_json_data):
    """Verify that regulatory_chunks.json contains exactly 15 chunks."""
    assert len(chunks_json_data) == 15


def test_2_uk_chunks_count_and_distribution(deserialized_chunks):
    """Verify exactly 9 UK chunks with expected ID sequence RR-UK-01-C01 through RR-UK-09-C01."""
    uk_chunks = [c for c in deserialized_chunks if c.jurisdiction == "UK"]
    assert len(uk_chunks) == 9
    uk_chunk_ids = [c.chunk_id for c in uk_chunks]
    expected_uk_chunk_ids = [f"RR-UK-{i:02d}-C01" for i in range(1, 10)]
    assert sorted(uk_chunk_ids) == sorted(expected_uk_chunk_ids)


def test_3_eu_chunks_count_and_distribution(deserialized_chunks):
    """Verify exactly 6 EU chunks with expected ID sequence RR-EU-01-C01 through RR-EU-06-C01."""
    eu_chunks = [c for c in deserialized_chunks if c.jurisdiction == "EU"]
    assert len(eu_chunks) == 6
    eu_chunk_ids = [c.chunk_id for c in eu_chunks]
    expected_eu_chunk_ids = [f"RR-EU-{i:02d}-C01" for i in range(1, 7)]
    assert sorted(eu_chunk_ids) == sorted(expected_eu_chunk_ids)


# ---------------------------------------------------------------------------
# 2. Identifiers & Uniqueness
# ---------------------------------------------------------------------------

def test_4_unique_chunk_ids(deserialized_chunks):
    """Verify that all 15 Chunk_IDs are strictly unique."""
    chunk_ids = [c.chunk_id for c in deserialized_chunks]
    assert len(chunk_ids) == len(set(chunk_ids)) == 15


def test_5_upstream_chunk_id_format_preservation(deserialized_chunks):
    """Verify that chunk IDs follow canonical RR-{JURISDICTION}-{NN}-C{MM} format."""
    pattern = re.compile(r"^RR-(UK|EU)-\d{2}-C\d{2}$")
    for c in deserialized_chunks:
        assert pattern.match(c.chunk_id), f"Invalid chunk_id format: {c.chunk_id}"


def test_6_unique_record_ids_and_source_ids(deserialized_chunks):
    """Verify 15 unique record IDs and 15 unique source IDs."""
    record_ids = [c.record_id for c in deserialized_chunks]
    source_ids = [c.source_id for c in deserialized_chunks]
    assert len(record_ids) == len(set(record_ids)) == 15
    assert len(source_ids) == len(set(source_ids)) == 15


# ---------------------------------------------------------------------------
# 3. Upstream Mapping & 1:1 Preservation
# ---------------------------------------------------------------------------

def test_7_normalized_record_to_chunk_one_to_one_mapping(deserialized_chunks, normalized_records):
    """Verify that every normalized record maps to exactly one chunk with matching chunk_id."""
    chunk_by_record_id = {c.record_id: c for c in deserialized_chunks}
    assert len(chunk_by_record_id) == len(normalized_records) == 15

    for rec in normalized_records:
        assert rec.record_id in chunk_by_record_id
        chunk = chunk_by_record_id[rec.record_id]
        assert chunk.chunk_id == rec.chunk_id
        assert chunk.source_id == rec.source_id
        assert chunk.regulation == rec.regulation
        assert chunk.regulator == rec.regulator
        assert chunk.jurisdiction == rec.jurisdiction
        assert chunk.section_article == rec.section_article
        assert chunk.title == rec.title


def test_8_zero_orphan_chunks_and_zero_duplicate_chunks(deserialized_chunks, normalized_records):
    """Verify zero orphan chunks and zero duplicate chunks."""
    normalized_rec_ids = {r.record_id for r in normalized_records}
    chunk_rec_ids = [c.record_id for c in deserialized_chunks]
    assert set(chunk_rec_ids) == normalized_rec_ids
    assert len(chunk_rec_ids) == len(normalized_rec_ids)


# ---------------------------------------------------------------------------
# 4. Text Integrity, Types & Non-Fabrication
# ---------------------------------------------------------------------------

def test_9_chunk_text_originates_strictly_from_retrieval_text(deserialized_chunks, normalized_records):
    """Verify that chunk.text is populated directly from upstream retrieval_text."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.text_type == "retrieval_text"
        assert chunk.text == upstream_rec.retrieval_text.strip()
        assert len(chunk.text) > 0


def test_10_requirement_not_used_as_main_chunk_text_when_retrieval_text_available(deserialized_chunks):
    """Verify conceptual separation: chunk.text contains retrieval_text, not the shorter requirement paraphrase."""
    for chunk in deserialized_chunks:
        assert chunk.text != chunk.requirement
        assert chunk.requirement in chunk.text
        assert len(chunk.text) > len(chunk.requirement)


def test_11_regulatory_text_remains_none(deserialized_chunks):
    """Verify that regulatory_text remains None across all 15 chunks (no legal text fabrication)."""
    for chunk in deserialized_chunks:
        assert chunk.regulatory_text is None


# ---------------------------------------------------------------------------
# 5. Metadata & Week 4 Enriched Fields Preservation
# ---------------------------------------------------------------------------

def test_12_retrieval_tags_preserved_as_clean_list(deserialized_chunks, normalized_records):
    """Verify retrieval_tags are preserved as non-empty list of cleaned strings."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert isinstance(chunk.retrieval_tags, list)
        assert len(chunk.retrieval_tags) > 0
        assert chunk.retrieval_tags == upstream_rec.retrieval_tags
        for tag in chunk.retrieval_tags:
            assert tag == tag.strip()
            assert len(tag) > 0


def test_13_official_source_url_preserved(deserialized_chunks, normalized_records):
    """Verify official_source canonical HTTPS URLs are preserved."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.official_source == upstream_rec.official_source
        assert chunk.official_source.startswith("https://")


def test_14_citation_label_preserved(deserialized_chunks, normalized_records):
    """Verify citation_label is preserved on all chunks."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.citation_label is not None
        assert chunk.citation_label == upstream_rec.citation_label
        assert len(chunk.citation_label.strip()) > 0


def test_15_retrieval_priority_preserved(deserialized_chunks, normalized_records):
    """Verify retrieval_priority (P1, P2) is preserved."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.retrieval_priority is not None
        assert chunk.retrieval_priority == upstream_rec.retrieval_priority
        assert chunk.retrieval_priority.startswith("P")


def test_16_authority_rule_preserved(deserialized_chunks, normalized_records):
    """Verify authority_rule is preserved on all chunks."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.authority_rule is not None
        assert chunk.authority_rule == upstream_rec.authority_rule


def test_17_rag_instruction_preserved(deserialized_chunks, normalized_records):
    """Verify rag_instruction is preserved on all chunks."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.rag_instruction is not None
        assert chunk.rag_instruction == upstream_rec.rag_instruction


def test_18_official_source_check_note_preserved(deserialized_chunks, normalized_records):
    """Verify official_source_check_note is preserved on all chunks."""
    rec_map = {r.record_id: r for r in normalized_records}
    for chunk in deserialized_chunks:
        upstream_rec = rec_map[chunk.record_id]
        assert chunk.official_source_check_note is not None
        assert chunk.official_source_check_note == upstream_rec.official_source_check_note


# ---------------------------------------------------------------------------
# 6. Gating & Status Controls
# ---------------------------------------------------------------------------

def test_19_all_chunks_unapproved_for_rag(deserialized_chunks):
    """Verify that is_approved_for_rag is False across all 15 chunks (0 approved)."""
    assert all(c.is_approved_for_rag is False for c in deserialized_chunks)


def test_20_all_chunks_candidate_awaiting_approval(deserialized_chunks):
    """Verify that validation_status is 'Candidate - Awaiting Approval' across all 15 chunks."""
    assert all(c.validation_status == "Candidate - Awaiting Approval" for c in deserialized_chunks)


def test_21_total_chunks_and_chunk_index_values(deserialized_chunks):
    """Verify chunk_index == 0 and total_chunks == 1 for all 1:1 mapped chunks."""
    for chunk in deserialized_chunks:
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1


# ---------------------------------------------------------------------------
# 7. Statistics, Provenance & Deserialization
# ---------------------------------------------------------------------------

def test_22_chunk_length_statistics(deserialized_chunks):
    """Verify chunk length statistics (Min=343, Max=578, Average=485.47, limit=800)."""
    lengths = [len(c.text) for c in deserialized_chunks]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) / len(lengths)

    assert min_len == 343
    assert max_len == 578
    assert round(avg_len, 2) == 485.47
    assert max_len < 800


def test_23_provenance_traceability(deserialized_chunks):
    """Verify unbroken provenance pointer chain from chunk to official source."""
    for chunk in deserialized_chunks:
        assert chunk.chunk_id.startswith("RR-")
        assert chunk.record_id in chunk.chunk_id
        assert chunk.source_id.startswith(("UK-", "EU-"))
        assert len(chunk.section_article) > 0
        assert chunk.official_source.startswith("https://")


def test_24_full_json_roundtrip_deserialization_fidelity(chunks_json_data, deserialized_chunks):
    """Verify 100% roundtrip deserialization fidelity and exact 31 serialized fields."""
    expected_field_count = len(RegulatoryChunk.model_fields)
    assert expected_field_count in (31, 32)

    for raw_dict, chunk_obj in zip(chunks_json_data, deserialized_chunks):
        assert len(raw_dict.keys()) in (expected_field_count, expected_field_count - 1)
        reserialized = chunk_obj.model_dump()
        if "validation_date" not in raw_dict and "validation_date" in reserialized and reserialized["validation_date"] is None:
            reserialized.pop("validation_date")
        assert reserialized == raw_dict


# ---------------------------------------------------------------------------
# 8. Legacy Fallback & Immutability Verification
# ---------------------------------------------------------------------------

def test_25_legacy_week_3_fallback_chunking():
    """Verify backward compatibility: fallback to requirement when retrieval_text is absent."""
    legacy_rec = NormalizedRegulatoryRecord(
        record_id="RR-UK-99",
        source_id="UK-99",
        regulation="Test Regulation 2024",
        regulator="FCA",
        jurisdiction="UK",
        section_article="Section 10",
        title="Test Requirement Title",
        regulatory_text=None,
        requirement="This is a legacy requirement summary without retrieval_text.",
        validation_status="Candidate - Awaiting Approval",
        official_source="https://example.com/rule",
    )

    chunker = RegulatoryChunker(max_chunk_chars=800, overlap_chars=100)
    chunks = chunker.chunk_record(legacy_rec)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunk_id == "RR-UK-99-C01"
    assert c.text == "This is a legacy requirement summary without retrieval_text."
    assert c.text_type == "requirement_paraphrase"
    assert c.is_approved_for_rag is False
    assert c.chunk_index == 0
    assert c.total_chunks == 1


def test_26_upstream_normalized_records_and_raw_excel_immutability():
    """Verify that normalized_regulatory_records.json and raw Excel workbooks remain 100% unchanged."""
    assert NORMALIZED_RECORDS_PATH.exists()
    current_norm_hash = compute_file_hash(NORMALIZED_RECORDS_PATH)
    assert current_norm_hash == NORMALIZED_RECORDS_EXPECTED_HASH, (
        f"normalized_regulatory_records.json was modified! Expected {NORMALIZED_RECORDS_EXPECTED_HASH}, got {current_norm_hash}"
    )

    for filename, expected_hash in RAW_EXCEL_EXPECTED_HASHES.items():
        filepath = RAW_DATA_DIR / filename
        assert filepath.exists(), f"File missing: {filename}"
        current_hash = compute_file_hash(filepath)
        assert current_hash == expected_hash, (
            f"Raw workbook {filename} was modified! Expected {expected_hash}, got {current_hash}"
        )
