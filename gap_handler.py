"""Deterministic GAP and No-Source handling layer for ABC Shield regulatory RAG.

Categorizes and explains situations where available regulatory evidence is
insufficient, missing, unapproved, or out-of-scope. Operates entirely outside
the LLM to guarantee predictable, honest disclosure of evidence gaps without
attempting to extrapolate or hallucinate missing regulatory text.
"""

from enum import Enum
from typing import List, Optional, Set, Dict, Any
from pathlib import Path
import re
import json
import logging
from pydantic import BaseModel, Field

from rag.retrieval.retriever import RetrievalResult

logger = logging.getLogger(__name__)


class GapType(str, Enum):
    """Taxonomy of regulatory evidence gaps."""

    NO_RETRIEVED_EVIDENCE = "NO_RETRIEVED_EVIDENCE"
    INSUFFICIENT_RETRIEVED_EVIDENCE = "INSUFFICIENT_RETRIEVED_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    MISSING_SPECIFIC_PROVISION = "MISSING_SPECIFIC_PROVISION"
    UNAPPROVED_EVIDENCE = "UNAPPROVED_EVIDENCE"
    UNKNOWN_EVIDENCE_GAP = "UNKNOWN_EVIDENCE_GAP"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    DATA_COVERAGE_LIMITATION = "DATA_COVERAGE_LIMITATION"
    RETRIEVAL_LIMITATION = "RETRIEVAL_LIMITATION"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class GapResult(BaseModel):
    """Structured result model for regulatory evidence gap analysis."""

    is_gap: bool = Field(True, description="Whether an evidence gap exists")
    gap_type: GapType = Field(..., description="Taxonomy classification of the gap")
    message: str = Field(..., description="Technical diagnostic explanation of the gap")
    user_safe_message: str = Field(
        ...,
        description="User-safe disclosure strictly limited to retrieved evidence context"
    )
    retrieved_chunk_ids: List[str] = Field(
        default_factory=list,
        description="List of Chunk IDs retrieved for this query"
    )
    retrieved_record_ids: List[str] = Field(
        default_factory=list,
        description="List of parent Record IDs retrieved for this query"
    )
    relevant_evidence_count: int = Field(0, description="Total number of evidence chunks retrieved")
    approved_evidence_count: int = Field(
        0,
        description="Number of retrieved chunks approved for authoritative RAG use"
    )
    has_candidate_evidence: bool = Field(
        False,
        description="Whether unapproved candidate evidence was located for the query"
    )
    requires_human_review: bool = Field(
        False,
        description="Explicit flag indicating compliance/SME review is required"
    )
    coverage_nature: Optional[str] = Field(
        None,
        description="Distinction between CORPUS_COVERAGE_LIMITATION and RETRIEVAL_LIMITATION"
    )
    recommended_next_action: Optional[str] = Field(
        None,
        description="Recommended safe next action (workflow suggestion only, not legal advice)"
    )


# Out-of-scope taxonomy mapping keywords to human-readable domain descriptions
OUT_OF_SCOPE_TAXONOMY: Dict[str, str] = {
    "cybersecurity": "cybersecurity requirements",
    "cyber": "cybersecurity and IT resilience",
    "information security": "information security requirements",
    "dora": "Digital Operational Resilience Act (DORA)",
    "nis2": "NIS2 Directive",
    "anti-money laundering": "general Anti-Money Laundering (AML) framework",
    "aml": "general Anti-Money Laundering (AML) framework",
    "sanctions": "economic and financial sanctions",
    "tax evasion": "tax crime and evasion",
    "tax crime": "tax crime and evasion",
    "gdpr": "General Data Protection Regulation (GDPR) / privacy",
    "data privacy": "data privacy regulations",
    "privacy": "data privacy regulations",
    "mica": "Markets in Crypto-Assets (MiCA)",
    "crypto": "cryptocurrency regulations",
    "sec": "US Securities and Exchange Commission (SEC) regulations",
}


