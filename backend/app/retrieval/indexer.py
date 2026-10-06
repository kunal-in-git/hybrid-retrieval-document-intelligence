from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Chunk, Document, IngestionJob
from ..storage.opensearch import (
    INDEX_NAME,
    get_opensearch_client,
)


def index_document_chunks(
    db: Session,
    ingestion_job_id,
) -> int:
    """
    Index all child chunks belonging to an ingestion job
    into OpenSearch.

    PostgreSQL remains the source of truth.
    OpenSearch is the retrieval index.
    """

    client = get_opensearch_client()

    # --------------------------------------------
    # Find the ingestion job
    # --------------------------------------------

    job = db.scalar(
        select(IngestionJob).where(
            IngestionJob.id == ingestion_job_id
        )
    )

    if job is None:
        raise ValueError(
            f"Ingestion job {ingestion_job_id} not found"
        )

    document_id = job.document_id

    # --------------------------------------------
    # Find the document
    # --------------------------------------------

    document = db.scalar(
        select(Document).where(
            Document.id == document_id
        )
    )

    if document is None:
        raise ValueError(
            f"Document {document_id} not found"
        )

    # --------------------------------------------
    # Get child chunks
    # --------------------------------------------

    chunks = db.scalars(
        select(Chunk).where(
            Chunk.ingestion_job_id == ingestion_job_id,
            Chunk.parent_id.is_not(None),
        )
    ).all()

    if not chunks:
        return 0

    # --------------------------------------------
    # Index each child chunk
    # --------------------------------------------

    for chunk in chunks:

        body = {
            "chunk_id": str(chunk.id),
            "parent_id": str(chunk.parent_id),
            "document_id": str(document_id),
            "ingestion_job_id": str(ingestion_job_id),

            # Document metadata
            "filename": document.filename,

            # Chunk data
            "text": chunk.text,
            "page": chunk.page,
            "section": chunk.section,
            "position": chunk.position,
        }

        client.index(
            index=INDEX_NAME,
            id=str(chunk.id),
            body=body,
            pipeline="document_chunks_neural_sparse",
            refresh=False,
        )

    # --------------------------------------------
    # Make indexed documents searchable
    # --------------------------------------------

    client.indices.refresh(
        index=INDEX_NAME
    )

    return len(chunks)