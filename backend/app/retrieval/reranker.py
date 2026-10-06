from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

reranker = CrossEncoder(MODEL_NAME)


def rerank(
    query: str,
    results: list[dict],
    top_k: int = 5,
) -> list[dict]:

    if not query.strip() or not results:
        return []

    pairs = [
        [query, result["text"]]
        for result in results
    ]

    scores = reranker.predict(pairs)

    reranked_results = []

    for result, score in zip(results, scores):
        item = result.copy()
        item["rerank_score"] = float(score)
        reranked_results.append(item)

    reranked_results.sort(
        key=lambda result: result["rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]