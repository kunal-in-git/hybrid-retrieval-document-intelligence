from sqlalchemy import text
from sqlalchemy.orm import Session

from ..embeddings import embed_query


def dense_search(
    db: Session,
    query: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Perform dense vector similarity search using pgvector.

    Flow:

        query
          ↓
        Ollama embedding
          ↓
        pgvector cosine distance
          ↓
        top-K child chunks
          ↓
        document metadata
    """

    # --------------------------------------------
    # 1. Validate query
    # --------------------------------------------

    if not query.strip():
        return []

    # --------------------------------------------
    # 2. Convert query into embedding
    # --------------------------------------------

    query_embedding = embed_query(query)

    # --------------------------------------------
    # 3. Search pgvector
    #
    # <=> = cosine distance
    #
    # Smaller distance = more similar
    # --------------------------------------------

    sql = text("""
        SELECT
            chunks.id,
            chunks.parent_id,
            chunks.text,
            chunks.page,
            chunks.section,
            chunks.position,

            documents.id AS document_id,
            documents.filename,

            chunks.embedding
                <=> CAST(:query_embedding AS vector)
                AS distance

        FROM chunks

        JOIN ingestion_jobs
            ON chunks.ingestion_job_id = ingestion_jobs.id

        JOIN documents
            ON ingestion_jobs.document_id = documents.id

        WHERE chunks.embedding IS NOT NULL
          AND chunks.parent_id IS NOT NULL

        ORDER BY
            chunks.embedding
                <=> CAST(:query_embedding AS vector)

        LIMIT :top_k
    """)

    rows = (
        db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "top_k": top_k,
            },
        )
        .mappings()
        .all()
    )

    # --------------------------------------------
    # 4. Convert database rows to dictionaries
    # --------------------------------------------

    results = []

    for row in rows:

        results.append(
            {
                # Chunk information
                "chunk_id": str(row["id"]),
                "parent_id": (
                    str(row["parent_id"])
                    if row["parent_id"] is not None
                    else None
                ),

                # Content
                "text": row["text"],

                # Location inside document
                "page": row["page"],
                "section": row["section"],
                "position": row["position"],

                # Document metadata
                "document_id": str(row["document_id"]),
                "filename": row["filename"],

                # Dense retrieval score
                "distance": float(row["distance"]),
            }
        )

    return results