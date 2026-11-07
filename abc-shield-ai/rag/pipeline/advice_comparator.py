"""Advice comparison engine for ABC Shield.

Provides source-grounded comparison between two advisor advice positions:
- Difference detection (substantive, scope, authority, version, contradiction)
- Regulatory evidence retrieval via existing ChromaDB vector store
- Deterministic citation and provenance tracking
- Regulatory conflict/relationship detection via existing ConflictDetector (CO-001..CO-011)
- Evidence gap detection via GapHandler
- Strict non-adjudication: never selects a winning advisor or declares legal correctness
- Preserves decision=None for downstream human compliance SME disposition.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
import uuid
import re
import logging
from pydantic import BaseModel, Field, ConfigDict

from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.conflict.conflict_detector import ConflictDetector, ConflictFinding, ConflictType
from rag.generation.gap_handler import GapHandler, GapResult, GapType
from rag.generation.citations import CitationBuilder, Citation, ProvenanceRecord

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. Input Models
# ==============================================================================

class AdvisorAdviceItem(BaseModel):
    """Advice record from an individual legal or compliance advisor."""
    model_config = ConfigDict(extra="forbid")

    advice_id: str = Field(..., description="Unique advisor advice identifier (e.g. ADV-001).")
    advice_text: str = Field(..., min_length=1, max_length=4000, description="Natural language advice text from the advisor.")
    advisor_name: Optional[str] = Field(None, description="Optional name or title of the advisor.")
    source_reference: Optional[str] = Field(None, description="Optional regulatory reference or citation claimed by the advisor.")


class AdviceComparisonRequest(BaseModel):
    """Request payload for comparing two advisor advice records."""
    model_config = ConfigDict(extra="forbid")

    comparison_id: Optional[str] = Field(None, description="Optional correlation comparison identifier.")
    request_id: Optional[str] = Field(None, description="Optional upstream request correlation identifier.")
    project_id: Optional[str] = Field(None, description="Optional workspace / tenant context.")
    requirement_ids: Optional[List[str]] = Field(None, description="Optional upstream requirement identifiers.")
    advisor_1: AdvisorAdviceItem = Field(..., description="First advisor advice record.")
    advisor_2: AdvisorAdviceItem = Field(..., description="Second advisor advice record.")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context hints (e.g. jurisdiction, regulatory_area).")


# ==============================================================================
# 2. Difference & Supporting Evidence Models
# ==============================================================================

class ComparisonDifferenceType:
    """Taxonomy of detected advice differences."""
    NO_DIFFERENCE = "NO_DIFFERENCE"
    SUBSTANTIVE_DIFFERENCE = "SUBSTANTIVE_DIFFERENCE"
    SCOPE_DIFFERENCE = "SCOPE_DIFFERENCE"
    AUTHORITY_DIFFERENCE = "AUTHORITY_DIFFERENCE"
    VERSION_DIFFERENCE = "VERSION_DIFFERENCE"
    POTENTIAL_CONTRADICTION = "POTENTIAL_CONTRADICTION"


class AdviceDifference(BaseModel):
    """Structured difference detected between Advisor 1 and Advisor 2."""
    model_config = ConfigDict(extra="forbid")

    difference_type: str = Field(
        ...,
        description="Taxonomy classification: NO_DIFFERENCE, SUBSTANTIVE_DIFFERENCE, SCOPE_DIFFERENCE, AUTHORITY_DIFFERENCE, VERSION_DIFFERENCE, POTENTIAL_CONTRADICTION."
    )
    summary: str = Field(..., description="Neutral factual description of the difference.")
    advisor_1_position: str = Field(..., description="Summary of Advisor 1 stance.")
    advisor_2_position: str = Field(..., description="Summary of Advisor 2 stance.")
    is_contradiction: bool = Field(False, description="Whether this difference represents a potential substantive contradiction.")


class AdviceSupportingEvidence(BaseModel):
    """Assessment of regulatory evidence supporting an advisor advice position."""
    model_config = ConfigDict(extra="forbid")

    advice_id: str = Field(..., description="Identifier of the advisor advice (e.g. ADV-001).")
    advice_text: str = Field(..., description="Advice text evaluated.")
    supporting_chunk_ids: List[str] = Field(default_factory=list, description="Chunk IDs providing factual regulatory context.")
    supporting_source_ids: List[str] = Field(default_factory=list, description="Source IDs providing factual regulatory context.")
    evidence_status: str = Field(..., description="SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, or INSUFFICIENT_EVIDENCE.")
    notes: str = Field(..., description="Neutral factual commentary on evidence backing.")


class ComparisonTraceabilityContext(BaseModel):
    """Traceability metadata linking upstream advice records to comparison output."""
    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., description="Unique comparison correlation identifier.")
    request_id: Optional[str] = Field(None, description="Upstream request correlation identifier.")
    project_id: Optional[str] = Field(None, description="Workspace / tenant context.")
    requirement_ids: List[str] = Field(default_factory=list, description="Upstream requirement IDs.")
    advisor_1_id: str = Field(..., description="Advisor 1 advice ID.")
    advisor_2_id: str = Field(..., description="Advisor 2 advice ID.")
    jurisdiction: Optional[str] = Field(None, description="Applied jurisdiction filter hint.")
    regulatory_area: Optional[str] = Field(None, description="Applied regulatory area hint.")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of execution.")


# ==============================================================================
# 3. Comparison Result Output Model
# ==============================================================================

class AdviceComparisonResult(BaseModel):
    """Unified result packaging the comparison between Advisor 1 and Advisor 2."""
    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., description="Comparison correlation identifier.")
    advisor_1: AdvisorAdviceItem = Field(..., description="Advisor 1 advice record.")
    advisor_2: AdvisorAdviceItem = Field(..., description="Advisor 2 advice record.")
    differences: List[AdviceDifference] = Field(default_factory=list, description="List of differences and contradictions identified.")
    relationships: List[ConflictFinding] = Field(default_factory=list, description="Documented regulatory relationships (CO-001..CO-011) between co-retrieved sources.")
    supporting_evidence: List[AdviceSupportingEvidence] = Field(default_factory=list, description="Evidence support breakdown for each advisor.")
    citations: List[Citation] = Field(default_factory=list, description="Deterministic regulatory citations supporting the analysis.")
    provenance: List[ProvenanceRecord] = Field(default_factory=list, description="Traceable provenance lineage for cited regulatory chunks.")
    evidence_gaps: List[GapResult] = Field(default_factory=list, description="Evidence gaps or limitations identified during comparison.")
    human_review_required: bool = Field(..., description="Explicit flag indicating whether human compliance SME review is mandatory.")
    decision: Optional[str] = Field(
        default=None,
        description="Final compliance decision or advisor selection. Strictly None at RAG comparison stage; reserved for human SME / backend workflow."
    )
    disclaimer: str = Field(
        default=(
            "This comparison provides source-grounded regulatory analysis and factual difference identification. "
            "It does not constitute formal legal or professional advice. It does NOT determine which advisor is "
            "legally or professionally correct. Final legal determinations and compliance disposition remain "
            "the exclusive responsibility of a qualified compliance professional."
        ),
        description="Mandatory non-adjudication disclaimer.",
    )

    traceability: ComparisonTraceabilityContext = Field(..., description="Traceability context.")

    def get_evidence_trace_for_advice(self, advice_id: str) -> Optional[Dict[str, Any]]:
        """Trace an advisor advice item back to its supporting chunks, citations, and provenance."""
        for supp in self.supporting_evidence:
            if supp.advice_id == advice_id:
                matched_citations = [c for c in self.citations if c.chunk_id in supp.supporting_chunk_ids]
                matched_provenance = [p for p in self.provenance if p.chunk_id in supp.supporting_chunk_ids]
                return {
                    "advice_id": supp.advice_id,
                    "advice_text": supp.advice_text,
                    "evidence_status": supp.evidence_status,
                    "supporting_chunk_ids": supp.supporting_chunk_ids,
                    "supporting_source_ids": supp.supporting_source_ids,
                    "citations": matched_citations,
                    "provenance": matched_provenance,
                    "notes": supp.notes,
                }
        return None

    def get_conflict_trace(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Trace a conflict/relationship finding back to its supporting chunks, citations, and provenance."""
        for rel in self.relationships:
            if rel.conflict_id == conflict_id:
                matched_citations = [c for c in self.citations if c.chunk_id in rel.retrieved_chunk_ids]
                matched_provenance = [p for p in self.provenance if p.chunk_id in rel.retrieved_chunk_ids]
                return {
                    "conflict_id": rel.conflict_id,
                    "relationship": rel.relationship,
                    "conflict_type": rel.conflict_type,
                    "source_id_1": rel.source_id_1,
                    "source_id_2": rel.source_id_2,
                    "retrieved_chunk_ids": rel.retrieved_chunk_ids,
                    "retrieved_source_ids": rel.retrieved_source_ids,
                    "citations": matched_citations,
                    "provenance": matched_provenance,
                    "message": rel.message,
                }
        return None

    def get_full_traceability_summary(self) -> Dict[str, Any]:
        """Generate a complete end-to-end traceability summary linking advice, comparison, and regulatory evidence."""
        return {
            "comparison_id": self.comparison_id,
            "request_id": self.traceability.request_id,
            "project_id": self.traceability.project_id,
            "requirement_ids": self.traceability.requirement_ids,
            "advisor_1_id": self.traceability.advisor_1_id,
            "advisor_2_id": self.traceability.advisor_2_id,
            "timestamp": self.traceability.timestamp,
            "advisor_1_evidence": self.get_evidence_trace_for_advice(self.advisor_1.advice_id),
            "advisor_2_evidence": self.get_evidence_trace_for_advice(self.advisor_2.advice_id),
            "conflict_count": len(self.relationships),
            "gap_count": len(self.evidence_gaps),
            "human_review_required": self.human_review_required,
            "decision": self.decision,
            "is_adjudicated": False,
        }


