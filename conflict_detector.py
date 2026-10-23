"""Deterministic regulatory conflict and overlap detection layer for ABC Shield.

Identifies documented regulatory relationships and differences (scope, authority,
version/amendment) between retrieved evidence sources based strictly on the
controlled Conflict Overlap dataset.

Safety & Integrity Principles:
1. 100% Deterministic: Detection is based strictly on matching retrieved source IDs
   against the controlled Conflict Overlap register. No LLM is used.
2. Both Sources Required: A conflict/overlap is reported only when BOTH Source_ID_1
   and Source_ID_2 of a documented pair are present in the retrieved evidence.
3. No Legal Conflict Resolution: The system identifies documented relationships and
   differences; it does NOT decide which regulation overrides another, which source
   wins, or which regulation is legally controlling.
4. Preserved Metadata: Retains original Excel relationship, comparisons, scope differences,
   authority differences, version differences, conflict status, and RAG usage guidance.
5. Approval Separation: Candidate/unapproved validation status is preserved and remains
   strictly independent from conflict detection.
"""

from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging
from pydantic import BaseModel, Field

from rag.ingestion.schemas import ConflictOverlapRecord
from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.retrieval.retriever import RetrievalResult

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """Normalized classification taxonomy for regulatory relationships."""

    CONFLICT = "CONFLICT"
    OVERLAP = "OVERLAP"
    SCOPE_DIFFERENCE = "SCOPE_DIFFERENCE"
    AUTHORITY_DIFFERENCE = "AUTHORITY_DIFFERENCE"
    VERSION_DIFFERENCE = "VERSION_DIFFERENCE"
    UNKNOWN_RELATIONSHIP = "UNKNOWN_RELATIONSHIP"


def classify_relationship(relationship: str, conflict_status: str) -> ConflictType:
    """Deterministically maps Excel relationship & status strings to normalized ConflictType.

    The original relationship string is always preserved in ConflictFinding.relationship.
    """
    rel_lower = (relationship or "").strip().lower()
    stat_lower = (conflict_status or "").strip().lower()

    # 1. Version / Amendment differences (e.g. EU-04 vs EU-05 in CO-010)
    if "amendment" in rel_lower or "version" in rel_lower or "amendment" in stat_lower or "version" in stat_lower:
        return ConflictType.VERSION_DIFFERENCE

    # 2. Direct substantive conflicts (if any, excluding negative statements)
    if "conflict" in rel_lower and not any(neg in rel_lower for neg in ["no conflict", "not conflict", "no direct conflict"]):
        return ConflictType.CONFLICT
    if "conflict" in stat_lower and not any(neg in stat_lower for neg in ["no conflict", "not conflict", "no direct conflict"]):
        return ConflictType.CONFLICT

    # 3. Overlaps (complementary, partial, same regulator, legal act + index, policy alignment)
    if "overlap" in rel_lower:
        return ConflictType.OVERLAP

    # 4. Authority differences
    if "authority" in rel_lower:
        return ConflictType.AUTHORITY_DIFFERENCE

    # 5. Scope differences
    if "scope" in rel_lower:
        return ConflictType.SCOPE_DIFFERENCE

    return ConflictType.UNKNOWN_RELATIONSHIP


