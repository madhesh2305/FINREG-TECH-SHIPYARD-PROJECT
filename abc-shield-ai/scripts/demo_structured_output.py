"""Demonstration script for Task 9: Structured AI Output Contract.

Executes the actual pipeline and outputs the serialized JSON StructuredAIResponse
for 5 representative compliance scenarios:
1. Grounded Response (sufficient retrieved evidence).
2. Insufficient Evidence (Bribery Act specific provision missing at top_k=3).
3. Out-of-Scope Query (DORA cybersecurity).
4. Unapproved Evidence (filtered to approved-only while records are Candidate).
5. Conflict / Overlap Finding (Bribery Act 2010 + MoJ Guidance retrieved).
"""

from pathlib import Path
import sys
import json

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure utf-8 output on Windows
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rag.generation.grounded_generator import GroundedGenerator
from rag.generation.llm_interface import MockLLMProvider
from rag.output.structured_response import StructuredAIResponse


def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_demo():
    print("=" * 80)
    print("ABC SHIELD — TASK 9 STRUCTURED AI OUTPUT CONTRACT DEMO")
    print("=" * 80)

    generator = GroundedGenerator(llm_provider=MockLLMProvider())

    # -------------------------------------------------------------------------
    # SCENARIO 1: Grounded Response with Evidence
    # -------------------------------------------------------------------------
    print_separator("SCENARIO 1: Grounded Response (UK Bribery Act & MoJ Guidance)")
    resp1: StructuredAIResponse = generator.generate_structured_response(
        query="What procedures should commercial organisations implement to prevent bribery under UK guidance?",
        top_k=5,
        jurisdiction="UK",
        request_id="REQ-2026-001",
    )
    print(resp1.model_dump_json(indent=2))

    # -------------------------------------------------------------------------
    # SCENARIO 2: Insufficient Evidence
    # -------------------------------------------------------------------------
    print_separator("SCENARIO 2: Insufficient Evidence (Specific Section Absent at top_k=3)")
    resp2: StructuredAIResponse = generator.generate_structured_response(
        query="What does the Bribery Act 2010 say about bribing another person?",
        top_k=3,
        jurisdiction="UK",
        request_id="REQ-2026-002",
    )
    print(resp2.model_dump_json(indent=2))

    # -------------------------------------------------------------------------
    # SCENARIO 3: Out-of-Scope Query
    # -------------------------------------------------------------------------
    print_separator("SCENARIO 3: Out-of-Scope Query (DORA Cybersecurity)")
    resp3: StructuredAIResponse = generator.generate_structured_response(
        query="What are the ICT resilience requirements under DORA cybersecurity regulations?",
        top_k=5,
        request_id="REQ-2026-003",
    )
    print(resp3.model_dump_json(indent=2))

    # -------------------------------------------------------------------------
    # SCENARIO 4: Unapproved Evidence
    # -------------------------------------------------------------------------
    print_separator("SCENARIO 4: Unapproved Evidence (Approved-only filter on Candidate records)")
    resp4: StructuredAIResponse = generator.generate_structured_response(
        query="What are the commercial bribery penalties?",
        top_k=5,
        filter_approved_only=True,
        request_id="REQ-2026-004",
    )
    print(resp4.model_dump_json(indent=2))

    # -------------------------------------------------------------------------
    # SCENARIO 5: Conflict / Overlap Finding
    # -------------------------------------------------------------------------
    print_separator("SCENARIO 5: Documented Conflict / Overlap Finding (UK-01 & UK-02)")
    resp5: StructuredAIResponse = generator.generate_structured_response(
        query="What is the relationship between Bribery Act offences and the prevention guidance?",
        top_k=5,
        jurisdiction="UK",
        request_id="REQ-2026-005",
    )
    print(resp5.model_dump_json(indent=2))

    print("\n" + "=" * 80)
    print("ALL 5 DEMONSTRATION SCENARIOS EXECUTED AND SERIALIZED CLEANLY")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
