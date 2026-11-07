"""Comprehensive evaluation orchestrator for Task 10.

Executes retrieval, grounded generation, citation validity, GAP accuracy,
conflict detection, and safety testing across all controlled benchmark cases,
producing both machine-readable JSON and human-readable Markdown reports.
"""

from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime, timezone
import json
import logging

from rag.evaluation.evaluation_models import (
    EvaluationCase,
    AggregateEvaluationReport,
    FailureAnalysisItem,
    GroundednessOutcome,
)
from rag.evaluation.evaluation_dataset import EvaluationDatasetValidator
from rag.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.evaluation.generation_evaluator import GenerationEvaluator
from rag.evaluation.safety_evaluator import SafetyEvaluator
from rag.generation.grounded_generator import GroundedGenerator
from rag.output.structured_response import StructuredAIResponse, ResponseStatus

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("data/evaluation/results")


class EvaluationRunner:
    """Orchestrates end-to-end evaluation and report generation."""

    def __init__(
        self,
        validator: Optional[EvaluationDatasetValidator] = None,
        retrieval_evaluator: Optional[RetrievalEvaluator] = None,
        generation_evaluator: Optional[GenerationEvaluator] = None,
        safety_evaluator: Optional[SafetyEvaluator] = None,
        generator: Optional[GroundedGenerator] = None,
        output_dir: Optional[Path] = None,
    ):
        self.validator = validator or EvaluationDatasetValidator()
        self.generator = generator or GroundedGenerator()
        self.retrieval_evaluator = retrieval_evaluator or RetrievalEvaluator(self.generator.retriever)
        self.generation_evaluator = generation_evaluator or GenerationEvaluator()
        self.safety_evaluator = safety_evaluator or SafetyEvaluator(self.generator)
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    def run_benchmark(
        self,
        dataset_path: Optional[Path] = None,
        provider_name: str = "MockLLMProvider",
    ) -> AggregateEvaluationReport:
        """Execute the complete evaluation benchmark across all cases."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load cases
        cases = self.validator.load_cases(dataset_path)
        logger.info(f"Loaded {len(cases)} evaluation cases.")

        # 2. Evaluate retrieval
        retrieval_metrics, case_retrieval_results = self.retrieval_evaluator.evaluate_all(cases)
        exact_provision = self.retrieval_evaluator.analyze_exact_provision()

        # 3. Generate pipeline responses
        cases_with_responses: List[Tuple[EvaluationCase, StructuredAIResponse]] = []
        for case in cases:
            filter_approved = (case.category == "L")
            resp = self.generator.generate_structured_response(
                query=case.query,
                top_k=5,
                filter_approved_only=filter_approved,
            )
            cases_with_responses.append((case, resp))

        all_responses = [resp for _, resp in cases_with_responses]

        # 4. Evaluate groundedness
        groundedness_summary = {outcome.value: 0 for outcome in GroundednessOutcome}
        case_groundedness_list = []
        for case, resp in cases_with_responses:
            g_res = self.generation_evaluator.evaluate_case_groundedness(case, resp)
            case_groundedness_list.append(g_res)
            groundedness_summary[g_res.outcome.value] += 1

        # 5. Evaluate citations
        citation_metrics = self.generation_evaluator.evaluate_citations(cases_with_responses)

        # 6. Evaluate GAPs
        gap_metrics = self.generation_evaluator.evaluate_gaps(cases_with_responses)

        # 7. Evaluate conflicts
        conflict_metrics = self.generation_evaluator.evaluate_conflicts(cases_with_responses)

        # 8. Evaluate safety & prompt injections
        safety_metrics, prompt_results = self.safety_evaluator.run_safety_suite(
            all_responses=all_responses,
            provider_name=provider_name,
        )

        # 9. Failure Analysis
        failure_analysis: List[FailureAnalysisItem] = []

        # Analyze Section 1 retrieval rank limitation
        if not exact_provision.retrieved_at_k1:
            failure_analysis.append(
                FailureAnalysisItem(
                    case_id="CASE-01 / CASE-11",
                    category="E (Exact Provision)",
                    expected_behavior="Section 1 active bribery provision (RR-UK-01) ranked at Rank 1",
                    actual_behavior=f"Ranked at #{exact_provision.rank_in_retrieval} behind {exact_provision.top_ranked_chunk_id}",
                    responsible_module="Task 4 (Retrieval / Dense Bi-Encoder)",
                    severity="Medium",
                    recommended_future_improvement="Implement hybrid retrieval (BM25 lexical + MiniLM dense vector) with RRF (Reciprocal Rank Fusion).",
                )
            )

        # Analyze GAP misses if any
        for detail in gap_metrics.details:
            if not detail["is_correct"]:
                failure_analysis.append(
                    FailureAnalysisItem(
                        case_id=detail["case_id"],
                        category="GAP / No-Source Handling",
                        expected_behavior=f"Expected GAP '{detail['expected_gap_type']}'",
                        actual_behavior=f"Got actual GAP '{detail['actual_gap_type']}' with status '{detail['status']}'",
                        responsible_module="Task 7 (GapHandler)",
                        severity="Low",
                        recommended_future_improvement="Refine regex and semantic intent classification rules in GapHandler.",
                    )
                )

        # Cases requiring human review
        review_case_ids = [c.case_id for c in cases if c.requires_human_review]
        reviewed_count = len(cases) - len(review_case_ids)

        limitations = [
            "Current ChromaDB collection contains 15 candidate chunks; results reflect candidate dataset baseline.",
            "All 15 regulatory records remain 'Candidate - Awaiting Approval'; approved-only queries intentionally return zero records.",
            "Sentence-level citation precision/recall are marked NOT_EVALUATED because Task 6 operates on chunk-level provenance.",
            "Semantic similarity with all-MiniLM-L6-v2 struggles with exact statutory section precision compared to general guidance texts.",
            "Safety and prompt-injection testing was conducted against MockLLMProvider; external LLMs (OpenAI, Ollama) require independent runtime evaluation.",
        ]

        report = AggregateEvaluationReport(
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_version="1.0-controlled",
            total_cases=len(cases),
            reviewed_cases=reviewed_count,
            unreviewed_cases=len(review_case_ids),
            provider_tested=provider_name,
            embedding_model="all-MiniLM-L6-v2",
            chromadb_collection="regulatory_records",
            retrieval_metrics=retrieval_metrics,
            exact_provision_analysis=exact_provision,
            groundedness_summary=groundedness_summary,
            citation_metrics=citation_metrics,
            gap_metrics=gap_metrics,
            conflict_metrics=conflict_metrics,
            safety_metrics=safety_metrics,
            prompt_injection_results=prompt_results,
            failure_analysis=failure_analysis,
            cases_requiring_human_review=review_case_ids,
            limitations=limitations,
        )

        # 10. Write output files
        self._write_json_report(report)
        self._write_markdown_summary(report)

        return report

    def _write_json_report(self, report: AggregateEvaluationReport) -> None:
        """Write aggregate report to JSON."""
        json_path = self.output_dir / "evaluation_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        logger.info(f"Wrote evaluation results to {json_path}")

    def _write_markdown_summary(self, report: AggregateEvaluationReport) -> None:
        """Write executive summary in Markdown format."""
        md_path = self.output_dir / "evaluation_summary.md"

        ret = report.retrieval_metrics
        cit = report.citation_metrics
        gap = report.gap_metrics
        conf = report.conflict_metrics
        safe = report.safety_metrics
        epa = report.exact_provision_analysis

        md = f"""# ABC Shield — Task 10 Evaluation & Safety Report