class ConflictFinding(BaseModel):
    """Structured finding of a documented regulatory conflict or overlap."""

    conflict_id: str = Field(..., description="Unique conflict/overlap ID from register (e.g. CO-001)")
    topic: str = Field(..., description="Regulatory topic area")
    source_id_1: str = Field(..., description="First source identifier (e.g. UK-01)")
    source_1: str = Field(..., description="First source name")
    source_id_2: str = Field(..., description="Second source identifier (e.g. UK-02)")
    source_2: str = Field(..., description="Second source name")
    relationship: str = Field(..., description="Original relationship text from Excel")
    conflict_type: ConflictType = Field(..., description="Normalized conflict/overlap classification")
    requirement_comparison: Optional[str] = Field(None, description="Documented requirement comparison")
    scope_difference: Optional[str] = Field(None, description="Documented scope difference")
    authority_difference: Optional[str] = Field(None, description="Documented authority difference")
    version_effective_date_difference: Optional[str] = Field(None, description="Documented version/effective date difference")
    conflict_status: str = Field(..., description="Original conflict status from register")
    rag_use: Optional[str] = Field(None, description="RAG usage guidance from register")
    retrieved_source_ids: List[str] = Field(default_factory=list, description="Source IDs present in retrieval")
    retrieved_chunk_ids: List[str] = Field(default_factory=list, description="Chunk IDs from retrieved evidence supporting this pair")
    both_sources_retrieved: bool = Field(True, description="Whether both sources are present in retrieved evidence")
    source_1_validation_status: Optional[str] = Field(None, description="Validation status of source 1")
    source_2_validation_status: Optional[str] = Field(None, description="Validation status of source 2")
    source_1_is_approved_for_rag: bool = Field(False, description="Whether source 1 is approved for authoritative RAG")
    source_2_is_approved_for_rag: bool = Field(False, description="Whether source 2 is approved for authoritative RAG")
    is_approved_for_rag: bool = Field(False, description="True only if BOTH sources are approved for authoritative RAG")
    requires_human_review: bool = Field(True, description="Whether compliance SME review is required to assess this relationship")
    source_1_jurisdiction: Optional[str] = Field(None, description="Jurisdiction of Source 1 (e.g. UK, EU)")
    source_2_jurisdiction: Optional[str] = Field(None, description="Jurisdiction of Source 2 (e.g. UK, EU)")
    source_1_authority_level: Optional[str] = Field(None, description="Authority level of Source 1 (A, B, C, D)")
    source_2_authority_level: Optional[str] = Field(None, description="Authority level of Source 2 (A, B, C, D)")
    message: str = Field(..., description="Neutral factual description of documented relationship and differences")


