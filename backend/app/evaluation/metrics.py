def recall_at_k(
    results: list[dict],
    relevant_documents: list[str],
    k: int,
) -> float:
    """
    Document-level Recall@K.

    Returns 1.0 when at least one relevant document
    appears in the top-K results.
    """

    if not relevant_documents:
        return 0.0

    relevant_documents_set = set(
        relevant_documents
    )

    retrieved_documents = {
        result.get("document_id")
        for result in results[:k]
        if result.get("document_id") is not None
    }

    return float(
        bool(
            retrieved_documents
            & relevant_documents_set
        )
    )


def reciprocal_rank(
    results: list[dict],
    relevant_documents: list[str],
) -> float:
    """
    Reciprocal Rank.

    RR = 1 / rank of first relevant result.
    """

    if not relevant_documents:
        return 0.0

    relevant_documents_set = set(
        relevant_documents
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        if result.get("document_id") in relevant_documents_set:
            return 1.0 / rank

    return 0.0