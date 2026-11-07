"""Regulatory document and record chunker.

Prepares chunks for downstream RAG retrieval while strictly preserving 100% of parent
metadata and provenance pointers on every chunk.
"""

from typing import List, Optional
import re

from rag.ingestion.schemas import NormalizedRegulatoryRecord, RegulatoryChunk


class RegulatoryRecordChunker:
    """Chunks normalized regulatory records while preserving metadata hierarchy."""

    def __init__(self, max_chunk_chars: int = 800, overlap_chars: int = 100):
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def _split_text_by_boundaries(self, text: str) -> List[str]:
        """Split text along paragraph or sentence boundaries if exceeding max_chunk_chars."""
        if len(text) <= self.max_chunk_chars:
            return [text]

        # First attempt paragraph splitting
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1 and all(len(p) <= self.max_chunk_chars for p in paragraphs):
            return paragraphs

        # Otherwise split by sentence boundaries while respecting max length
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > self.max_chunk_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sent]
                current_len = sent_len
            else:
                current_chunk.append(sent)
                current_len += sent_len + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]

    def chunk_record(self, record: NormalizedRegulatoryRecord) -> List[RegulatoryChunk]:
        """Create one or more RegulatoryChunks from a NormalizedRegulatoryRecord.

        Prefers Week 4 Retrieval_Text as primary chunk text and preserves upstream Chunk_ID.
        Maintains backward compatibility for legacy records where Retrieval_Text is absent.
        """
        # 1. Determine base chunk text and text_type:
        # Preference: Retrieval_Text (Week 4 composite evidence) -> Regulatory_Text -> Requirement
        if record.retrieval_text and record.retrieval_text.strip():
            raw_text = record.retrieval_text.strip()
            text_type = "retrieval_text"
        elif record.regulatory_text and record.regulatory_text.strip():
            raw_text = record.regulatory_text.strip()
            text_type = "regulatory_text"
        else:
            raw_text = record.requirement.strip()
            text_type = "requirement_paraphrase"

        text_pieces = self._split_text_by_boundaries(raw_text)
        total_chunks = len(text_pieces)

        chunks: List[RegulatoryChunk] = []
        for idx, piece in enumerate(text_pieces):
            # If an upstream Chunk_ID is present and only 1 piece, preserve it exactly
            if record.chunk_id and total_chunks == 1:
                chunk_id = record.chunk_id
            elif record.chunk_id and total_chunks > 1:
                chunk_id = f"{record.chunk_id}-{idx+1:02d}"
            else:
                chunk_suffix = f"-C{idx+1:02d}"
                chunk_id = f"{record.record_id}{chunk_suffix}"

            chunk = RegulatoryChunk(
                chunk_id=chunk_id,
                record_id=record.record_id,
                source_id=record.source_id,
                regulation=record.regulation,
                regulator=record.regulator,
                jurisdiction=record.jurisdiction,
                section_article=record.section_article,
                title=record.title,
                text=piece,
                text_type=text_type,
                requirement=record.requirement,
                regulatory_text=record.regulatory_text,
                summary=record.summary,
                topic=record.topic,
                official_source=record.official_source,
                version_date=record.version_date,
                effective_date=record.effective_date,
                validation_status=record.validation_status,
                validation_date=record.validation_date,
                authority_level=record.authority_level,
                source_type=record.source_type,
                is_approved_for_rag=record.is_approved_for_rag,
                chunk_index=idx,
                total_chunks=total_chunks,
                # Week 4 Enriched Fields
                content_type=record.content_type,
                retrieval_text=record.retrieval_text,
                retrieval_tags=record.retrieval_tags or [],
                citation_label=record.citation_label,
                retrieval_priority=record.retrieval_priority,
                authority_rule=record.authority_rule,
                rag_instruction=record.rag_instruction,
                official_source_check_note=record.official_source_check_note,
            )
            chunks.append(chunk)

        return chunks

    def chunk_all(self, records: List[NormalizedRegulatoryRecord]) -> List[RegulatoryChunk]:
        """Chunk a list of normalized regulatory records."""
        all_chunks: List[RegulatoryChunk] = []
        for rec in records:
            all_chunks.extend(self.chunk_record(rec))
        return all_chunks


# Convenient alias
RegulatoryChunker = RegulatoryRecordChunker
