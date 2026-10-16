"""create revoked_tokens table in identity schema

Revision ID: 001_create_revoked_tokens
Revises:
Create Date: 2026-10-16 23:59:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_create_revoked_tokens'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        insp = sa.inspect(bind)
        if "identity" not in insp.get_schema_names():
            op.execute("CREATE SCHEMA IF NOT EXISTS identity")

        existing_tables = insp.get_table_names(schema="identity")
        if "revoked_tokens" not in existing_tables:
            op.execute("""
                CREATE TABLE identity.revoked_tokens (
                    token_id BIGSERIAL PRIMARY KEY,
                    jti VARCHAR(255) UNIQUE,
                    token_signature VARCHAR(255) NOT NULL UNIQUE,
                    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE
                )
            """)
            op.execute("""
                CREATE INDEX ix_identity_revoked_tokens_jti
                ON identity.revoked_tokens (jti)
            """)
            op.execute("""
                CREATE INDEX ix_identity_revoked_tokens_token_signature
                ON identity.revoked_tokens (token_signature)
            """)
    else:
        # SQLite or other fallback
        insp = sa.inspect(bind)
        existing_tables = insp.get_table_names()
        if "revoked_tokens" not in existing_tables:
            op.execute("""
                CREATE TABLE revoked_tokens (
                    token_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jti VARCHAR(255) UNIQUE,
                    token_signature VARCHAR(255) NOT NULL UNIQUE,
                    revoked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            op.execute("""
                CREATE INDEX ix_revoked_tokens_jti
                ON revoked_tokens (jti)
            """)
            op.execute("""
                CREATE INDEX ix_revoked_tokens_token_signature
                ON revoked_tokens (token_signature)
            """)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        insp = sa.inspect(bind)
        if "revoked_tokens" in insp.get_table_names(schema="identity"):
            op.execute("DROP TABLE identity.revoked_tokens CASCADE")
    else:
        insp = sa.inspect(bind)
        if "revoked_tokens" in insp.get_table_names():
            op.execute("DROP TABLE revoked_tokens")
