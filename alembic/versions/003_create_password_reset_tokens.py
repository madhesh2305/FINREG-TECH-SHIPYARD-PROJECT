"""create password_reset_tokens table in identity schema

Revision ID: 003_create_password_reset_tokens
Revises: 002_create_project_attachments
Create Date: 2026-10-20 23:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_create_password_reset_tokens'
down_revision: Union[str, None] = '002_create_project_attachments'
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
        if "password_reset_tokens" not in existing_tables:
            op.execute("""
                CREATE TABLE identity.password_reset_tokens (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES identity.users (user_id) ON DELETE CASCADE,
                    token_hash VARCHAR(128) NOT NULL UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    used_at TIMESTAMP WITH TIME ZONE,
                    is_revoked BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            op.execute("""
                CREATE INDEX ix_identity_password_reset_tokens_user_id
                ON identity.password_reset_tokens (user_id)
            """)
            op.execute("""
                CREATE INDEX ix_identity_password_reset_tokens_token_hash
                ON identity.password_reset_tokens (token_hash)
            """)
    else:
        # SQLite dialect
        insp = sa.inspect(bind)
        existing_tables = insp.get_table_names()
        if "password_reset_tokens" not in existing_tables:
            op.execute("""
                CREATE TABLE password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
                    token_hash VARCHAR(128) NOT NULL UNIQUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP,
                    is_revoked BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            op.execute("""
                CREATE INDEX ix_password_reset_tokens_user_id
                ON password_reset_tokens (user_id)
            """)
            op.execute("""
                CREATE INDEX ix_password_reset_tokens_token_hash
                ON password_reset_tokens (token_hash)
            """)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP TABLE IF EXISTS identity.password_reset_tokens CASCADE")
    else:
        op.execute("DROP TABLE IF EXISTS password_reset_tokens")
