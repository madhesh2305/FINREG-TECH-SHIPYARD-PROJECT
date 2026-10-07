import os
from typing import Generator
from urllib.parse import unquote
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

SCHEMAS = [
    "identity",
    "project_management",
    "advisor_management",
    "regulatory",
    "advice",
    "ai",
    "decision",
    "readiness",
    "audit",
    "reporting",
]

def create_db_engine():
    """Create SQLAlchemy engine with appropriate dialect settings."""
    url = settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")
    
    if is_sqlite:
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
        
        @event.listens_for(engine, "connect")
        def attach_sqlite_schemas(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            for schema in SCHEMAS:
                cursor.execute(f"ATTACH DATABASE ':memory:' AS {schema}")
            cursor.close()
            
        return engine
    else:
        try:
            parsed_url = make_url(url)
            if parsed_url.database and "%20" in parsed_url.database:
                parsed_url = parsed_url.set(database=unquote(parsed_url.database))
            engine = create_engine(
                parsed_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            # Test connection
            with engine.connect() as conn:
                pass
            return engine
        except Exception as e:
            # Fallback for offline development if PostgreSQL instance is unreachable
            print(f"[DB Warning] Could not connect to PostgreSQL ({e}). Using SQLite fallback.")
            engine = create_engine(
                settings.SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False}
            )
            sqlite_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".sqlite_data"))
            os.makedirs(sqlite_dir, exist_ok=True)
            @event.listens_for(engine, "connect")
            def attach_sqlite_schemas(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                for schema in SCHEMAS:
                    db_path = os.path.join(sqlite_dir, f"{schema}.db").replace("\\", "/")
                    cursor.execute(f"ATTACH DATABASE '{db_path}' AS {schema}")
                cursor.close()
            return engine

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
