#!/usr/bin/env python3
"""
Standalone Database Migration Verification Script.
Executes Alembic migrations and verifies the identity.revoked_tokens schema.
"""
import argparse
import os
import sys
from urllib.parse import unquote
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

def run_migration_and_verify(target_url: str = None) -> bool:
    url = target_url or settings.TEST_DATABASE_URL or settings.DATABASE_URL
    os.environ["ALEMBIC_DATABASE_URL"] = url

    print("[MIGRATION VERIFICATION] Starting Alembic migration runner...")
    alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")
    alembic_cfg = Config(alembic_cfg_path)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    try:
        # Run upgrade to head
        print("[MIGRATION VERIFICATION] Executing: alembic upgrade head")
        command.upgrade(alembic_cfg, "head")
        print("[MIGRATION VERIFICATION] Alembic upgrade completed successfully.")
    except Exception as e:
        print(f"[MIGRATION ERROR] Migration upgrade failed: {e}")
        return False

    # Connect to verify schema
    try:
        if url.startswith("sqlite"):
            engine = create_engine(url, connect_args={"check_same_thread": False})
            schema_name = None
        else:
            parsed = make_url(url)
            if parsed.database and "%20" in parsed.database:
                parsed = parsed.set(database=unquote(parsed.database))
            engine = create_engine(parsed)
            schema_name = "identity"

        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=schema_name)

        target_table = "revoked_tokens"
        if target_table not in tables:
            print(f"[MIGRATION ERROR] Table '{schema_name}.{target_table}' not found in database!")
            return False

        columns = {col["name"]: str(col["type"]) for col in inspector.get_columns(target_table, schema=schema_name)}
        expected_cols = ["token_id", "jti", "token_signature", "revoked_at", "expires_at"]
        for col in expected_cols:
            if col not in columns:
                print(f"[MIGRATION ERROR] Missing expected column '{col}' in '{target_table}'!")
                return False

        print(f"[MIGRATION VERIFICATION] Table '{schema_name}.{target_table}' verified with columns: {list(columns.keys())}")

        indexes = inspector.get_indexes(target_table, schema=schema_name)
        index_names = [idx["name"] for idx in indexes]
        print(f"[MIGRATION VERIFICATION] Found indexes: {index_names}")
        print("[MIGRATION VERIFICATION] PASSED: Database migration verified successfully.")
        return True
    except Exception as e:
        print(f"[MIGRATION ERROR] Schema inspection failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Alembic migrations on target database.")
    parser.add_argument("--test-db", action="store_true", help="Run against TEST_DATABASE_URL")
    args = parser.parse_args()

    target = settings.TEST_DATABASE_URL if args.test_db else settings.DATABASE_URL
    success = run_migration_and_verify(target)
    sys.exit(0 if success else 1)
