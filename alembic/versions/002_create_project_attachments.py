"""create project_attachments table in project_management schema

Revision ID: 002_create_project_attachments
Revises: 001_create_revoked_tokens
Create Date: 2026-10-20 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_create_project_attachments'
down_revision: Union[str, None] = '001_create_revoked_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        insp = sa.inspect(bind)
        if "project_management" not in insp.get_schema_names():
            op.execute("CREATE SCHEMA IF NOT EXISTS project_management")

        existing_tables = insp.get_table_names(schema="project_management")
        if "project_attachments" not in existing_tables:
            op.execute("""
                CREATE TABLE project_management.project_attachments (
                    attachment_id BIGSERIAL PRIMARY KEY,
                    project_id BIGINT NOT NULL REFERENCES project_management.projects (project_id) ON DELETE CASCADE,
                    uploaded_by BIGINT NOT NULL REFERENCES identity.users (user_id),
                    original_filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_size BIGINT NOT NULL,
                    content_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
                    category VARCHAR(50) NOT NULL DEFAULT 'ADVISORY_REFERENCE',
                    storage_path VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            op.execute("""
                CREATE INDEX ix_project_management_attachments_project_id
                ON project_management.project_attachments (project_id)
            """)
    else:
        # SQLite or other fallback
        insp = sa.inspect(bind)
        existing_tables = insp.get_table_names()
        if "project_attachments" not in existing_tables:
            op.execute("""
                CREATE TABLE project_attachments (
                    attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects (project_id) ON DELETE CASCADE,
                    uploaded_by INTEGER NOT NULL REFERENCES users (user_id),
                    original_filename VARCHAR(255) NOT NULL,
                    stored_filename VARCHAR(255) NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
                    category VARCHAR(50) NOT NULL DEFAULT 'ADVISORY_REFERENCE',
                    storage_path VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            op.execute("""
                CREATE INDEX ix_project_attachments_project_id
                ON project_attachments (project_id)
            """)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        insp = sa.inspect(bind)
        if "project_attachments" in insp.get_table_names(schema="project_management"):
            op.execute("DROP TABLE project_management.project_attachments CASCADE")
    else:
        insp = sa.inspect(bind)
        if "project_attachments" in insp.get_table_names():
            op.execute("DROP TABLE project_attachments")