# ==============================================================================
# 4. Difference Detection Logic
# ==============================================================================

def detect_advice_differences(adv_1_text: str, adv_2_text: str) -> List[AdviceDifference]:
    """Deterministically identifies differences and potential contradictions between two advice texts."""
    norm_1 = " ".join(adv_1_text.strip().split()).lower()
    norm_2 = " ".join(adv_2_text.strip().split()).lower()

    # 1. Identical Check
    if norm_1 == norm_2:
        return [
            AdviceDifference(
                difference_type=ComparisonDifferenceType.NO_DIFFERENCE,
                summary="Both advisors provide identical advice text; no substantive difference detected.",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        ]

    differences: List[AdviceDifference] = []

    # 2. Potential Contradiction Detection
    # Polarity opposites (mandatory vs optional, prohibited vs permitted, strict liability vs intent required)
    polarity_pairs = [
        ({"mandatory", "compulsory", "strictly required", "must", "shall", "strict liability"},
         {"optional", "voluntary", "not required", "discretionary", "not mandatory", "exempt"}),
        ({"offence", "unlawful", "illegal", "criminal", "prohibited"},
         {"lawful", "permitted", "allowed", "legal", "not an offence"}),
        ({"strict liability", "no intention required", "intent not required"},
         {"intent required", "intention required", "mens rea", "requires intent", "intent must be proved"}),
        ({"all commercial organisations", "every organisation", "universal"},
         {"only financial institutions", "only public bodies", "exempt organisations"}),
    ]

    is_contradiction = False
    for group_a, group_b in polarity_pairs:
        has_a_in_1 = any(term in norm_1 for term in group_a)
        has_b_in_2 = any(term in norm_2 for term in group_b)
        has_b_in_1 = any(term in norm_1 for term in group_b)
        has_a_in_2 = any(term in norm_2 for term in group_a)

        if (has_a_in_1 and has_b_in_2) or (has_b_in_1 and has_a_in_2):
            is_contradiction = True
            differences.append(
                AdviceDifference(
                    difference_type=ComparisonDifferenceType.POTENTIAL_CONTRADICTION,
                    summary="Potential substantive contradiction detected regarding legal obligations, culpability standards, or operational mandates.",
                    advisor_1_position=adv_1_text,
                    advisor_2_position=adv_2_text,
                    is_contradiction=True,
                )
            )
            break

    # 3. Scope Difference Detection
    # Differing jurisdictions or statutory offence vs commercial procedures
    is_uk_1 = any(k in norm_1 for k in ["uk", "united kingdom", "bribery act 2010", "section 1", "section 2"])
    is_eu_1 = any(k in norm_1 for k in ["eu", "european union", "directive", "member state"])
    is_uk_2 = any(k in norm_2 for k in ["uk", "united kingdom", "bribery act 2010", "section 1", "section 2"])
    is_eu_2 = any(k in norm_2 for k in ["eu", "european union", "directive", "member state"])

    is_offence_1 = any(k in norm_1 for k in ["offence", "prosecution", "criminal", "bribing another"])
    is_proc_1 = any(k in norm_1 for k in ["six principles", "prevention procedures", "adequate procedures", "guidance"])
    is_offence_2 = any(k in norm_2 for k in ["offence", "prosecution", "criminal", "bribing another"])
    is_proc_2 = any(k in norm_2 for k in ["six principles", "prevention procedures", "adequate procedures", "guidance"])

    if (is_uk_1 != is_uk_2 or is_eu_1 != is_eu_2) and not is_contradiction:
        differences.append(
            AdviceDifference(
                difference_type=ComparisonDifferenceType.SCOPE_DIFFERENCE,
                summary="Jurisdictional scope difference identified: advisors address differing legal frameworks or regional jurisdictions.",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        )
    elif ((is_offence_1 and is_proc_2) or (is_proc_1 and is_offence_2)) and not is_contradiction:
        differences.append(
            AdviceDifference(
                difference_type=ComparisonDifferenceType.SCOPE_DIFFERENCE,
                summary="Scope difference identified: one advisor addresses statutory criminal offences while the other addresses commercial prevention procedures.",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        )

    # 4. Authority Difference Detection
    # Primary Parliamentary Act vs Ministry of Justice Guidance / administrative circular
    is_act_1 = any(k in norm_1 for k in ["act of parliament", "statute", "primary act", "bribery act 2010"])
    is_guide_1 = any(k in norm_1 for k in ["ministry of justice", "moj guidance", "guidance document", "statutory guidance"])
    is_act_2 = any(k in norm_2 for k in ["act of parliament", "statute", "primary act", "bribery act 2010"])
    is_guide_2 = any(k in norm_2 for k in ["ministry of justice", "moj guidance", "guidance document", "statutory guidance"])

    if ((is_act_1 and is_guide_2) or (is_guide_1 and is_act_2)) and not is_contradiction:
        differences.append(
            AdviceDifference(
                difference_type=ComparisonDifferenceType.AUTHORITY_DIFFERENCE,
                summary="Authority difference identified: advisors rely on different tiers of regulatory authority (primary Parliamentary legislation vs executive guidance).",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        )

    # 5. Version Difference Detection
    is_version_1 = any(k in norm_1 for k in ["amendment", "amended", "2025 revision", "2012 version", "4amld", "5amld"])
    is_version_2 = any(k in norm_2 for k in ["amendment", "amended", "2025 revision", "2012 version", "4amld", "5amld"])
    if (is_version_1 or is_version_2) and not is_contradiction:
        differences.append(
            AdviceDifference(
                difference_type=ComparisonDifferenceType.VERSION_DIFFERENCE,
                summary="Version/amendment difference identified: advice positions reference differing temporal versions or amendment dates.",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        )

    # 6. Fallback General Substantive Difference
    if not differences:
        differences.append(
            AdviceDifference(
                difference_type=ComparisonDifferenceType.SUBSTANTIVE_DIFFERENCE,
                summary="Substantive difference identified: advisors recommend differing operational procedures or legal interpretations.",
                advisor_1_position=adv_1_text,
                advisor_2_position=adv_2_text,
                is_contradiction=False,
            )
        )

    return differences


# ==============================================================================
# 5. Advice Comparator Engine
# ==============================================================================

class AdviceComparator:
    """RAG-side comparison engine for evaluating two advisor advice positions."""

    def __init__(
        self,
        retriever: Optional[RegulatoryRetriever] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        """Initialize the AdviceComparator reusing existing retrieval and conflict singletons."""
        if retriever is not None and conflict_detector is not None:
            self.retriever = retriever
            self.conflict_detector = conflict_detector
        else:
            from api.dependencies import get_grounded_generator
            gen = get_grounded_generator()
            self.retriever = retriever or gen.retriever
            self.conflict_detector = conflict_detector or gen.conflict_detector

    def compare_advice(
        self,
        advisor_1: AdvisorAdviceItem,
        advisor_2: AdvisorAdviceItem,
        comparison_id: Optional[str] = None,
        request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        requirement_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        jurisdiction: Optional[str] = None,
        regulatory_area: Optional[str] = None,
        filter_approved_only: bool = False,
        top_k: int = 5,
    ) -> AdviceComparisonResult:
        """Execute a source-grounded comparison between Advisor 1 and Advisor 2.

        Integrity Invariants:
        1. Identifies differences, contradictions, scope, authority, and version differences.
        2. Retrieves regulatory evidence using the existing ChromaDB vector store.
        3. Attaches deterministic citations and provenance.
        4. Detects registered regulatory relationships (CO-001..CO-011) via ConflictDetector.
        5. Detects evidence gaps via GapHandler without claiming advice is wrong.
        6. Preserves decision=None and enforces mandatory non-adjudication disclaimer.
        7. Fails closed on tenant isolation (unassigned project_id) and approved-only gating.
        """
        cmp_id = comparison_id.strip() if comparison_id and comparison_id.strip() else f"CMP-{uuid.uuid4()}"
        clean_project_id = project_id.strip() if project_id and project_id.strip() else None

        # Resolve context hints
        resolved_jurisdiction = jurisdiction.strip() if jurisdiction and jurisdiction.strip() else None
        resolved_area = regulatory_area.strip() if regulatory_area and regulatory_area.strip() else None

        if context and isinstance(context, dict):
            if not resolved_jurisdiction:
                jur = context.get("jurisdiction")
                if jur and isinstance(jur, str) and jur.strip():
                    resolved_jurisdiction = jur.strip()
            if not resolved_area:
                area = context.get("regulatory_area")
                if area and isinstance(area, str) and area.strip():
                    resolved_area = area.strip()

        req_ids = [r.strip() for r in requirement_ids if r and isinstance(r, str) and r.strip()] if requirement_ids else []

        logger.info(
            "Executing Advice Comparison [%s] (project_id=%s, adv_1=%s, adv_2=%s, jur=%s, area=%s)",
            cmp_id,
            clean_project_id,
            advisor_1.advice_id,
            advisor_2.advice_id,
            resolved_jurisdiction,
            resolved_area,
        )

        # 1. Detect differences between advisor texts
        differences = detect_advice_differences(advisor_1.advice_text, advisor_2.advice_text)

        # 2. Retrieve supporting regulatory evidence using combined query
        combined_query = f"{advisor_1.advice_text} {advisor_2.advice_text}".strip()
        retrieved_chunks: List[RetrievalResult] = self.retriever.retrieve(
            query=combined_query,
            top_k=top_k,
            jurisdiction=resolved_jurisdiction,
            filter_approved_only=filter_approved_only,
            project_id=clean_project_id,
        )

        # 3. Build deterministic citations and provenance
        is_grounded = len(retrieved_chunks) > 0
        citations, provenance = CitationBuilder.build_citations(
            retrieved_chunks=retrieved_chunks,
            is_grounded=is_grounded,
        )

        # 4. Detect registered regulatory conflicts/relationships among co-retrieved sources
        relationships: List[ConflictFinding] = self.conflict_detector.detect(retrieved_chunks)

        # 5. Evaluate evidence support for each advisor
        supporting_evidence = self._assess_supporting_evidence(
            advisor_1=advisor_1,
            advisor_2=advisor_2,
            retrieved_chunks=retrieved_chunks,
        )

        # 6. Evaluate evidence gaps
        evidence_gaps = self._evaluate_evidence_gaps(
            query=combined_query,
            retrieved_chunks=retrieved_chunks,
            filter_approved_only=filter_approved_only,
            advisor_1=advisor_1,
            advisor_2=advisor_2,
        )

        # 7. Determine Human Review Requirement
        has_contradiction = any(d.is_contradiction for d in differences)
        has_substantive_diff = any(d.difference_type != ComparisonDifferenceType.NO_DIFFERENCE for d in differences)
        has_relationships = len(relationships) > 0
        has_gaps = len(evidence_gaps) > 0
        has_candidate = any(not c.is_approved_for_rag for c in retrieved_chunks) if retrieved_chunks else True

        human_review_required = bool(
            has_contradiction or has_substantive_diff or has_relationships or has_gaps or has_candidate
        )

        resolved_req_id = request_id.strip() if request_id and request_id.strip() else cmp_id

        traceability = ComparisonTraceabilityContext(
            comparison_id=cmp_id,
            request_id=resolved_req_id,
            project_id=clean_project_id,
            requirement_ids=req_ids,
            advisor_1_id=advisor_1.advice_id,
            advisor_2_id=advisor_2.advice_id,
            jurisdiction=resolved_jurisdiction,
            regulatory_area=resolved_area,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return AdviceComparisonResult(
            comparison_id=cmp_id,
            advisor_1=advisor_1,
            advisor_2=advisor_2,
            differences=differences,
            relationships=relationships,
            supporting_evidence=supporting_evidence,
            citations=citations,
            provenance=provenance,
            evidence_gaps=evidence_gaps,
            human_review_required=human_review_required,
            decision=None,  # Strictly None: final compliance decision belongs to human SME
            traceability=traceability,
        )

    def compare_from_request(
        self,
        request: AdviceComparisonRequest,
        filter_approved_only: bool = False,
        top_k: int = 5,
    ) -> AdviceComparisonResult:
        """Execute advice comparison using a validated AdviceComparisonRequest model."""
        return self.compare_advice(
            advisor_1=request.advisor_1,
            advisor_2=request.advisor_2,
            comparison_id=request.comparison_id,
            request_id=request.request_id,
            project_id=request.project_id,
            requirement_ids=request.requirement_ids,
            context=request.context,
            filter_approved_only=filter_approved_only,
            top_k=top_k,
        )

    def _assess_supporting_evidence(
        self,
        advisor_1: AdvisorAdviceItem,
        advisor_2: AdvisorAdviceItem,
        retrieved_chunks: List[RetrievalResult],
    ) -> List[AdviceSupportingEvidence]:
        """Assess which retrieved chunks factually support Advisor 1 and Advisor 2."""
        if not retrieved_chunks:
            return [
                AdviceSupportingEvidence(
                    advice_id=advisor_1.advice_id,
                    advice_text=advisor_1.advice_text,
                    supporting_chunk_ids=[],
                    supporting_source_ids=[],
                    evidence_status="INSUFFICIENT_EVIDENCE",
                    notes="No regulatory evidence was retrieved from the current corpus to evaluate this advice.",
                ),
                AdviceSupportingEvidence(
                    advice_id=advisor_2.advice_id,
                    advice_text=advisor_2.advice_text,
                    supporting_chunk_ids=[],
                    supporting_source_ids=[],
                    evidence_status="INSUFFICIENT_EVIDENCE",
                    notes="No regulatory evidence was retrieved from the current corpus to evaluate this advice.",
                ),
            ]

        results: List[AdviceSupportingEvidence] = []
        for adv in [advisor_1, advisor_2]:
            adv_words = set(re.findall(r"\w+", adv.advice_text.lower()))
            # Remove very common words
            stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "with", "by", "is", "are", "be"}
            meaningful_words = adv_words - stopwords

            matched_chunks: List[RetrievalResult] = []
            for chunk in retrieved_chunks:
                chunk_text_lower = f"{chunk.text} {chunk.title} {chunk.section_article}".lower()
                # Check keyword overlap
                overlap = sum(1 for w in meaningful_words if w in chunk_text_lower)
                if overlap >= 2:
                    matched_chunks.append(chunk)

            chunk_ids = [c.chunk_id for c in matched_chunks]
            source_ids = list(dict.fromkeys(c.source_id for c in matched_chunks))

            if matched_chunks:
                status = "SUPPORTED" if len(matched_chunks) >= 2 else "PARTIALLY_SUPPORTED"
                notes = f"Retrieved regulatory evidence ({', '.join(chunk_ids)}) provides factual context relevant to this advice."
            else:
                status = "INSUFFICIENT_EVIDENCE"
                notes = "Retrieved evidence does not directly corroborate the assertions in this advice position."

            results.append(
                AdviceSupportingEvidence(
                    advice_id=adv.advice_id,
                    advice_text=adv.advice_text,
                    supporting_chunk_ids=chunk_ids,
                    supporting_source_ids=source_ids,
                    evidence_status=status,
                    notes=notes,
                )
            )

        return results

    def _evaluate_evidence_gaps(
        self,
        query: str,
        retrieved_chunks: List[RetrievalResult],
        filter_approved_only: bool,
        advisor_1: AdvisorAdviceItem,
        advisor_2: AdvisorAdviceItem,
    ) -> List[GapResult]:
        """Analyze evidence gaps across the comparison context without claiming either advice is false."""
        gaps: List[GapResult] = []

        # 1. Standard retrieval gap analysis
        gap = GapHandler.analyze_gap(
            query=query,
            retrieved_chunks=retrieved_chunks,
            is_grounded=len(retrieved_chunks) > 0,
            filter_approved_only=filter_approved_only,
        )
        if gap and gap.is_gap:
            gaps.append(gap)

        # 2. Check for missing specific provisions cited in advice (e.g. Section 7)
        combined_text = f"{advisor_1.advice_text} {advisor_2.advice_text}".lower()
        if "section 7" in combined_text and not any("section 7" in (c.section_article or "").lower() for c in retrieved_chunks):
            # Missing Section 7 in canonical corpus
            gaps.append(
                GapResult(
                    is_gap=True,
                    gap_type=GapType.MISSING_SPECIFIC_PROVISION,
                    message="Advice references 'Section 7 (Failure of commercial organisations to prevent bribery)', which is not represented in the ABC Shield corpus.",
                    user_safe_message="Section 7 is not represented in the current ABC Shield regulatory evidence corpus. This reflects corpus coverage limitations rather than proof that the advisor is incorrect.",
                    retrieved_chunk_ids=[c.chunk_id for c in retrieved_chunks],
                    retrieved_record_ids=list(dict.fromkeys(c.record_id for c in retrieved_chunks)),
                    relevant_evidence_count=len(retrieved_chunks),
                    approved_evidence_count=sum(1 for c in retrieved_chunks if c.is_approved_for_rag),
                    has_candidate_evidence=any(not c.is_approved_for_rag for c in retrieved_chunks),
                    requires_human_review=True,
                    coverage_nature="CORPUS_COVERAGE_LIMITATION",
                    recommended_next_action="Consult external primary sources or compliance SME for Section 7 provisions.",
                )
            )

        return gaps


__all__ = [
    "AdvisorAdviceItem",
    "AdviceComparisonRequest",
    "ComparisonDifferenceType",
    "AdviceDifference",
    "AdviceSupportingEvidence",
    "ComparisonTraceabilityContext",
    "AdviceComparisonResult",
    "detect_advice_differences",
    "AdviceComparator",
]