class ConflictDetector:
    """Deterministic regulatory conflict and overlap detector."""

    def __init__(
        self,
        raw_data_dir: Optional[Path] = None,
        conflict_records: Optional[List[ConflictOverlapRecord]] = None,
    ):
        """Initialize the conflict detector with controlled Conflict Overlap records.

        Args:
            raw_data_dir: Optional path to data/raw directory.
            conflict_records: Optional list of ConflictOverlapRecord instances for testing.
        """
        if conflict_records is not None:
            self.conflict_records = list(conflict_records)
        else:
            data_dir = raw_data_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "raw")
            loader = ExcelWorkbookLoader(data_dir)
            self.conflict_records = loader.load_conflict_overlap()

        # Sort deterministically by conflict_id
        self.conflict_records.sort(key=lambda r: r.conflict_id)
        logger.info("ConflictDetector initialized with %d documented conflict/overlap records.", len(self.conflict_records))

    def detect(self, retrieved_chunks: List[RetrievalResult]) -> List[ConflictFinding]:
        """Detect documented regulatory relationships among retrieved evidence chunks.

        Integrity Rules:
        1. If retrieved_chunks is empty -> returns [].
        2. Gathers unique source IDs from retrieved chunks.
        3. Only reports a finding if BOTH source_id_1 and source_id_2 are present
           in the retrieved evidence.
        4. Deduplicates findings so each conflict pair appears at most once per conflict_id.
        5. Does not resolve conflicts or claim one regulation overrides another.
        6. Preserves candidate validation status and approval flags.
        7. Operates strictly in-memory without calling an LLM or vector database.

        Args:
            retrieved_chunks: List of RetrievalResult objects from vector retrieval.

        Returns:
            List of ConflictFinding objects ordered deterministically by conflict_id.
        """
        if not retrieved_chunks:
            return []

        # Map each source_id to its retrieved chunks
        source_to_chunks: Dict[str, List[RetrievalResult]] = {}
        for chunk in retrieved_chunks:
            source_to_chunks.setdefault(chunk.source_id, []).append(chunk)

        retrieved_source_ids: Set[str] = set(source_to_chunks.keys())
        findings: List[ConflictFinding] = []

        for record in self.conflict_records:
            s1 = record.source_id_1
            s2 = record.source_id_2

            # Check if BOTH sources are present in the retrieved evidence
            has_s1 = s1 in retrieved_source_ids
            has_s2 = s2 in retrieved_source_ids

            if not (has_s1 and has_s2):
                # One-sided retrieval or neither retrieved -> do not report active finding
                continue

            chunks_1 = source_to_chunks[s1]
            chunks_2 = source_to_chunks[s2]

            # Preserve retrieved chunk order for traceable provenance
            chunk_ids_present = [
                c.chunk_id for c in retrieved_chunks
                if c.source_id in (s1, s2)
            ]

            s1_chunk = chunks_1[0] if chunks_1 else None
            s2_chunk = chunks_2[0] if chunks_2 else None

            s1_status = s1_chunk.validation_status if s1_chunk else "Unknown"
            s2_status = s2_chunk.validation_status if s2_chunk else "Unknown"

            s1_jurisdiction = s1_chunk.jurisdiction if s1_chunk else None
            s2_jurisdiction = s2_chunk.jurisdiction if s2_chunk else None

            s1_authority = getattr(s1_chunk, "authority_level", None) if s1_chunk else None
            s2_authority = getattr(s2_chunk, "authority_level", None) if s2_chunk else None

            s1_approved = all(c.is_approved_for_rag for c in chunks_1) if chunks_1 else False
            s2_approved = all(c.is_approved_for_rag for c in chunks_2) if chunks_2 else False
            both_approved = s1_approved and s2_approved

            conflict_type = classify_relationship(record.relationship, record.conflict_status)

            # Construct strictly neutral and non-adjudicative message distinguishing relationship types
            if conflict_type == ConflictType.VERSION_DIFFERENCE:
                rel_desc = "a documented version/amendment relationship"
            elif conflict_type == ConflictType.OVERLAP:
                rel_desc = "a documented regulatory overlap"
            elif conflict_type == ConflictType.CONFLICT:
                rel_desc = "a documented regulatory conflict"
            elif conflict_type == ConflictType.SCOPE_DIFFERENCE:
                rel_desc = "a documented scope difference"
            elif conflict_type == ConflictType.AUTHORITY_DIFFERENCE:
                rel_desc = "a documented authority difference"
            else:
                rel_desc = "a documented relationship"

            msg = (
                f"Retrieved evidence contains {rel_desc} between {s1} ({record.source_1}) "
                f"and {s2} ({record.source_2}). The Conflict Overlap register identifies the relationship as: "
                f"'{record.relationship}'. Documented differences in scope, authority, and version are reported "
                f"as registered. No legal conflict resolution is made by this system."
            )

            finding = ConflictFinding(
                conflict_id=record.conflict_id,
                topic=record.topic,
                source_id_1=s1,
                source_1=record.source_1,
                source_id_2=s2,
                source_2=record.source_2,
                relationship=record.relationship,
                conflict_type=conflict_type,
                requirement_comparison=record.requirement_comparison,
                scope_difference=record.scope_difference,
                authority_difference=record.authority_difference,
                version_effective_date_difference=record.version_effective_date_difference,
                conflict_status=record.conflict_status,
                rag_use=record.rag_use,
                retrieved_source_ids=[s1, s2],
                retrieved_chunk_ids=chunk_ids_present,
                both_sources_retrieved=True,
                source_1_validation_status=s1_status,
                source_2_validation_status=s2_status,
                source_1_is_approved_for_rag=s1_approved,
                source_2_is_approved_for_rag=s2_approved,
                is_approved_for_rag=both_approved,
                requires_human_review=True,
                source_1_jurisdiction=s1_jurisdiction,
                source_2_jurisdiction=s2_jurisdiction,
                source_1_authority_level=s1_authority,
                source_2_authority_level=s2_authority,
                message=msg,
            )
            findings.append(finding)

        return findings
