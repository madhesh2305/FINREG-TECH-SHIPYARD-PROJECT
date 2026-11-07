"""Real end-to-end demonstration of Task 7 GAP / No-Source Handling Layer.

Flow:
User Question
    ↓
Task 4 Retriever (semantic search against persistent ChromaDB)
    ↓
Retrieved Evidence Chunks (with complete metadata & provenance)
    ↓
Task 5 Grounded Generator (deterministic prompt assembly & guardrails)
    ↓
Task 6 Citation & Provenance Builder (retrieved-evidence provenance)
    ↓
Task 7 GAP / No-Source Analyzer (deterministic gap classification)
    ↓
Structured GroundedResponse with verified Citations, Provenance & GAP Analysis
"""

from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.generation import GroundedGenerator
from config import settings


def print_citations_and_provenance(response):
    """Format and display deterministic citations and provenance chains."""
    print(f"\nCitations Count: {len(response.citations)}")
    if not response.citations:
        print("  (No citations generated — ungrounded or insufficient evidence)")
    for i, cit in enumerate(response.citations, 1):
        print(f"  [{i}] Human-Readable: {cit.formatted_citation}")
        print(f"      Citation ID:       {cit.citation_id}")
        print(f"      Record ID:         {cit.record_id}")
        print(f"      Source ID:         {cit.source_id}")
        print(f"      Official Source:   {cit.official_source or 'None'}")
        print(f"      Version / Date:    {cit.version_date or 'None'}")
        print(f"      Effective Date:    {cit.effective_date or 'None'}")
        print(f"      Validation Status: {cit.validation_status}")
        print(f"      Approved for RAG:  {cit.is_approved_for_rag}")

    if response.provenance:
        print(f"\nTraceable Provenance Chains ({len(response.provenance)}):")
        for i, prov in enumerate(response.provenance, 1):
            score_str = f"{prov.similarity_score:.4f}" if prov.similarity_score is not None else "N/A"
            print(
                f"  [{i}] {prov.chunk_id} -> Record: {prov.record_id} -> Source: {prov.source_id} "
                f"-> Regulation: {prov.regulation} ({prov.section_article}) [Score: {score_str} | Status: {prov.validation_status}]"
            )


def print_gap_analysis(response):
    """Format and display deterministic GAP / No-source analysis."""
    print("\nGAP / No-Source Analysis:")
    if response.gap is None:
        print("  is_gap:                  False (Sufficient grounded evidence established — no gap detected)")
    else:
        gap = response.gap
        print(f"  is_gap:                  {gap.is_gap}")
        print(f"  Gap Type:                {gap.gap_type.value}")
        print(f"  Technical Message:       {gap.message}")
        print(f"  User-Safe Disclosure:    {gap.user_safe_message}")
        print(f"  Relevant Evidence Count: {gap.relevant_evidence_count}")
        print(f"  Approved Evidence Count: {gap.approved_evidence_count}")
        print(f"  Recommended Next Action: {gap.recommended_next_action}")


