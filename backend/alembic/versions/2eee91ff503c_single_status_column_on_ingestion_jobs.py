"""single status column on ingestion_jobs

Revision ID: 2eee91ff503c
Revises: eae273067e6b
Create Date: 2026-10-07 08:39:55.569931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2eee91ff503c'
down_revision: Union[str, Sequence[str], None] = 'eae273067e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


job_status = sa.Enum(
    'QUEUED',
    'PARSING',
    'CHUNKING',
    'EMBEDDING',
    'INDEXING',
    'COMPLETED',
    'FAILED',
    name='job_status',
)


def upgrade() -> None:
    """Fold stage into status, convert status to an enum, drop old columns."""

    # 1. Finished jobs: SUCCESS -> COMPLETED
    op.execute(
        """
        UPDATE ingestion_jobs
        SET status = 'COMPLETED'
        WHERE status = 'SUCCESS'
        """
    )

    # 2. Running jobs: the stage becomes the status
    op.execute(
        """
        UPDATE ingestion_jobs
        SET status = stage
        WHERE status = 'PROCESSING'
          AND stage IS NOT NULL
        """
    )

    # 3. Failed jobs: keep the failing step inside the error message
    op.execute(
        """
        UPDATE ingestion_jobs
        SET error_message = stage || ': ' || error_message
        WHERE status = 'FAILED'
          AND stage IS NOT NULL
          AND error_message IS NOT NULL
        """
    )

    # 4. Create the Postgres enum type
    job_status.create(op.get_bind())

    # 5. Convert the column from VARCHAR to the enum.
    #    Fails if any row still holds a value outside the enum.
    op.execute(
        """
        ALTER TABLE ingestion_jobs
        ALTER COLUMN status TYPE job_status
        USING status::job_status
        """
    )

    # 6. Drop the columns we no longer need
    op.drop_column('ingestion_jobs', 'stage')
    op.drop_column('documents', 'status')


def downgrade() -> None:
    """
    Re-create the old columns.

    This is lossy: the old stage/status values cannot be reconstructed.
    """

    op.execute(
        """
        ALTER TABLE ingestion_jobs
        ALTER COLUMN status TYPE VARCHAR(30)
        USING status::text
        """
    )

    job_status.drop(op.get_bind())

    op.add_column(
        'documents',
        sa.Column(
            'status',
            sa.String(length=30),
            nullable=False,
            server_default='UPLOADED',
        ),
    )

    op.add_column(
        'ingestion_jobs',
        sa.Column('stage', sa.String(length=50), nullable=True),
    )
