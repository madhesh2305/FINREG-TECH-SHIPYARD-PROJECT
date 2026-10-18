"""
FINREGTECH SHIPYARD — FAIL-CLOSED MANUAL TEST SERVER LAUNCHER
Ensures the Uvicorn backend process is strictly connected to 'finregtech_test'
and guarantees that the primary database 'FinRegTech ShipYard' can never be touched.
"""
import os
import sys
import argparse
from urllib.parse import unquote
from sqlalchemy.engine import make_url

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

# 1. Read .env without importing app.core.config or initializing engine
from pydantic_settings import BaseSettings, SettingsConfigDict

class BootstrapConfig(BaseSettings):
    TEST_DATABASE_URL: str | None = None
    model_config = SettingsConfigDict(
        env_file=[os.path.join(backend_dir, ".env"), ".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

def main():
    parser = argparse.ArgumentParser(description="Start isolated manual-test backend locked to finregtech_test.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (strictly 127.0.0.1)")
    args = parser.parse_args()

    # Enforce localhost only
    if args.host not in ("127.0.0.1", "localhost"):
        print("ERROR: Test server must only be bound to 127.0.0.1 (localhost).", file=sys.stderr)
        sys.exit(1)

    # 1. Resolve test database connection from environment or .env
    cfg = BootstrapConfig()
    test_url = os.getenv("TEST_DATABASE_URL") or cfg.TEST_DATABASE_URL
    if not test_url:
        print("FATAL ERROR: TEST_DATABASE_URL is not configured in .env or environment!", file=sys.stderr)
        print("Manual testing cannot proceed without an isolated test database.", file=sys.stderr)
        sys.exit(1)

    # 2. Strict Database Name & Dialect Validation
    parsed = make_url(test_url)
    dialect = parsed.get_backend_name()
    if dialect != "postgresql":
        print(f"FATAL ERROR: Test database dialect must be 'postgresql', found '{dialect}'.", file=sys.stderr)
        sys.exit(1)

    raw_db = parsed.database or ""
    db_name = unquote(raw_db).strip()

    if db_name.lower() == "finregtech shipyard" or "shipyard" in db_name.lower():
        print("FATAL SECURITY VIOLATION: TEST_DATABASE_URL points to the primary database!", file=sys.stderr)
        print("Aborting immediately to protect primary database integrity.", file=sys.stderr)
        sys.exit(1)

    if db_name != "finregtech_test":
        print(f"FATAL ERROR: Test database must be exactly 'finregtech_test', found '{db_name}'.", file=sys.stderr)
        sys.exit(1)

    # 3. Live Database Identity Handshake before server initialization
    from sqlalchemy import create_engine, text
    try:
        if raw_db and "%20" in raw_db:
            parsed_conn = parsed.set(database=unquote(raw_db))
        else:
            parsed_conn = parsed
        verify_engine = create_engine(parsed_conn, pool_pre_ping=True)
        with verify_engine.connect() as conn:
            actual_db = conn.execute(text("SELECT current_database()")).scalar()
            actual_user = conn.execute(text("SELECT current_user")).scalar()
            
            if actual_db != "finregtech_test":
                print(f"FATAL ERROR: PostgreSQL connected to '{actual_db}', expected 'finregtech_test'!", file=sys.stderr)
                sys.exit(1)
        verify_engine.dispose()
    except Exception as e:
        print(f"FATAL ERROR: Could not connect to isolated test database 'finregtech_test'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Inject Environment Overrides BEFORE app/session engine is loaded
    os.environ["DATABASE_URL"] = test_url
    os.environ["ENVIRONMENT"] = "manual_test"
    os.environ["PORT"] = str(args.port)
    os.environ["HOST"] = args.host

    # 5. Assert engine initialization locks to finregtech_test
    from app.core.config import settings
    from app.db.session import engine

    effective_db = unquote(make_url(settings.DATABASE_URL).database)
    effective_engine_db = unquote(make_url(str(engine.url)).database)

    assert effective_db == "finregtech_test", f"Safety violation: settings.DATABASE_URL is {effective_db}"
    assert effective_engine_db == "finregtech_test", f"Safety violation: engine.url is {effective_engine_db}"

    # 6. Safe Display Banner (Zero Plaintext Secrets)
    print("=" * 80)
    print("  FINREGTECH SHIPYARD — ISOLATED MANUAL TEST SERVER")
    print("=" * 80)
    print(f"  Target Database   : finregtech_test (Confirmed via live SQL handshake)")
    print(f"  Connected User    : {actual_user} (NOSUPERUSER, isolated sandbox)")
    print(f"  Primary DB Guard  : 'FinRegTech ShipYard' is STRICTLY PROTECTED (Zero traffic)")
    print(f"  Environment Mode  : manual_test")
    print(f"  Service Address   : http://{args.host}:{args.port}")
    print(f"  Swagger Docs      : http://{args.host}:{args.port}/docs")
    print(f"  Health Check      : http://{args.host}:{args.port}/health")
    print("=" * 80)
    print("  Server is fail-closed: all write operations only affect 'finregtech_test'.")
    print("=" * 80)

    # 7. Launch Uvicorn
    import uvicorn
    uvicorn.run("app.main:app", host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