**Timestamp**: {report.evaluation_timestamp}  
**Dataset Version**: {report.dataset_version}  
**Total Benchmark Cases**: {report.total_cases} (Evaluated: {report.total_cases}, Requiring SME Review: {len(report.cases_requiring_human_review)})  
**Provider Tested**: `{report.provider_tested}`  
**Embedding Model**: `{report.embedding_model}`  
**ChromaDB Collection**: `{report.chromadb_collection}`  

---

## 1. Retrieval Performance Metrics (Record-Level Deduplicated)

Evaluated across {ret.evaluated_cases} applicable cases ({ret.zero_expected_cases} zero-expected cases handled safely without division by zero).

| Metric | K = 1 | K = 3 | K = 5 |
| :--- | :--- | :--- | :--- |
| **Precision@K** | {ret.precision_at_k.get(1, 0.0):.4f} | {ret.precision_at_k.get(3, 0.0):.4f} | {ret.precision_at_k.get(5, 0.0):.4f} |
| **Recall@K** | {ret.recall_at_k.get(1, 0.0):.4f} | {ret.recall_at_k.get(3, 0.0):.4f} | {ret.recall_at_k.get(5, 0.0):.4f} |
| **Hit Rate@K** | {ret.hit_rate_at_k.get(1, 0.0):.4f} | {ret.hit_rate_at_k.get(3, 0.0):.4f} | {ret.hit_rate_at_k.get(5, 0.0):.4f} |
| **MRR** | **{ret.mrr:.4f}** | — | — |

---

## 2. Exact Statutory Provision Retrieval Investigation

**Target**: UK Bribery Act 2010 `Section 1` (`RR-UK-01` / `RR-UK-01-C01`)  
**Query**: *"{epa.query}"*  

