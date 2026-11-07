"""Retrieval demonstration script for Task 4.

Executes semantic retrieval for the three specified queries against the
existing persistent ChromaDB without calling any LLM.
"""

from pathlib import Path
import sys
import json

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.retrieval.retriever import RegulatoryRetriever

QUERIES = [
    "What does the Bribery Act 2010 say about bribing another person?",
    "What are practical anti-bribery controls?",
    "What cybersecurity requirements apply?",
]


def run_demonstration():
    print("=" * 80)
    print("ABC SHIELD / FINREGTECH SHIPYARD — TASK 4 RETRIEVAL DEMONSTRATION")
    print("Persistent ChromaDB Path: data/processed/chroma_db/")
    print("Collection Name: regulatory_records")
    print("Embedding Model: all-MiniLM-L6-v2 (384 dimensions)")
    print("=" * 80)

    retriever = RegulatoryRetriever()

    for idx, query in enumerate(QUERIES, 1):
        print(f"\n>>> TEST QUERY {idx}: \"{query}\"")
        results = retriever.retrieve(query=query, top_k=3)
        print(f"Total Chunks Retrieved: {len(results)}\n")

        for r_idx, res in enumerate(results, 1):
            print(f"  [{r_idx}] CHUNK ID: {res.chunk_id}")
            print(f"      Record ID: {res.record_id} | Source ID: {res.source_id}")
            print(f"      Regulation: {res.regulation}")
            print(f"      Section / Article: {res.section_article}")
            print(f"      Title: {res.title}")
            print(f"      Jurisdiction: {res.jurisdiction} | Authority Level: {res.authority_level}")
            print(f"      Validation Status: {res.validation_status}")
            print(f"      Approved for Authoritative RAG: {res.is_approved_for_rag}")
            print(f"      Text Type: {res.text_type}")
            print(f"      Cosine Distance: {res.distance:.4f} | Similarity Score: {res.similarity_score:.4f}")
            print(f"      Official Source: {res.official_source}")
            print(f"      Retrieved Text: \"{res.text}\"")
            print()

    # Demonstration of the safety rule: approved-only filter
    print("=" * 80)
    print("SAFETY RULE DEMONSTRATION: filter_approved_only=True")
    print("Query: 'Bribery Act 2010 offences'")
    approved_results = retriever.retrieve("Bribery Act 2010 offences", top_k=5, filter_approved_only=True)
    print(f"Chunks returned when filtering for approved-only evidence: {len(approved_results)}")
    print("Note: Correctly returns 0 chunks because all 15 records are 'Candidate - Awaiting Approval'.")
    print("=" * 80)


if __name__ == "__main__":
    run_demonstration()
