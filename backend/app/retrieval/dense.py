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
    """

    if not query.strip():
        return []

    # --------------------------------------------
    # 1. Convert query into embedding
    # --------------------------------------------

    query_embedding = embed_query(query)

    # --------------------------------------------
    # 2. Search pgvector
    #
    # <=> = cosine distance
    #
    # Smaller distance = more similar
    # --------------------------------------------

    sql = text(
        """
        SELECT
            id,
            parent_id,
            text,
            page,
            section,
            position,
            embedding <=> CAST(:query_embedding AS vector)
                AS distance
        FROM chunks
        WHERE embedding IS NOT NULL
          AND parent_id IS NOT NULL
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
        """
    )

    rows = db.execute(
        sql,
        {
            "query_embedding": str(query_embedding),
            "top_k": top_k,
        },
    ).mappings().all()

    # --------------------------------------------
    # 3. Convert database rows to dictionaries
    # --------------------------------------------

    results = []

    for row in rows:
        results.append(
            {
                "chunk_id": str(row["id"]),
                "parent_id": str(row["parent_id"])
                if row["parent_id"]
                else None,
                "text": row["text"],
                "page": row["page"],
                "section": row["section"],
                "position": row["position"],
                "distance": float(row["distance"]),
            }
        )

    return results