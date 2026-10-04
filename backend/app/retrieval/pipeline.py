from sqlalchemy.orm import Session

from .dense import dense_search
from ..context.builder import expand_to_parents


def dense_retrieval(
    db: Session,
    query: str,
    child_top_k: int = 10,
    parent_top_k: int = 5,
) -> list[dict]:
    """
    Complete dense retrieval pipeline.

    Query
      ↓
    Query embedding
      ↓
    pgvector child search
      ↓
    Parent expansion
      ↓
    Top parent contexts
    """

    # --------------------------------------------
    # 1. Retrieve child chunks
    # --------------------------------------------

    child_results = dense_search(
        db=db,
        query=query,
        top_k=child_top_k,
    )

    if not child_results:
        return []

    # --------------------------------------------
    # 2. Expand children to parents
    # --------------------------------------------

    parent_results = expand_to_parents(
        db=db,
        results=child_results,
    )

    # --------------------------------------------
    # 3. Limit final parent contexts
    # --------------------------------------------

    return parent_results[:parent_top_k]