"""add vector hnsw index

Revision ID: eae273067e6b
Revises: 7c3e1f9a2b4d
Create Date: 2026-10-04 10:49:23.775140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eae273067e6b'
down_revision: Union[str, Sequence[str], None] = '7c3e1f9a2b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade():
    op.execute(
        """
        DROP INDEX IF EXISTS ix_chunks_embedding_hnsw
        """
    )