"""Task 10 RAG evaluation and safety testing framework."""

from rag.evaluation.evaluation_models import (
    EvaluationCase,
    CaseRetrievalResult,
    RetrievalMetrics,
    ExactProvisionAnalysis,
    CaseGroundednessResult,
    GroundednessOutcome,
    CitationEvaluationResult,
    GapEvaluationResult,
    ConflictEvaluationResult,
    SafetyEvaluationResult,
    PromptInjectionResult,
    FailureAnalysisItem,
    AggregateEvaluationReport,
)
from rag.evaluation.evaluation_dataset import EvaluationDatasetValidator
from rag.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.evaluation.generation_evaluator import GenerationEvaluator
from rag.evaluation.safety_evaluator import SafetyEvaluator
from rag.evaluation.evaluation_runner import EvaluationRunner

__all__ = [
    "EvaluationCase",
    "CaseRetrievalResult",
    "RetrievalMetrics",
    "ExactProvisionAnalysis",
    "CaseGroundednessResult",
    "GroundednessOutcome",
    "CitationEvaluationResult",
    "GapEvaluationResult",
    "ConflictEvaluationResult",
    "SafetyEvaluationResult",
    "PromptInjectionResult",
    "FailureAnalysisItem",
    "AggregateEvaluationReport",
    "EvaluationDatasetValidator",
    "RetrievalEvaluator",
    "GenerationEvaluator",
    "SafetyEvaluator",
    "EvaluationRunner",
]
