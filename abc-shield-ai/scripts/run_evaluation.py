"""Command-line script to run the Task 10 evaluation and safety benchmark.

Usage:
    python scripts/run_evaluation.py [--dataset PATH] [--output-dir PATH]
"""

import sys
from pathlib import Path
import argparse
import logging

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.evaluation.evaluation_runner import EvaluationRunner

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run ABC Shield RAG Evaluation Benchmark")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation/evaluation_cases.json",
        help="Path to evaluation cases JSON dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/evaluation/results",
        help="Directory to save evaluation reports",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="MockLLMProvider",
        help="Name of the LLM provider under test",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("ABC SHIELD / FINREGTECH SHIPYARD — TASK 10 EVALUATION & SAFETY")
    print("=" * 70)

    runner = EvaluationRunner(output_dir=Path(args.output_dir))
    report = runner.run_benchmark(
        dataset_path=Path(args.dataset),
        provider_name=args.provider,
    )

    ret = report.retrieval_metrics
    cit = report.citation_metrics
    gap = report.gap_metrics
    conf = report.conflict_metrics
    safe = report.safety_metrics
    epa = report.exact_provision_analysis

    print("\n" + "=" * 70)
    print("1. RETRIEVAL METRICS (Record-Level Deduplicated)")
    print("=" * 70)
    print(f"Evaluated Cases: {ret.evaluated_cases}  |  Zero-Expected Cases: {ret.zero_expected_cases}")
    print(f"{'K':<5} | {'Precision@K':<15} | {'Recall@K':<15} | {'Hit Rate@K':<15}")
    print("-" * 55)
    for k in (1, 3, 5):
        print(f"{k:<5} | {ret.precision_at_k.get(k, 0.0):<15.4f} | {ret.recall_at_k.get(k, 0.0):<15.4f} | {ret.hit_rate_at_k.get(k, 0.0):<15.4f}")
    print("-" * 55)
    print(f"MRR (Mean Reciprocal Rank): {ret.mrr:.4f}")

    print("\n" + "=" * 70)
    print("2. EXACT STATUTORY PROVISION RANK ANALYSIS")
    print("=" * 70)
    print(f"Target Provision: {epa.target_record_id} ({epa.target_chunk_id})")
    print(f"Query: {epa.query}")
    print(f"Retrieval Rank: #{epa.rank_in_retrieval} (Similarity: {epa.similarity_score:.4f})")
    print(f"Top-Ranked Chunk: {epa.top_ranked_chunk_id} ({epa.top_ranked_regulation})")
    print(f"Retrieved in Top-1: {epa.retrieved_at_k1} | Top-3: {epa.retrieved_at_k3} | Top-5: {epa.retrieved_at_k5}")

    print("\n" + "=" * 70)
    print("3. GROUNDEDNESS OUTCOMES")
    print("=" * 70)
    for outcome, count in report.groundedness_summary.items():
        print(f"  - {outcome:<25}: {count}")

    print("\n" + "=" * 70)
    print("4. CITATION & PROVENANCE QUALITY")
    print("=" * 70)
    print(f"Total Citations: {cit.total_citations}")
    print(f"Whitelisted / Valid: {cit.valid_citations}")
    print(f"Citation Validity Rate: {cit.validity_rate * 100:.1f}%")
    print("Sentence-level Precision/Recall: NOT_EVALUATED (chunk-level provenance)")

    print("\n" + "=" * 70)
    print("5. GAP CLASSIFICATION ACCURACY")
    print("=" * 70)
    print(f"Total GAP Cases: {gap.total_gap_cases}")
    print(f"Correct Classifications: {gap.correct_classifications}")
    print(f"GAP Accuracy: {gap.accuracy * 100:.1f}%")
    print(f"False-Grounded Answers: {gap.false_grounded_count}")

    print("\n" + "=" * 70)
    print("6. REGULATORY CONFLICT & OVERLAP DETECTION")
    print("=" * 70)
    print(f"Evaluated Cases: {conf.total_cases_evaluated}")
    print(f"True Positives: {conf.true_positives} | False Positives: {conf.false_positives} | False Negatives: {conf.false_negatives}")
    print(f"Pair Precision: {conf.pair_precision * 100:.1f}%")
    print(f"Pair Recall: {conf.pair_recall * 100:.1f}%")
    print(f"Exact Match Accuracy: {conf.classification_accuracy * 100:.1f}%")

    print("\n" + "=" * 70)
    print("7. SAFETY & ADVERSARIAL RESILIENCE")
    print("=" * 70)
    print(f"Candidate Status Preserved (15 records): {safe.candidate_status_preserved}")
    print(f"Approved-Only Gating Correct: {safe.approved_only_filtering_correct}")
    print(f"Zero Fabricated Citations: {safe.zero_fabricated_citations}")
    print(f"Zero Fabricated Conflict IDs: {safe.zero_fabricated_conflicts}")
    print(f"Zero Legal Conflict Adjudication: {safe.zero_legal_conflict_resolutions}")
    print(f"Checks Passed: {safe.checks_passed_count} / {safe.checks_passed_count + safe.checks_failed_count}")
    print("\nAdversarial Injections:")
    for pi in report.prompt_injection_results:
        status_str = "SAFE" if pi.safe_behavior_observed else "VULNERABLE"
        print(f"  [{status_str}] {pi.case_id} ({pi.attack_type})")

    print("\n" + "=" * 70)
    print("REPORTS GENERATED")
    print("=" * 70)
    print(f"JSON: {args.output_dir}/evaluation_results.json")
    print(f"Markdown: {args.output_dir}/evaluation_summary.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
