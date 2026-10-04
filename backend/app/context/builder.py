from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Chunk


def expand_to_parents(
    db: Session,
    results: list[dict],
) -> list[dict]:
    """
    Convert retrieved child chunks into their parent chunks.

    Child chunks are used for retrieval because they are smaller
    and more precise.

    Parent chunks are used for context because they provide more
    surrounding information to the LLM.
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

    # Remove duplicate parent IDs while preserving order.
    unique_parent_ids = list(
        dict.fromkeys(parent_ids)
    )

    parents = db.scalars(
        select(Chunk).where(
            Chunk.id.in_(unique_parent_ids)
        )
    ).all()

    # Convert database objects into lookup dictionary.
    parent_by_id = {
        str(parent.id): parent
        for parent in parents
    }

    expanded_results = []

    # Preserve the ranking order produced by retrieval.
    seen_parent_ids = set()

    for result in results:

        parent_id = result.get("parent_id")

        if parent_id is None:
            continue

        parent_id_str = str(parent_id)

        # Multiple child chunks can belong to the same
        # parent. We only want one parent context.
        if parent_id_str in seen_parent_ids:
            continue

        parent = parent_by_id.get(parent_id_str)

        if parent is None:
            continue

        seen_parent_ids.add(parent_id_str)

        expanded_results.append(
            {
                "parent_id": parent_id_str,
                "text": parent.text,
                "page": parent.page,
                "section": parent.section,
                "position": parent.position,

                # Keep the child that caused this parent
                # to be retrieved.
                "matched_child_id": result["chunk_id"],

                # Lower distance = better dense match.
                "distance": result.get("distance"),
            }
        )

    return expanded_results