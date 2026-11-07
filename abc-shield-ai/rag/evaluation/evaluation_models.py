"""Data models for Task 10 RAG evaluation and safety testing.

Defines schemas for evaluation benchmark cases, retrieval metrics, groundedness
rubrics, citation validity metrics, conflict detection evaluations, safety checks,
prompt-injection test outcomes, and comprehensive aggregate reports.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GroundednessOutcome(str, Enum):
    """Rubric outcomes for response groundedness evaluation."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class EvaluationCase(BaseModel):
    """Controlled benchmark evaluation case representing a compliance or adversarial scenario."""

    case_id: str = Field(..., description="Unique case identifier (e.g. CASE-01)")
    query: str = Field(..., description="Input query string for the pipeline")
    category: str = Field(..., description="Category code (A through O)")
    expected_record_ids: List[str] = Field(
        default_factory=list,
        description="Controlled expected relevant record IDs (empty for out-of-scope/adversarial)"
    )
    expected_source_ids: List[str] = Field(
        default_factory=list,
        description="Controlled expected source register IDs"
    )
    expected_status: Optional[str] = Field(
        None,
        description="Expected ResponseStatus (e.g. 'GROUNDED', 'OUT_OF_SCOPE', 'INSUFFICIENT_EVIDENCE')"
    )
    expected_gap_type: Optional[str] = Field(
        None,
        description="Expected GapType if evidence is deficient or out of scope"
    )
    expected_conflict_ids: List[str] = Field(
        default_factory=list,
        description="Expected documented Conflict IDs if relationship should be detected"
    )
    expected_behavior: str = Field(..., description="Description of expected safe system behavior")
    requires_human_review: bool = Field(
        False,
        description="Whether regulatory relevance is ambiguous and requires SME review"
    )
    notes: Optional[str] = Field(None, description="Contextual, legal, or test notes")


class CaseRetrievalResult(BaseModel):
    """Detailed retrieval metrics for a single evaluation case."""

    case_id: str
    query: str
    category: str
    retrieved_chunk_ids: List[str]
    retrieved_record_ids: List[str]
    expected_record_ids: List[str]
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    hit_rate_at_k: Dict[int, float]
    reciprocal_rank: float
    is_zero_expected: bool = False


class RetrievalMetrics(BaseModel):
    """Aggregate record-level retrieval metrics evaluated across applicable cases."""

    evaluated_cases: int
    zero_expected_cases: int
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    hit_rate_at_k: Dict[int, float]
    mrr: float


class ExactProvisionAnalysis(BaseModel):
    """Investigation of exact statutory provision retrieval rank (e.g. Bribery Act Section 1)."""

    query: str
    target_record_id: str
    target_chunk_id: str
    rank_in_retrieval: Optional[int]
    retrieved_at_k1: bool
    retrieved_at_k3: bool
    retrieved_at_k5: bool
    similarity_score: Optional[float]
    top_ranked_chunk_id: str
    top_ranked_regulation: str
    notes: str


class CaseGroundednessResult(BaseModel):
    """Groundedness evaluation outcome for a single generated answer."""

    case_id: str
    outcome: GroundednessOutcome
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)
    details: str
    requires_human_review: bool = False


class CitationEvaluationResult(BaseModel):
    """Citation validity and completeness metrics."""

    total_citations: int
    valid_citations: int
    invalid_citations: int
    validity_rate: float
    precision_evaluated: bool = False
    recall_evaluated: bool = False
    precision_rate: Optional[float] = None
    recall_rate: Optional[float] = None
    notes: str


class GapEvaluationResult(BaseModel):
    """GAP detection evaluation metrics."""

    total_gap_cases: int
    correct_classifications: int
    incorrect_classifications: int
    accuracy: float
    false_grounded_count: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


class ConflictEvaluationResult(BaseModel):
    """Conflict and overlap detection metrics against controlled 11-pair register."""

    total_cases_evaluated: int
    true_positives: int
    false_positives: int
    false_negatives: int
    pair_precision: float
    pair_recall: float
    classification_accuracy: float
    details: List[Dict[str, Any]] = Field(default_factory=list)


class SafetyEvaluationResult(BaseModel):
    """Approval status preservation and non-adjudication safety evaluation."""

    candidate_status_preserved: bool
    approved_only_filtering_correct: bool
    zero_fabricated_citations: bool
    zero_fabricated_conflicts: bool
    zero_legal_conflict_resolutions: bool
    safe_refusal_when_unavailable_text: bool
    checks_passed_count: int
    checks_failed_count: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


class PromptInjectionResult(BaseModel):
    """Test outcome for adversarial prompt-injection attacks."""

    case_id: str
    provider_tested: str
    attack_type: str
    query: str
    safe_behavior_observed: bool
    observed_answer: str
    details: str


class FailureAnalysisItem(BaseModel):
    """Structured record of an evaluation failure or limitation."""

    case_id: str
    category: str
    expected_behavior: str
    actual_behavior: str
    responsible_module: str
    severity: str
    recommended_future_improvement: str


class AggregateEvaluationReport(BaseModel):
    """Comprehensive evaluation report unifying all evaluation dimensions."""

    evaluation_timestamp: str
    dataset_version: str
    total_cases: int
    reviewed_cases: int
    unreviewed_cases: int
    provider_tested: str
    embedding_model: str
    chromadb_collection: str
    retrieval_metrics: RetrievalMetrics
    exact_provision_analysis: ExactProvisionAnalysis
    groundedness_summary: Dict[str, int]
    citation_metrics: CitationEvaluationResult
    gap_metrics: GapEvaluationResult
    conflict_metrics: ConflictEvaluationResult
    safety_metrics: SafetyEvaluationResult
    prompt_injection_results: List[PromptInjectionResult]
    failure_analysis: List[FailureAnalysisItem]
    cases_requiring_human_review: List[str]
    limitations: List[str]
