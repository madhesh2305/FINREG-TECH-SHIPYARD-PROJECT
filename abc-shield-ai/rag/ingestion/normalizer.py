"""Normalizer mapping raw Excel regulatory records into typed internal representations.

Performs metadata join with the Source Register without modifying or overwriting
source values, preserving provenance and distinguishing requirements from verbatim
regulatory text and structured retrieval text blocks.
"""

from typing import List, Dict, Optional, Any
import logging

from rag.ingestion.schemas import (
    SourceRegisterRecord,
    NormalizedRegulatoryRecord,
)

logger = logging.getLogger(__name__)


class RegulatoryDataNormalizer:
    """Normalizes raw regulatory records and enriches them with Source Register metadata."""

    def __init__(self, source_register: List[SourceRegisterRecord]):
        # Index sources by Source ID for O(1) join
        self.sources_by_id: Dict[str, SourceRegisterRecord] = {
            s.source_id.strip(): s for s in source_register if s.source_id
        }

    def normalize_record(self, raw: Dict[str, Optional[Any]]) -> NormalizedRegulatoryRecord:
        """Normalize a single raw regulatory record dictionary into NormalizedRegulatoryRecord."""
        record_id = (str(raw.get("Record_ID") or "")).strip()
        source_id = (str(raw.get("Source_ID") or "")).strip()

        if not record_id:
            raise ValueError("Record_ID is missing in raw regulatory record")
        if not source_id:
            raise ValueError(f"Source_ID is missing for record {record_id}")

        source_meta = self.sources_by_id.get(source_id)
        if not source_meta:
            logger.warning("No matching Source Register entry found for Source ID: %s in record: %s", source_id, record_id)

        # 1. Strict distinction: verbatim text vs requirement paraphrase vs retrieval text
        # In legacy workbooks, regulatory_text is not provided (None).
        # In canonical 25 corpus, exact verbatim quote is in Exact_Source_Extract.
        # Requirement strictly maps to Requirement or Structured_Summary (never falling back to Exact_Source_Extract).
        exact_extract = raw.get("Exact_Source_Extract")
        verbatim_text = raw.get("Regulatory_Text") or exact_extract
        raw_requirement = raw.get("Requirement") or raw.get("Structured_Summary")

        if not raw_requirement:
            raise ValueError(f"Requirement/Structured_Summary is mandatory but missing for record {record_id}")

        # 2. Combine or fallback for official source URL
        # Preference: Official_Source_URL (new Week 4) -> Official_URL (canonical) -> Source_URL (legacy Week 3) -> source register link
        official_url = raw.get("Official_Source_URL") or raw.get("Official_URL") or raw.get("Source_URL") or (source_meta.official_link_reference if source_meta else None)

        # 3. Topic, authority level, and source type
        topic = raw.get("Topic") or (source_meta.topic if source_meta else None)
        # Authority_Level on record sheet takes precedence if provided, else inherit from source register
        authority_level = raw.get("Authority_Level") or (source_meta.authority_level if source_meta else None)
        source_type = (source_meta.source_type if source_meta else None) or raw.get("Source_Type")
        source_notes = source_meta.notes_limitations if source_meta else None

        # 4. Dates handling
        version_date = raw.get("Version_Date") or raw.get("Version") or (source_meta.version_last_updated if source_meta else None)
        effective_date = (
            raw.get("Effective_Date")
            or raw.get("Publication_Date")
            or (source_meta.effective_date if source_meta and source_meta.effective_date else None)
            or (source_meta.publication_effective_date if source_meta else None)
        )
        validation_date = raw.get("Validation_Date") or raw.get("Validation Date")

        # 5. Validation status
        raw_status = str(raw.get("Status") or "").strip()
        raw_val_status = str(raw.get("Validation_Status") or "").strip()
        notes = str(raw.get("Notes_Limitations") or "").strip()

        # Fail-closed provisional RAG governance (Option A: DEC-01 OPEN & RAG-014)
        # Extraction / RAG testing approval is distinct from authoritative legal compliance SME approval.
        # Discloses provisional RAG integration while preserving pending SME validation gating.
        if raw_status == "Approved for RAG Integration" or (raw_val_status == "Approved" and "pending sme validation" in notes.lower()):
            validation_status = "Approved for RAG Integration - Pending SME Validation"
        elif raw_val_status:
            validation_status = raw_val_status
        elif raw_status:
            validation_status = raw_status
        elif source_meta:
            validation_status = source_meta.status
        else:
            validation_status = "Candidate - Awaiting Approval"

        # 6. Parse semicolon-delimited Retrieval_Tags into List[str]
        raw_tags = raw.get("Retrieval_Tags")
        retrieval_tags: List[str] = []
        if raw_tags:
            if isinstance(raw_tags, list):
                retrieval_tags = [str(t).strip() for t in raw_tags if str(t).strip()]
            elif isinstance(raw_tags, str):
                retrieval_tags = [t.strip() for t in raw_tags.split(";") if t.strip()]
        elif topic:
            retrieval_tags = [t.strip() for t in topic.replace(";", ",").split(",") if t.strip()]

        # 7. Title handling (fallback to Topic or Section_Article if Title column is absent)
        title = raw.get("Title") or raw.get("Topic") or raw.get("Section_Article") or ""

        # 8. Week 4 RAG-Specific Fields and fallbacks
        chunk_id = raw.get("Chunk_ID") or f"{record_id}-C01"
        source_name = raw.get("Source_Name") or (source_meta.source_name if source_meta else "")
        sec_art = raw.get("Section_Article") or ""
        citation_label = raw.get("Citation_Label") or f"{source_id} | {source_name} | {sec_art}"

        retrieval_text = raw.get("Retrieval_Text")
        if not retrieval_text:
            parts = [
                f"Source: {source_id} - {source_name}",
                f"Reference: {sec_art}",
                f"Topic: {topic or 'General'}",
                f"Requirement: {raw_requirement}",
            ]
            if raw.get("Notes_Limitations"):
                parts.append(f"Notes: {raw.get('Notes_Limitations')}")
            retrieval_text = "\n".join(parts)

        # 9. Build normalized record with all Week 3, Week 4, and Canonical handover fields
        normalized = NormalizedRegulatoryRecord(
            record_id=record_id,
            source_id=source_id,
            regulation=raw.get("Regulation_Name") or source_name,
            regulator=raw.get("Issuing_Authority") or (source_meta.issuing_authority if source_meta else ""),
            jurisdiction=raw.get("Jurisdiction") or (source_meta.jurisdiction if source_meta else ""),
            section_article=sec_art,
            title=title,
            regulatory_text=verbatim_text,
            requirement=str(raw_requirement),
            summary=raw.get("Summary") or raw.get("Structured_Summary"),
            topic=topic,
            official_source=official_url,
            version_date=version_date,
            effective_date=effective_date,
            validation_status=validation_status,
            validation_date=validation_date,
            applicability=raw.get("Applicability"),
            relevance_to_project=raw.get("Relevance_to_Project"),
            notes_limitations=raw.get("Notes_Limitations"),
            source_type=source_type,
            authority_level=authority_level,
            source_notes=source_notes,
            # Week 4 RAG-Specific Fields
            chunk_id=chunk_id,
            content_type=raw.get("Content_Type") or source_type,
            retrieval_text=retrieval_text,
            retrieval_tags=retrieval_tags,
            citation_label=citation_label,
            retrieval_priority=raw.get("Retrieval_Priority") or (source_meta.extraction_priority if source_meta else None),
            authority_rule=raw.get("Authority_Rule"),
            rag_instruction=raw.get("RAG_Instruction"),
            official_source_check_note=raw.get("Official_Source_Check_Note"),
        )

        return normalized

    def normalize_all(self, raw_records: List[Dict[str, Optional[Any]]]) -> List[NormalizedRegulatoryRecord]:
        """Normalize a collection of raw records."""
        normalized_records = []
        for raw in raw_records:
            normalized_records.append(self.normalize_record(raw))
        return normalized_records