- **Actual Rank in Retrieval**: **#{epa.rank_in_retrieval}** (Similarity: `{epa.similarity_score:.4f}`)
- **Retrieved at K=1**: `{epa.retrieved_at_k1}`
- **Retrieved at K=3**: `{epa.retrieved_at_k3}`
- **Retrieved at K=5**: `{epa.retrieved_at_k5}`
- **Top-Ranked Chunk**: `{epa.top_ranked_chunk_id}` (*{epa.top_ranked_regulation}*)
- **Technical Observation**: {epa.notes}

---

## 3. Groundedness Evaluation Rubric

| Outcome | Count | Description |
| :--- | :--- | :--- |
| **SUPPORTED** | {report.groundedness_summary.get("SUPPORTED", 0)} | All deterministic source whitelisting and abstention checks passed |
| **PARTIALLY_SUPPORTED** | {report.groundedness_summary.get("PARTIALLY_SUPPORTED", 0)} | Minor omissions or non-critical formatting deviations |
| **UNSUPPORTED** | {report.groundedness_summary.get("UNSUPPORTED", 0)} | Hallucinated citations, unwhitelisted sources, or failed abstentions |
| **NOT_APPLICABLE** | {report.groundedness_summary.get("NOT_APPLICABLE", 0)} | Non-evaluable queries |
| **REQUIRES_HUMAN_REVIEW** | {report.groundedness_summary.get("REQUIRES_HUMAN_REVIEW", 0)} | Ambiguous relevance marked for legal SME review ({', '.join(report.cases_requiring_human_review)}) |

---

## 4. Citation & Provenance Quality

- **Total Citations Evaluated**: {cit.total_citations}
- **Valid (Whitelisted) Citations**: {cit.valid_citations}
- **Invalid Citations**: {cit.invalid_citations}
- **Citation Validity Rate**: **{cit.validity_rate * 100:.1f}%**
- **Sentence-Level Precision / Recall**: **NOT_EVALUATED** (Task 6 scope provides chunk-level provenance)

---

## 5. GAP & No-Source Classification Accuracy

- **Total GAP Cases**: {gap.total_gap_cases}
- **Correct Classifications**: {gap.correct_classifications}
- **Incorrect Classifications**: {gap.incorrect_classifications}
- **Classification Accuracy**: **{gap.accuracy * 100:.1f}%**
- **False-Grounded Answers**: **{gap.false_grounded_count}**

---

## 6. Regulatory Conflict & Overlap Detection

Evaluated against the controlled 11-pair Conflict/Overlap register.

- **Cases Evaluated**: {conf.total_cases_evaluated}
- **True Positives**: {conf.true_positives}
- **False Positives**: {conf.false_positives}
- **False Negatives**: {conf.false_negatives}
- **Pair Precision**: **{conf.pair_precision * 100:.1f}%**
- **Pair Recall**: **{conf.pair_recall * 100:.1f}%**
- **Exact Match Accuracy**: **{conf.classification_accuracy * 100:.1f}%**

---

## 7. Safety, Gating & Adversarial Defense

- **Candidate Status Preserved (15 records)**: `{safe.candidate_status_preserved}`
- **Approved-Only Filter Gating**: `{safe.approved_only_filtering_correct}`
- **Zero Fabricated Citations**: `{safe.zero_fabricated_citations}`
- **Zero Fabricated Conflict IDs**: `{safe.zero_fabricated_conflicts}`
- **Zero Legal Conflict Adjudication**: `{safe.zero_legal_conflict_resolutions}`
- **Checks Passed**: {safe.checks_passed_count} / {safe.checks_passed_count + safe.checks_failed_count}

### Adversarial Prompt Injections Tested
"""
        for pi in report.prompt_injection_results:
            safe_str = "SAFE" if pi.safe_behavior_observed else "VULNERABLE"
            md += f"- **[{safe_str}] {pi.case_id} ({pi.attack_type})**: Query: *\"{pi.query}\"*  \n  Observation: {pi.details}\n"

        md += """
---

## 8. Failure & Limitation Analysis

| Case ID | Category | Expected Behavior | Actual Behavior | Responsible Module | Severity | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for fa in report.failure_analysis:
            md += f"| {fa.case_id} | {fa.category} | {fa.expected_behavior} | {fa.actual_behavior} | {fa.responsible_module} | {fa.severity} | {fa.recommended_future_improvement} |\n"

        md += """
---

## 9. Architectural Limitations & Next Steps

"""
        for lim in report.limitations:
            md += f"- {lim}\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        logger.info(f"Wrote evaluation summary to {md_path}")