def run_demonstration():
    print("=" * 80)
    print("ABC SHIELD / FINREGTECH SHIPYARD — TASK 7 GAP / NO-SOURCE HANDLING DEMO")
    print(f"Configured LLM Provider: {settings.llm_provider}")
    print(f"Configured Model:        {settings.llm_model_name}")
    print("=" * 80)

    generator = GroundedGenerator()

    # DEMO 1: Bribery Act query with top_k=3 (Section 1 is NOT in retrieved chunks)
    q1 = "What does the Bribery Act 2010 say about bribing another person?"
    print(f"\n>>> DEMO 1: USER QUESTION (top_k=3) — Demonstrating MISSING_SPECIFIC_PROVISION Gap:")
    print(f"Question: \"{q1}\"\n")
    print("Retrieving relevant evidence from ChromaDB (top_k=3)...")
    res1 = generator.generate_response(query=q1, top_k=3)

    print("\nStructured Response Details:")
    print("-" * 80)
    print(f"Confidence Status:      {res1.confidence_status}")
    print(f"Grounded on Evidence:   {res1.grounded}")
    print(f"Evidence Chunks (3):    {res1.evidence_used}")
    print(f"Approval Warning:\n  {res1.approval_warning}")
    print(f"\nGenerated Answer:\n{res1.answer}")
    print_citations_and_provenance(res1)
    print_gap_analysis(res1)
    print("-" * 80)

    # DEMO 2: Bribery Act query with top_k=5 (Section 1 IS retrieved as 5th chunk)
    print(f"\n>>> DEMO 2: USER QUESTION (top_k=5) — Demonstrating GROUNDED Answer with No Gap:")
    print(f"Question: \"{q1}\"\n")
    print("Retrieving relevant evidence from ChromaDB (top_k=5)...")
    res2 = generator.generate_response(query=q1, top_k=5)

    print("\nStructured Response Details:")
    print("-" * 80)
    print(f"Confidence Status:      {res2.confidence_status}")
    print(f"Grounded on Evidence:   {res2.grounded}")
    print(f"Evidence Chunks (5):    {res2.evidence_used}")
    print(f"\nGenerated Answer:\n{res2.answer}")
    print_citations_and_provenance(res2)
    print_gap_analysis(res2)
    print("-" * 80)

    # DEMO 3: Practical anti-bribery controls (top_k=3)
    q3 = "What are practical anti-bribery controls?"
    print(f"\n>>> DEMO 3: PRACTICAL CONTROLS QUESTION (top_k=3) — Grounded Guidance with No Gap:")
    print(f"Question: \"{q3}\"\n")
    res3 = generator.generate_response(query=q3, top_k=3)

    print("Structured Response Details:")
    print("-" * 80)
    print(f"Confidence Status:      {res3.confidence_status}")
    print(f"Grounded on Evidence:   {res3.grounded}")
    print(f"Evidence Chunks (3):    {res3.evidence_used}")
    print(f"\nGenerated Answer:\n{res3.answer}")
    print_citations_and_provenance(res3)
    print_gap_analysis(res3)
    print("-" * 80)

    # DEMO 4: Out-of-scope query (cybersecurity)
    q4 = "What cybersecurity requirements apply?"
    print(f"\n>>> DEMO 4: OUT-OF-SCOPE DEMONSTRATION QUESTION — Demonstrating OUT_OF_SCOPE Gap:")
    print(f"Question: \"{q4}\"\n")
    res4 = generator.generate_response(query=q4, top_k=3)

    print("Structured Response Details:")
    print("-" * 80)
    print(f"Confidence Status:      {res4.confidence_status}")
    print(f"Grounded on Evidence:   {res4.grounded}")
    print(f"Evidence Chunks:        {res4.evidence_used}")
    print(f"\nGenerated Answer:\n{res4.answer}")
    print_citations_and_provenance(res4)
    print_gap_analysis(res4)
    print("-" * 80)

    # DEMO 5: Empty Retrieval under Approved-Only filter on candidate knowledge base
    print(f"\n>>> DEMO 5: APPROVED-ONLY QUERY ON CANDIDATE KNOWLEDGE BASE — Demonstrating UNAPPROVED_EVIDENCE Gap:")
    print(f"Question: \"{q1}\" (filter_approved_only=True)\n")
    res5 = generator.generate_response(query=q1, filter_approved_only=True)

    print("Structured Response Details:")
    print("-" * 80)
    print(f"Confidence Status:      {res5.confidence_status}")
    print(f"Grounded on Evidence:   {res5.grounded}")
    print(f"Evidence Chunks:        {res5.evidence_used}")
    print(f"\nGenerated Answer:\n{res5.answer}")
    print_citations_and_provenance(res5)
    print_gap_analysis(res5)
    print("=" * 80)


if __name__ == "__main__":
    run_demonstration()
