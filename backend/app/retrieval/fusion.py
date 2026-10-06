from collections import defaultdict


def rrf_fusion(
    result_lists: dict[str, list[dict]],
    k: int = 60,
    top_k: int = 10,
) -> list[dict]:
    scores = defaultdict(float)
    result_by_chunk_id = {}
    ranks_by_chunk_id = defaultdict(dict)

    for retriever_name, results in result_lists.items():
        for rank, result in enumerate(results, start=1):
            chunk_id = result["chunk_id"]

            scores[chunk_id] += 1 / (k + rank)

            ranks_by_chunk_id[chunk_id][f"{retriever_name}_rank"] = rank

            if chunk_id not in result_by_chunk_id:
                result_by_chunk_id[chunk_id] = result.copy()

    ranked_chunks = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    fused_results = []

    for chunk_id, rrf_score in ranked_chunks[:top_k]:
        result = result_by_chunk_id[chunk_id].copy()

        result["rrf_score"] = rrf_score
        result.update(ranks_by_chunk_id[chunk_id])

        fused_results.append(result)

    return fused_results
