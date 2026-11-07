"""Packaging script for ABC Shield AI/RAG Delivery ZIP.

Generates a clean delivery package at D:\\FInregTech Shipyard\\abc-shield-ai-delivery.zip
strictly excluding virtual environments, caches, secrets, scratch scripts, and temporary databases.
Includes complete canonical staged artifacts (step4, step5, step6 ChromaDB), fast-track artifacts,
all raw/incoming datasets, scripts, tests, and configuration for clean-machine execution.
"""

from pathlib import Path
import zipfile
import json
import sys


def create_delivery_zip():
    project_root = Path(__file__).resolve().parent.parent
    output_zip_path = project_root.parent / "abc-shield-ai-delivery.zip"

    print(f"Project root: {project_root}")
    print(f"Target delivery zip: {output_zip_path}")

    # Explicit inclusions (relative to project_root)
    included_dirs = [
        "api",
        "rag",
        "config",
        "data/staging/madhesh_handover",
        "data/staging/fast_track",
        "data/incoming_handover_20261021",
        "data/incoming_handover_20261014",
        "data/raw",
        "data/evaluation",
        "data/processed",
        "tests",
        "scripts",
    ]

    included_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        "pytest.ini",
        ".gitignore",
    ]

    # Explicit exclusion patterns
    exclude_parts = {
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "scratch",
        ".git",
    }

    exclude_extensions = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".log",
        ".tmp",
    }

    exclude_filenames = {
        ".env",
        "approval_test_source.txt",
        "check_databases.py",
    }

    files_to_pack = set()

    # Collect individual files
    for fname in included_files:
        fpath = project_root / fname
        if fpath.is_file():
            files_to_pack.add(fpath)
        else:
            print(f"WARNING: Root file not found: {fname}")

    # Collect directory files
    for dname in included_dirs:
        dirpath = project_root / dname
        if not dirpath.exists():
            print(f"WARNING: Directory not found: {dname}")
            continue

        for p in dirpath.rglob("*"):
            if not p.is_file():
                continue

            # Check exclusions
            if any(part in exclude_parts for part in p.parts):
                continue
            if p.suffix.lower() in exclude_extensions:
                continue
            if p.name in exclude_filenames:
                continue

            files_to_pack.add(p)

    sorted_files = sorted(list(files_to_pack))
    print(f"Total files to pack: {len(sorted_files)}")

    # Build ZIP archive
    if output_zip_path.exists():
        output_zip_path.unlink()

    with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in sorted_files:
            rel_path = file_path.relative_to(project_root)
            # Use forward slashes in zip archive for cross-platform portability
            arcname = str(rel_path).replace("\\", "/")
            zf.write(file_path, arcname=arcname)

    # Verification of the generated ZIP
    print("\n--- ZIP VERIFICATION ---")
    with zipfile.ZipFile(output_zip_path, "r") as zf:
        infolist = zf.infolist()
        total_compressed = sum(info.compress_size for info in infolist)
        total_uncompressed = sum(info.file_size for info in infolist)
        namelist = zf.namelist()

        print(f"Archived entries: {len(namelist)}")
        print(f"Total uncompressed size: {total_uncompressed / (1024*1024):.2f} MB")
        print(f"Total compressed size:   {total_compressed / (1024*1024):.2f} MB")

        # Sanity check forbidden patterns
        forbidden_hits = [
            name for name in namelist
            if any(forbidden in name.lower() for forbidden in [
                ".venv", "__pycache__", ".pytest_cache", "scratch/", ".env"
            ]) and not name.endswith(".env.example")
        ]

        if forbidden_hits:
            print(f"CRITICAL ERROR: Forbidden entries found in archive: {forbidden_hits[:10]}")
            sys.exit(1)
        else:
            print("Sanity Check Passed: No venvs, caches, scratch scripts, or secrets found.")

        # Check required key components
        must_contain = [
            "api/main.py",
            "api/routes/query.py",
            "api/routes/compare.py",
            "api/routes/health.py",
            "rag/generation/grounded_generator.py",
            "rag/retrieval/vector_store.py",
            "config/settings.py",
            "data/staging/madhesh_handover/step4/normalized_regulatory_records.json",
            "data/staging/madhesh_handover/step5/regulatory_chunks.json",
            "data/staging/madhesh_handover/step6/chroma_db/chroma.sqlite3",
            "data/staging/fast_track/normalized_regulatory_records.json",
            "data/staging/fast_track/regulatory_chunks.json",
            "data/incoming_handover_20261021/ABC_Shield_Canonical_25_Record_Corpus.xlsx",
            "data/incoming_handover_20261021/ABC_Shield_Canonical_Source_Register.xlsx",
            "data/incoming_handover_20261014/ABC Shield _scope note.docx",
            "data/raw/ABC_Shield_Canonical_25_Record_Corpus.xlsx",
            "data/evaluation/ABC_SHIELD_RAG_HANDOVER_GUIDE.md",
            "tests/test_source_control_approval.py",
            "tests/test_fast_track_step6_smoke.py",
            "tests/test_fast_track_step4_acceptance.py",
            "tests/test_handover_step4_ingestion_validation.py",
            "tests/test_handover_step5_chunk_validation.py",
            "scripts/index_staged_handover_step6.py",
            "scripts/prepare_fast_track_step2_kb.py",
            "README.md",
            ".env.example",
            "pytest.ini",
        ]

        missing_must_contain = [m for m in must_contain if m not in namelist]
        if missing_must_contain:
            print(f"CRITICAL ERROR: Missing required files: {missing_must_contain}")
            sys.exit(1)
        else:
            print("Sanity Check Passed: All required core components, source datasets, and scripts verified present.")

        # In-archive verification of canonical chunk and record approval safeguards
        datasets_to_verify = [
            ("data/staging/madhesh_handover/step5/regulatory_chunks.json", 25),
            ("data/staging/madhesh_handover/step4/normalized_regulatory_records.json", 25),
            ("data/staging/fast_track/regulatory_chunks.json", 25),
            ("data/staging/fast_track/normalized_regulatory_records.json", 25),
        ]

        for entry_name, expected_count in datasets_to_verify:
            with zf.open(entry_name) as entry_file:
                items = json.load(entry_file)
            assert len(items) == expected_count, (
                f"Expected {expected_count} items in {entry_name}, found {len(items)}"
            )
            unapproved = sum(1 for it in items if it.get("is_approved_for_rag") is False)
            approved = sum(1 for it in items if it.get("is_approved_for_rag") is True)
            assert unapproved == expected_count and approved == 0, (
                f"Fail-closed violation in {entry_name}: {unapproved} unapproved, {approved} approved"
            )
            print(f"Safeguard Verified: {entry_name} ({len(items)} items, 100% unapproved, is_approved_for_rag=False)")

    print(f"\nDelivery ZIP successfully created at: {output_zip_path}")


if __name__ == "__main__":
    create_delivery_zip()
