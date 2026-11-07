"""Generation, citation, GAP, and conflict evaluation module for Task 10.

Implements deterministic rubric checks for response groundedness, citation validity,
GAP classification accuracy, and conflict detection evaluation against the controlled register.
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import logging

from rag.evaluation.evaluation_models import (
    EvaluationCase,
    CaseGroundednessResult,
    GroundednessOutcome,
    CitationEvaluationResult,
    GapEvaluationResult,
    ConflictEvaluationResult,
)
from rag.output.structured_response import StructuredAIResponse, ResponseStatus
from rag.generation.gap_handler import GapType

logger = logging.getLogger(__name__)


class GenerationEvaluator:
    """Evaluates groundedness, citations, GAP handling, and conflict detection."""

    def evaluate_case_groundedness(
        self,
        case: EvaluationCase,
        response: StructuredAIResponse,
    ) -> CaseGroundednessResult:
        """Evaluate groundedness for a single pipeline response using deterministic rubrics."""
        checks_passed: List[str] = []
        checks_failed: List[str] = []

        retrieved_chunk_ids = {e.chunk_id for e in response.retrieved_evidence}
        retrieved_source_ids = {e.source_id for e in response.retrieved_evidence}

        # Check 1: Citation whitelist check
        # If citations exist, every cited chunk MUST be in retrieved_evidence
        cited_chunk_ids = [c.chunk_id for c in response.citations]
        unwhitelisted_citations = [cid for cid in cited_chunk_ids if cid not in retrieved_chunk_ids]
        if unwhitelisted_citations:
            checks_failed.append(f"Unwhitelisted citations found: {unwhitelisted_citations}")
        else:
            checks_passed.append("All citations whitelisted in retrieved evidence")

        # Check 2: Source ID whitelist check
        # All cited source IDs must match retrieved source IDs
        cited_source_ids = [c.source_id for c in response.citations]
        unwhitelisted_sources = [sid for sid in cited_source_ids if sid not in retrieved_source_ids]
        if unwhitelisted_sources:
            checks_failed.append(f"Unwhitelisted sources in citations: {unwhitelisted_sources}")
        else:
            checks_passed.append("All citation source IDs whitelisted")

        # Check 3: Abstention correctness
        # If the case is expected to have a GAP or non-grounded status, ensure system did not claim GROUNDED
        if case.expected_status and case.expected_status != ResponseStatus.GROUNDED.value:
            if response.status == ResponseStatus.GROUNDED:
                checks_failed.append(
                    f"Failed to abstain: expected status '{case.expected_status}', got '{response.status.value}'"
                )
            else:
                checks_passed.append(f"Properly abstained with status '{response.status.value}'")
        else:
            checks_passed.append("Status conforms to grounded expectation")

        # Check 4: Verbatim text non-fabrication check
        # When regulatory_text is null in retrieved evidence, the answer must not falsely claim official verbatim quotes
        has_null_text = any(e.text is None for e in response.retrieved_evidence)
        if has_null_text and "official consolidated verbatim text:" in response.answer.lower():
            checks_failed.append("Claimed official consolidated verbatim text when evidence text was null")
        else:
            checks_passed.append("Paraphrase integrity preserved (no false verbatim claims)")

        # Determine overall outcome
        if case.requires_human_review:
            outcome = GroundednessOutcome.REQUIRES_HUMAN_REVIEW
            details = "Relevance or regulatory interpretation is complex and marked for human SME review."
        elif checks_failed:
            if any("Unwhitelisted" in f or "Failed to abstain" in f for f in checks_failed):
                outcome = GroundednessOutcome.UNSUPPORTED
            else:
                outcome = GroundednessOutcome.PARTIALLY_SUPPORTED
            details = f"Failed checks: {'; '.join(checks_failed)}"
        else:
            outcome = GroundednessOutcome.SUPPORTED
            details = "All deterministic groundedness checks passed successfully."

        return CaseGroundednessResult(
            case_id=case.case_id,
            outcome=outcome,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
            requires_human_review=case.requires_human_review,
        )

    def evaluate_citations(
        self,
        cases_with_responses: List[Tuple[EvaluationCase, StructuredAIResponse]],
    ) -> CitationEvaluationResult:
        """Evaluate citation validity across all evaluated cases.

        Explicitly reports sentence-level precision and recall as NOT_EVALUATED
        in alignment with Task 6 scope.
        """
        total_citations = 0
        valid_citations = 0
        invalid_citations = 0

        for _, response in cases_with_responses:
            retrieved_chunk_ids = {e.chunk_id for e in response.retrieved_evidence}
            for citation in response.citations:
                total_citations += 1
                if citation.chunk_id in retrieved_chunk_ids:
                    valid_citations += 1
                else:
                    invalid_citations += 1

        validity_rate = (
            round(valid_citations / float(total_citations), 4)
            if total_citations > 0
            else 1.0
        )

        notes = (
            "Citation validity rate measures the percentage of generated citations that reference "
            "strictly whitelisted retrieved evidence chunks. Sentence-level citation precision and recall "
            "are explicitly marked NOT_EVALUATED because Task 6 operates on chunk-level provenance "
            "rather than claim-level markup."
        )

        return CitationEvaluationResult(
            total_citations=total_citations,
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
            validity_rate=validity_rate,
            precision_evaluated=False,
            recall_evaluated=False,
            precision_rate=None,
            recall_rate=None,
            notes=notes,
        )

    def evaluate_gaps(
        self,
        cases_with_responses: List[Tuple[EvaluationCase, StructuredAIResponse]],
    ) -> GapEvaluationResult:
        """Evaluate accuracy of GAP taxonomy classifications across cases with expected gaps."""
        total_gap_cases = 0
        correct_classifications = 0
        incorrect_classifications = 0
        false_grounded_count = 0
        details: List[Dict[str, Any]] = []

        for case, response in cases_with_responses:
            if case.expected_gap_type is not None:
                total_gap_cases += 1
                actual_gap_type = (
                    response.gap.gap_type.value
                    if response.gap is not None and response.gap.gap_type is not None
                    else None
                )

                is_correct = actual_gap_type == case.expected_gap_type
                if is_correct:
                    correct_classifications += 1
                else:
                    incorrect_classifications += 1
                    if response.status == ResponseStatus.GROUNDED:
                        false_grounded_count += 1

                details.append({
                    "case_id": case.case_id,
                    "expected_gap_type": case.expected_gap_type,
                    "actual_gap_type": actual_gap_type,
                    "status": response.status.value,
                    "is_correct": is_correct,
                })

        accuracy = (
            round(correct_classifications / float(total_gap_cases), 4)
            if total_gap_cases > 0
            else 1.0
        )

        return GapEvaluationResult(
            total_gap_cases=total_gap_cases,
            correct_classifications=correct_classifications,
            incorrect_classifications=incorrect_classifications,
            accuracy=accuracy,
            false_grounded_count=false_grounded_count,
            details=details,
        )

    def evaluate_conflicts(
        self,
        cases_with_responses: List[Tuple[EvaluationCase, StructuredAIResponse]],
    ) -> ConflictEvaluationResult:
        """Evaluate deterministic regulatory conflict and overlap detection against expected pairs."""
        total_cases_evaluated = 0
        tp_total = 0
        fp_total = 0
        fn_total = 0
        correct_cases = 0
        details: List[Dict[str, Any]] = []

        for case, response in cases_with_responses:
            expected_conflicts = set(case.expected_conflict_ids)
            detected_conflicts = {c.conflict_id for c in response.conflicts}

            # Only evaluate cases where conflicts were either expected or detected
            if expected_conflicts or detected_conflicts:
                total_cases_evaluated += 1
                tp = len(expected_conflicts.intersection(detected_conflicts))
                fp = len(detected_conflicts - expected_conflicts)
                fn = len(expected_conflicts - detected_conflicts)

                tp_total += tp
                fp_total += fp
                fn_total += fn

                is_exact_match = (expected_conflicts == detected_conflicts)
                if is_exact_match:
                    correct_cases += 1

                details.append({
                    "case_id": case.case_id,
                    "expected_conflict_ids": sorted(list(expected_conflicts)),
                    "detected_conflict_ids": sorted(list(detected_conflicts)),
                    "true_positives": tp,
                    "false_positives": fp,
                    "false_negatives": fn,
                    "is_exact_match": is_exact_match,
                })

        pair_precision = (
            round(tp_total / float(tp_total + fp_total), 4)
            if (tp_total + fp_total) > 0
            else 1.0
        )
        pair_recall = (
            round(tp_total / float(tp_total + fn_total), 4)
            if (tp_total + fn_total) > 0
            else 1.0
        )
        classification_accuracy = (
            round(correct_cases / float(total_cases_evaluated), 4)
            if total_cases_evaluated > 0
            else 1.0
        )

        return ConflictEvaluationResult(
            total_cases_evaluated=total_cases_evaluated,
            true_positives=tp_total,
            false_positives=fp_total,
            false_negatives=fn_total,
            pair_precision=pair_precision,
            pair_recall=pair_recall,
            classification_accuracy=classification_accuracy,
            details=details,
        )
