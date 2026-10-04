"""add document_name to ingestion_jobs

Revision ID: 7c3e1f9a2b4d
Revises: 458a94bb90b2
Create Date: 2026-10-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7c3e1f9a2b4d'
down_revision: Union[str, Sequence[str], None] = '458a94bb90b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # A foreign key target must be unique.
    op.create_unique_constraint(
        'uq_documents_filename',
        'documents',
        ['filename'],
    )

    op.add_column(
        'ingestion_jobs',
        sa.Column('document_name', sa.String(length=255), nullable=True),
    )

    # Backfill existing jobs from their document.
    op.execute(
        """
        UPDATE ingestion_jobs
        SET document_name = documents.filename
        FROM documents
        WHERE documents.id = ingestion_jobs.document_id
        """
    )

    op.alter_column('ingestion_jobs', 'document_name', nullable=False)

    op.create_foreign_key(
        'fk_ingestion_jobs_document_name_documents',
        'ingestion_jobs',
        'documents',
        ['document_name'],
        ['filename'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_ingestion_jobs_document_name_documents',
        'ingestion_jobs',
        type_='foreignkey',
    )
    op.drop_column('ingestion_jobs', 'document_name')
    op.drop_constraint('uq_documents_filename', 'documents', type_='unique')
