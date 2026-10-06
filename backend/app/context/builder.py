from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Chunk, IngestionJob, Document


def expand_to_parents(
    db: Session,
    results: list[dict],
) -> list[dict]:
    """
    Convert retrieved child chunks into richer context objects.

    Retrieval happens on child chunks because they are smaller and
    more precise.

    The parent chunk is then fetched to provide surrounding context
    to the LLM.

    The returned context preserves:
    - matched child text
    - parent text
    - document metadata
    - retrieval/reranking metadata
    """

    if not results:
        return []

    parent_ids = []

    for result in results:
        parent_id = result.get("parent_id")

        if parent_id is not None:
            parent_ids.append(parent_id)

    if not parent_ids:
        return []

    unique_parent_ids = list(
        dict.fromkeys(parent_ids)
    )

    rows = db.execute(
        select(Chunk, IngestionJob, Document)
        .join(
            IngestionJob,
            Chunk.ingestion_job_id == IngestionJob.id,
        )
        .join(
            Document,
            IngestionJob.document_id == Document.id,
        )
        .where(
            Chunk.id.in_(unique_parent_ids)
        )
    ).all()

    parent_by_id = {}

    for chunk, _jobs, document in rows:
        parent_by_id[str(chunk.id)] = {
            "chunk": chunk,
            "document": document,
        }

    expanded_results = []
    seen_parent_ids = set()

    for result in results:

        parent_id = result.get("parent_id")

        if parent_id is None:
            continue

        parent_id_str = str(parent_id)

        if parent_id_str in seen_parent_ids:
            continue

        parent_data = parent_by_id.get(parent_id_str)

        if parent_data is None:
            continue

        parent = parent_data["chunk"]
        document = parent_data["document"]

        seen_parent_ids.add(parent_id_str)

        expanded_results.append(
            {
                # Document metadata
                "document_id": str(document.id),
                "filename": document.filename,

                # Parent metadata
                "parent_id": parent_id_str,
                "parent_text": parent.text,
                "page": parent.page,
                "section": parent.section,
                "position": parent.position,

                # Matched child
                "matched_child_id": result["chunk_id"],
                "matched_child_text": result["text"],

                # Retrieval scores
                "rrf_score": result.get("rrf_score"),
                "rerank_score": result.get("rerank_score"),

                # Retrieval ranks
                "dense_rank": result.get("dense_rank"),
                "bm25_rank": result.get("bm25_rank"),
                "neural_sparse_rank": result.get(
                    "neural_sparse_rank"
                ),
            }
        )

    return expanded_results