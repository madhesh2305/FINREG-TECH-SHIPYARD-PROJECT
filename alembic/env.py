import os
import sys
from logging.config import fileConfig
from urllib.parse import unquote

from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy.engine import make_url
from alembic import context

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.db.base import Base
import app.models  # Ensure all models are registered with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL") or settings.DATABASE_URL
    return url

def get_engine():
    raw_url = get_database_url()
    if raw_url.startswith("sqlite"):
        return create_engine(raw_url, connect_args={"check_same_thread": False})

    parsed = make_url(raw_url)
    if parsed.database and "%20" in parsed.database:
        parsed = parsed.set(database=unquote(parsed.database))
    return create_engine(parsed, poolclass=pool.NullPool)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema="public",
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