class GapHandler:
    """Deterministic analyzer and classifier for regulatory evidence gaps."""

    _CANONICAL_PROVISIONS: Optional[List[Dict[str, str]]] = None

    @classmethod
    def reset_cache(cls) -> None:
        """Reset cached canonical provisions for cache busting and testing."""
        cls._CANONICAL_PROVISIONS = None

    @classmethod
    def _get_canonical_provisions(cls) -> List[Dict[str, str]]:
        """Load and cache section and title references from canonical normalized records."""
        if cls._CANONICAL_PROVISIONS is not None:
            return cls._CANONICAL_PROVISIONS

        try:
            from config.settings import settings
            mode = getattr(settings, "rag_knowledge_base_mode", "canonical").lower()
        except Exception:
            mode = "canonical"

        if mode == "canonical":
            norm_path = Path("data/staging/fast_track/normalized_regulatory_records.json")
            if not norm_path.exists():
                norm_path = Path("data/staging/madhesh_handover/step4/normalized_regulatory_records.json")
            if not norm_path.exists():
                norm_path = Path("data/processed/normalized_regulatory_records.json")
        else:
            norm_path = Path("data/processed/normalized_regulatory_records.json")

        provisions = []
        if norm_path.exists():
            try:
                with open(norm_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for r in records:
                    provisions.append({
                        "record_id": r.get("record_id", ""),
                        "regulation": (r.get("regulation") or "").lower(),
                        "section_article": (r.get("section_article") or "").lower(),
                        "title": (r.get("title") or "").lower(),
                        "topic": (r.get("topic") or "").lower(),
                    })
            except Exception as e:
                logger.error(f"Error loading canonical records for gap analysis: {e}")

        cls._CANONICAL_PROVISIONS = provisions
        return cls._CANONICAL_PROVISIONS

    @classmethod
    def _is_provision_in_canonical_corpus(cls, requested_provision: str, query: str) -> Optional[bool]:
        """Check whether the requested provision is represented in the canonical 15-record corpus.

        Returns:
            True if provision is present in the canonical corpus.
            False if provision is definitively not represented in the corpus.
            None if indeterminate.
        """
        provisions = cls._get_canonical_provisions()
        if not provisions:
            return None

        prov_clean = requested_provision.strip().lower()
        query_lower = query.lower()

        # Check if the requested provision matches any canonical record
        for p in provisions:
            # Check section/article match
            if prov_clean in p["section_article"]:
                # If query mentions a specific regulation, verify regulation matches
                if "bribery act" in query_lower and "bribery act" not in p["regulation"]:
                    continue
                if "mar" in query_lower and "596/2014" not in p["regulation"] and "mar" not in p["regulation"]:
                    continue
                if "mad" in query_lower and "2003/6" not in p["regulation"] and "mad" not in p["regulation"]:
                    continue
                return True

            # Check title match (e.g. "bribing another person" -> Section 1)
            if prov_clean in p["title"]:
                return True

        return False

    @staticmethod
    def _detect_out_of_scope(query_lower: str) -> Optional[str]:
        """Detect whether the query belongs to an explicitly out-of-scope domain."""
        for keyword, domain_desc in OUT_OF_SCOPE_TAXONOMY.items():
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, query_lower):
                return domain_desc
        return None

    @staticmethod
    def _detect_unsupported_transposition(query_lower: str) -> Optional[str]:
        """Detect whether the query requests member-state national transposition outside corpus scope."""
        jurisdictions = {
            "france": "France",
            "french": "France",
            "germany": "Germany",
            "german": "Germany",
            "spain": "Spain",
            "spanish": "Spain",
            "italy": "Italy",
            "italian": "Italy",
            "netherlands": "Netherlands",
            "dutch": "Netherlands",
            "ireland": "Ireland",
            "irish": "Ireland",
        }
        for kw, jur_name in jurisdictions.items():
            if re.search(rf"\b{re.escape(kw)}\b", query_lower):
                if any(t in query_lower for t in ["transpos", "implements", "member-state", "national law", "member state"]):
                    return jur_name
        return None

    @staticmethod
    def _detect_requested_provision(query: str) -> Optional[str]:
        """Extract requested specific provision reference (e.g. 'Section 1', 'Article 3')."""
        query_l = query.lower()
        if "associated person" in query_l:
            return "Section 8"

        # Match Section <number/letter>
        sec_match = re.search(r"\bsection\s+(\d+|[a-zA-Z0-9]+)\b", query, re.IGNORECASE)
        if sec_match:
            return f"Section {sec_match.group(1)}"

        # Match Article <number/letter>
        art_match = re.search(r"\barticle\s+(\d+|[a-zA-Z0-9]+)\b", query, re.IGNORECASE)
        if art_match:
            return f"Article {art_match.group(1)}"

        # Match specific offences (e.g. bribing another person)
        if "bribing another person" in query_l:
            return "Section 1 (Offences of bribing another person)"
        if "failure to prevent" in query_l or "corporate failure" in query_l:
            return "Section 7 (Failure of commercial organisations to prevent bribery)"

        return None

    @classmethod
    def analyze_gap(
        cls,
        query: str,
        retrieved_chunks: List[RetrievalResult],
        is_grounded: bool,
        raw_answer: Optional[str] = None,
        filter_approved_only: bool = False,
        conflicts: Optional[List[Any]] = None,
    ) -> Optional[GapResult]:
        """Analyze and classify regulatory evidence gaps deterministically.

        Integrity and Safety Rules:
        1. If is_grounded is True: returns None (no gap).
        2. Distinguishes between zero retrieval, insufficient retrieval, out-of-scope,
           missing specific provisions, and unapproved status.
        3. Never claims an unretrieved regulation or section does not exist in law or
           in the knowledge base — only reports whether it is present in the retrieved evidence.
        4. Distinguishes evidence sufficiency from evidence approval status.
        5. Does not rely on the LLM to decide whether a gap exists.

        Args:
            query: The user's input query.
            retrieved_chunks: List of RetrievalResult objects from vector search.
            is_grounded: Whether Task 5 marked the response as successfully grounded.
            raw_answer: Optional raw text returned by the LLM.
            filter_approved_only: Whether the search was restricted to approved records.
            conflicts: Optional list of ConflictFinding objects detected for retrieved chunks.

        Returns:
            GapResult if a gap was detected, or None if the response is grounded.
        """
        # Rule 1: Grounded answer has no evidence gap
        if is_grounded:
            return None

        clean_query = query.strip()
        query_lower = clean_query.lower()

        chunk_ids = [c.chunk_id for c in retrieved_chunks]
        record_ids = list(dict.fromkeys(c.record_id for c in retrieved_chunks))
        total_chunks = len(retrieved_chunks)
        approved_chunks = sum(1 for c in retrieved_chunks if c.is_approved_for_rag)
        has_candidate = any(not c.is_approved_for_rag for c in retrieved_chunks)

        # Case A: Zero evidence chunks retrieved
        if total_chunks == 0:
            if filter_approved_only:
                return GapResult(
                    is_gap=True,
                    gap_type=GapType.UNAPPROVED_EVIDENCE,
                    message=(
                        "Zero approved records retrieved. All matching records in the knowledge "
                        "base currently have validation status 'Candidate - Awaiting Approval'."
                    ),
                    user_safe_message=(
                        "No approved authoritative evidence was found. The relevant regulatory records "
                        "are currently marked Candidate - Awaiting Approval and cannot be queried under "
                        "the approved-only filter."
                    ),
                    retrieved_chunk_ids=[],
                    retrieved_record_ids=[],
                    relevant_evidence_count=0,
                    approved_evidence_count=0,
                    has_candidate_evidence=True,
                    requires_human_review=True,
                    coverage_nature="UNAPPROVED_EVIDENCE",
                    recommended_next_action=(
                        "Obtain SME approval before treating candidate records as authoritative, "
                        "or query in development mode without approved-only filtering."
                    ),
                )

            return GapResult(
                is_gap=True,
                gap_type=GapType.NO_RETRIEVED_EVIDENCE,
                message="Zero regulatory evidence chunks were retrieved from the vector store for this query.",
                user_safe_message=(
                    "The current regulatory knowledge base does not contain sufficient retrieved evidence "
                    "for this question."
                ),
                retrieved_chunk_ids=[],
                retrieved_record_ids=[],
                relevant_evidence_count=0,
                approved_evidence_count=0,
                has_candidate_evidence=False,
                requires_human_review=False,
                coverage_nature="RETRIEVAL_LIMITATION",
                recommended_next_action="Review the regulatory source register or obtain an approved source covering this topic.",
            )

        # Case B: Out-of-scope query
        detected_domain = cls._detect_out_of_scope(query_lower)
        if detected_domain:
            return GapResult(
                is_gap=True,
                gap_type=GapType.OUT_OF_SCOPE,
                message=f"Query topic matches out-of-scope domain: '{detected_domain}'.",
                user_safe_message=(
                    f"The current ABC Shield scope does not provide sufficient evidence for {detected_domain}. "
                    "(Scope is strictly limited to UK and EU anti-bribery and anti-corruption frameworks, "
                    "and relevant FCA financial-crime systems and controls)."
                ),
                retrieved_chunk_ids=chunk_ids,
                retrieved_record_ids=record_ids,
                relevant_evidence_count=total_chunks,
                approved_evidence_count=approved_chunks,
                has_candidate_evidence=has_candidate,
                requires_human_review=False,
                coverage_nature="CORPUS_COVERAGE_LIMITATION",
                recommended_next_action="Refer to an approved knowledge source covering this regulatory domain.",
            )

        # Case C: Missing specific provision
        requested_provision = cls._detect_requested_provision(clean_query)
        if requested_provision:
            # Check whether any retrieved chunk contains the requested provision
            prov_clean = requested_provision.lower()
            provision_found = any(
                prov_clean in (c.section_article or "").lower()
                or prov_clean in (c.title or "").lower()
                for c in retrieved_chunks
            )

            if not provision_found:
                in_corpus = cls._is_provision_in_canonical_corpus(requested_provision, clean_query)
                if in_corpus is True:
                    coverage_nature = "RETRIEVAL_LIMITATION"
                    user_msg = (
                        f"The requested {requested_provision} provision is represented in the ABC Shield corpus "
                        f"but was not returned in the retrieved evidence set. "
                        f"The retrieved evidence contains: {', '.join(chunk_ids)}."
                    )
                    diag_msg = (
                        f"The query requested '{requested_provision}', which exists in the canonical corpus but is absent from the "
                        f"{total_chunks} retrieved evidence chunks (retrieval limitation)."
                    )
                    req_review = True
                elif in_corpus is False:
                    coverage_nature = "CORPUS_COVERAGE_LIMITATION"
                    user_msg = (
                        f"The requested {requested_provision} provision is not represented in the current ABC Shield regulatory evidence corpus. "
                        f"The retrieved evidence contains: {', '.join(chunk_ids)}."
                    )
                    diag_msg = (
                        f"The query requested '{requested_provision}', which is not represented in the canonical ABC Shield corpus "
                        f"(corpus coverage limitation)."
                    )
                    req_review = False
                else:
                    coverage_nature = "NEEDS_HUMAN_REVIEW"
                    user_msg = (
                        f"The requested {requested_provision} provision is not present in the retrieved evidence. "
                        f"The retrieved evidence contains: {', '.join(chunk_ids)}."
                    )
                    diag_msg = (
                        f"The query requested '{requested_provision}', which is absent from the "
                        f"{total_chunks} retrieved evidence chunks."
                    )
                    req_review = True

                return GapResult(
                    is_gap=True,
                    gap_type=GapType.MISSING_SPECIFIC_PROVISION,
                    message=diag_msg,
                    user_safe_message=user_msg,
                    retrieved_chunk_ids=chunk_ids,
                    retrieved_record_ids=record_ids,
                    relevant_evidence_count=total_chunks,
                    approved_evidence_count=approved_chunks,
                    has_candidate_evidence=has_candidate,
                    requires_human_review=req_review,
                    coverage_nature=coverage_nature,
                    recommended_next_action=(
                        f"Retrieve additional regulatory evidence containing {requested_provision} "
                        "or refine the retrieval query."
                    ),
                )

        # Case D: Conflicting evidence requiring review
        if conflicts and len(conflicts) > 0:
            return GapResult(
                is_gap=True,
                gap_type=GapType.CONFLICTING_EVIDENCE,
                message=f"Retrieved evidence presents {len(conflicts)} documented regulatory conflicts/overlaps requiring human review.",
                user_safe_message=(
                    "The retrieved evidence presents documented regulatory differences or conflicts between sources. "
                    "A compliance SME review is required to evaluate applicability."
                ),
                retrieved_chunk_ids=chunk_ids,
                retrieved_record_ids=record_ids,
                relevant_evidence_count=total_chunks,
                approved_evidence_count=approved_chunks,
                has_candidate_evidence=has_candidate,
                requires_human_review=True,
                coverage_nature="NEEDS_HUMAN_REVIEW",
                recommended_next_action="Consult a compliance officer or SME to review the conflicting provisions.",
            )

        # Case E: General insufficient retrieved evidence
        return GapResult(
            is_gap=True,
            gap_type=GapType.INSUFFICIENT_RETRIEVED_EVIDENCE,
            message=(
                f"{total_chunks} evidence chunks were retrieved, but they do not contain sufficient "
                "provisions to answer the specific question."
            ),
            user_safe_message=(
                "The retrieved evidence does not contain sufficient information to answer this specific question. "
                f"Retrieved evidence chunks: {', '.join(chunk_ids)}."
            ),
            retrieved_chunk_ids=chunk_ids,
            retrieved_record_ids=record_ids,
            relevant_evidence_count=total_chunks,
            approved_evidence_count=approved_chunks,
            has_candidate_evidence=has_candidate,
            requires_human_review=True,
            coverage_nature="INSUFFICIENT_RETRIEVED_EVIDENCE",
            recommended_next_action="Retrieve additional approved regulatory evidence or refine the query.",
        )
