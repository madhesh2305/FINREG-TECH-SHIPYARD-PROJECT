"""Regulatory Data Ingestion Module for ABC Shield / FinRegTech ShipYard.

Exposes loader, normalizer, validator, chunker, and end-to-end ingestion pipeline runner.
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import logging

from rag.ingestion.schemas import (
    DataDictionaryEntry,
    SourceRegisterRecord,
    SourceControlRecord,
    ConflictOverlapRecord,
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
    RAGRuleRecord,
    OfficialVerificationRecord,
    CANONICAL_SME_APPROVED_STATUSES,
    is_sme_approved,
)
from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator, IngestionValidationReport
from rag.ingestion.chunker import RegulatoryRecordChunker, RegulatoryChunker

logger = logging.getLogger(__name__)


def run_ingestion_pipeline(
    raw_data_dir: Path,
    processed_data_dir: Path
) -> Dict[str, Any]:
    """Execute end-to-end regulatory data ingestion and export processed JSON artifacts.

    Args:
        raw_data_dir: Path containing the 3 raw Excel workbooks.
        processed_data_dir: Path to write processed JSON artifacts.

    Returns:
        Summary dictionary with counts, validation report, and sample records.
    """
    raw_dir = Path(raw_data_dir)
    proc_dir = Path(processed_data_dir)
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Excel workbooks
    loader = ExcelWorkbookLoader(raw_dir)
    data_dict = loader.load_data_dictionary()
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()
    validation_notes = loader.load_validation_notes()
    conflict_records = loader.load_conflict_overlap()

    # 2. Normalize and join source metadata
    normalizer = RegulatoryDataNormalizer(sources)
    normalized_records = normalizer.normalize_all(raw_records)

    # 3. Validate normalized records
    validator = RegulatoryDataValidator(sources)
    val_report = validator.validate_records(normalized_records)

    # 4. Chunk normalized records
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(normalized_records)

    # 5. Save processed JSON artifacts
    normalized_json_path = proc_dir / "normalized_regulatory_records.json"
    chunks_json_path = proc_dir / "regulatory_chunks.json"

    with open(normalized_json_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in normalized_records], f, indent=2, ensure_ascii=False)

    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

    return {
        "status": "COMPLETED",
        "data_dictionary_fields_count": len(data_dict),
        "source_register_count": len(sources),
        "raw_regulatory_records_count": len(raw_records),
        "normalized_records_count": len(normalized_records),
        "chunks_count": len(chunks),
        "conflict_overlap_count": len(conflict_records),
        "validation_report": val_report.model_dump(),
        "normalized_output_file": str(normalized_json_path),
        "chunks_output_file": str(chunks_json_path),
    }


def export_normalized_records(
    raw_data_dir: Path = Path("data/raw"),
    output_path: Path = Path("data/processed/normalized_regulatory_records.json")
) -> List[NormalizedRegulatoryRecord]:
    """Load, normalize, validate, and write normalized regulatory records to JSON.

    This function specifically regenerates normalized_regulatory_records.json
    without executing chunking or touching regulatory_chunks.json or ChromaDB.

    Args:
        raw_data_dir: Path containing the raw Excel workbooks.
        output_path: Target path for normalized_regulatory_records.json.

    Returns:
        List of 15 validated NormalizedRegulatoryRecord instances.
    """
    raw_dir = Path(raw_data_dir)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    loader = ExcelWorkbookLoader(raw_dir)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records(normalized)
    if report.has_critical_errors:
        raise ValueError(f"Normalization failed validation with critical errors: {report.issues}")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in normalized], f, indent=2, ensure_ascii=False)

    return normalized


def export_regulatory_chunks(
    normalized_path: Path = Path("data/processed/normalized_regulatory_records.json"),
    output_path: Path = Path("data/processed/regulatory_chunks.json"),
) -> List[RegulatoryChunk]:
    """Generate and export RAG chunks from normalized regulatory records to JSON.

    Consumes normalized_regulatory_records.json and regenerates regulatory_chunks.json
    using Retrieval_Text and upstream Chunk_IDs, without rebuilding ChromaDB.

    Args:
        normalized_path: Path to normalized_regulatory_records.json.
        output_path: Target path for regulatory_chunks.json.

    Returns:
        List of 15 validated RegulatoryChunk instances.
    """
    norm_file = Path(normalized_path)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if not norm_file.exists():
        raise FileNotFoundError(f"Normalized records file not found at: {norm_file}")

    with open(norm_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = [NormalizedRegulatoryRecord(**item) for item in data]
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(records)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

    return chunks


__all__ = [
    "DataDictionaryEntry",
    "SourceRegisterRecord",
    "SourceControlRecord",
    "ConflictOverlapRecord",
    "NormalizedRegulatoryRecord",
    "RegulatoryChunk",
    "RAGRuleRecord",
    "OfficialVerificationRecord",
    "CANONICAL_SME_APPROVED_STATUSES",
    "is_sme_approved",
    "ExcelWorkbookLoader",
    "RegulatoryDataNormalizer",
    "RegulatoryDataValidator",
    "IngestionValidationReport",
    "RegulatoryRecordChunker",
    "RegulatoryChunker",
    "run_ingestion_pipeline",
    "export_normalized_records",
    "export_regulatory_chunks",
]
