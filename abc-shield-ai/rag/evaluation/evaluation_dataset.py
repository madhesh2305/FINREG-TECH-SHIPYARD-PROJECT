"""Dataset loader and dynamic reference validator for Task 10 evaluation.

Dynamically derives valid regulatory record IDs, source IDs, and conflict IDs
from normalized records and the controlled conflict register without hardcoding ranges.
"""

from typing import List, Dict, Any, Set, Optional
from pathlib import Path
import json
import logging

from rag.evaluation.evaluation_models import EvaluationCase
from rag.output.structured_response import ResponseStatus
from rag.generation.gap_handler import GapType
from rag.conflict.conflict_detector import ConflictDetector

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = Path("data/evaluation/evaluation_cases.json")
DEFAULT_NORMALIZED_PATH = Path("data/processed/normalized_regulatory_records.json")


class EvaluationDatasetValidator:
    """Dynamically validates evaluation cases against actual corpus records and conflict registers."""

    def __init__(
        self,
        normalized_records_path: Optional[Path] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        self.normalized_path = normalized_records_path or DEFAULT_NORMALIZED_PATH
        self._valid_record_ids: Set[str] = set()
        self._valid_source_ids: Set[str] = set()
        self._valid_conflict_ids: Set[str] = set()
        self._conflict_detector = conflict_detector

        self._load_dynamic_references()

    def _load_dynamic_references(self) -> None:
        """Derive valid IDs dynamically from the ingested records and conflict register."""
        if self.normalized_path.exists():
            try:
                with open(self.normalized_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    for rec in records:
                        if "record_id" in rec and rec["record_id"]:
                            self._valid_record_ids.add(rec["record_id"])
                        if "source_id" in rec and rec["source_id"]:
                            self._valid_source_ids.add(rec["source_id"])
            except Exception as e:
                logger.error(f"Error loading normalized records from {self.normalized_path}: {e}")

        # Derive conflict IDs from ConflictDetector
        try:
            detector = self._conflict_detector or ConflictDetector()
            for conf in detector.conflict_records:
                self._valid_conflict_ids.add(conf.conflict_id)
        except Exception as e:
            logger.error(f"Error loading conflict records: {e}")

    @property
    def valid_record_ids(self) -> Set[str]:
        """Dynamically derived valid regulatory record IDs."""
        return set(self._valid_record_ids)

    @property
    def valid_source_ids(self) -> Set[str]:
        """Dynamically derived valid source IDs."""
        return set(self._valid_source_ids)

    @property
    def valid_conflict_ids(self) -> Set[str]:
        """Dynamically derived valid conflict IDs."""
        return set(self._valid_conflict_ids)

    def load_cases(self, dataset_path: Optional[Path] = None) -> List[EvaluationCase]:
        """Load benchmark cases from JSON file."""
        path = dataset_path or DEFAULT_DATASET_PATH
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_cases = json.load(f)

        cases: List[EvaluationCase] = []
        for item in raw_cases:
            cases.append(EvaluationCase(**item))
        return cases

    def validate_case(self, case: EvaluationCase) -> List[str]:
        """Validate a single evaluation case against dynamic references.

        Returns a list of error strings; empty if perfectly valid.
        """
        errors = []

        # Validate expected_record_ids against dynamic set
        for rec_id in case.expected_record_ids:
            if rec_id not in self._valid_record_ids:
                errors.append(f"Invalid expected_record_id '{rec_id}' (not found in normalized records)")

        # Validate expected_source_ids against dynamic set
        for src_id in case.expected_source_ids:
            if src_id not in self._valid_source_ids:
                errors.append(f"Invalid expected_source_id '{src_id}' (not found in normalized records)")

        # Validate expected_conflict_ids against dynamic set
        for conf_id in case.expected_conflict_ids:
            if conf_id not in self._valid_conflict_ids:
                errors.append(f"Invalid expected_conflict_id '{conf_id}' (not found in conflict register)")

        # Validate expected_status against ResponseStatus enum
        if case.expected_status:
            valid_statuses = {s.value for s in ResponseStatus}
            if case.expected_status not in valid_statuses:
                errors.append(f"Invalid expected_status '{case.expected_status}'. Must be one of {valid_statuses}")

        # Validate expected_gap_type against GapType enum
        if case.expected_gap_type:
            valid_gap_types = {g.value for g in GapType}
            if case.expected_gap_type not in valid_gap_types:
                errors.append(f"Invalid expected_gap_type '{case.expected_gap_type}'. Must be one of {valid_gap_types}")

        # Validate category is in A..O
        valid_categories = {chr(c) for c in range(ord('A'), ord('P'))}
        if case.category not in valid_categories:
            errors.append(f"Invalid category '{case.category}'. Must be between A and O.")

        return errors

    def validate_all(self, cases: List[EvaluationCase]) -> Dict[str, Any]:
        """Validate an entire list of evaluation cases.

        Returns summary statistics and any validation errors found.
        """
        errors_by_case: Dict[str, List[str]] = {}
        category_counts: Dict[str, int] = {}
        review_count = 0

        for case in cases:
            # Category distribution
            category_counts[case.category] = category_counts.get(case.category, 0) + 1

            if case.requires_human_review:
                review_count += 1

            errs = self.validate_case(case)
            if errs:
                errors_by_case[case.case_id] = errs

        is_valid = len(errors_by_case) == 0

        return {
            "is_valid": is_valid,
            "total_cases": len(cases),
            "valid_cases": len(cases) - len(errors_by_case),
            "invalid_cases": len(errors_by_case),
            "errors": errors_by_case,
            "category_distribution": category_counts,
            "requires_human_review_count": review_count,
            "dynamic_record_count": len(self._valid_record_ids),
            "dynamic_source_count": len(self._valid_source_ids),
            "dynamic_conflict_count": len(self._valid_conflict_ids),
        }
