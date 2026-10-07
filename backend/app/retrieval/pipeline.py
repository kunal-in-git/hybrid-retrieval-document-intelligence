import time

from sqlalchemy.orm import Session

from ..context.builder import expand_to_parents
from ..generation.llm import generate_answer
from .bm25 import bm25_search
from .dense import dense_search
from .fusion import rrf_fusion
from .neural_sparse import neural_sparse_search
from .reranker import rerank


# Cross-encoder (ms-marco-MiniLM) scores are logits.
# Observed: relevant passages score about -5 to +8, junk about -10 to -11.
# Results below this score are not sent to the LLM.
MIN_RERANK_SCORE = -7.0

def hybrid_search(
    db: Session,
    query: str,
    retrieval_top_k: int = 10,
    rerank_top_k: int = 5,
    context_top_k: int = 5,
):
    # =========================================================
    # TOTAL END-TO-END TIMER
    # =========================================================

    total_start_time = time.perf_counter()

    # =========================================================
    # 1. Dense Retrieval
    # =========================================================

    start_time = time.perf_counter()

    dense_results = dense_search(
        db=db,
        query=query,
        top_k=retrieval_top_k,
    )

    dense_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # 2. BM25 Retrieval
    # =========================================================

    start_time = time.perf_counter()

    bm25_results = bm25_search(
        query=query,
        top_k=retrieval_top_k,
    )

    bm25_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # 3. Neural Sparse Retrieval
    # =========================================================

    start_time = time.perf_counter()

    neural_sparse_results = neural_sparse_search(
        query=query,
        top_k=retrieval_top_k,
    )

    neural_sparse_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # 4. RRF Fusion
    # =========================================================

    start_time = time.perf_counter()

    fused_results = rrf_fusion(
        result_lists={
            "dense": dense_results,
            "bm25": bm25_results,
            "neural_sparse": neural_sparse_results,
        },
        k=60,
        top_k=retrieval_top_k,
    )

    fusion_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # 5. Cross-Encoder Reranking
    # =========================================================

    start_time = time.perf_counter()

    reranked_results = rerank(
        query=query,
        results=fused_results,
        top_k=rerank_top_k,
    )

    reranking_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # 6. Parent Context Expansion
    # =========================================================

    start_time = time.perf_counter()

    # Only results the cross-encoder considers relevant become context.
    # reranked_results itself is kept unfiltered for evaluation/inspection.
    relevant_results = [
        result
        for result in reranked_results
        if result["rerank_score"] >= MIN_RERANK_SCORE
    ]

    parent_results = expand_to_parents(
        db=db,
        results=relevant_results,
    )[:context_top_k]

    parent_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # RETRIEVAL TOTAL
    #
    # Retrieval ends after parent context preparation.
    # =========================================================

    retrieval_total_latency_ms = (
        dense_latency_ms
        + bm25_latency_ms
        + neural_sparse_latency_ms
        + fusion_latency_ms
        + reranking_latency_ms
        + parent_latency_ms
    )

    # =========================================================
    # 7. AI / LLM Answer Generation
    # =========================================================

    start_time = time.perf_counter()

    answer = generate_answer(
        query=query,
        contexts=parent_results,
    )

    answer_latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    # =========================================================
    # TOTAL END-TO-END TIME
    #
    # From beginning of query until AI answer is generated.
    # =========================================================

    total_latency_ms = (
        time.perf_counter() - total_start_time
    ) * 1000

    # =========================================================
    # RETURN
    # =========================================================

    return {
        "query": query,

        "dense_results": dense_results,

        "bm25_results": bm25_results,

        "neural_sparse_results": neural_sparse_results,

        "fused_results": fused_results,

        "reranked_results": reranked_results,

        "contexts": parent_results,

        "answer": answer,

        "latency": {
            # Individual retrieval stages
            "dense_ms": dense_latency_ms,
            "bm25_ms": bm25_latency_ms,
            "neural_sparse_ms": neural_sparse_latency_ms,
            "rrf_ms": fusion_latency_ms,
            "rerank_ms": reranking_latency_ms,
            "parent_ms": parent_latency_ms,

            # Total retrieval
            "retrieval_total_ms": retrieval_total_latency_ms,

            # AI generation
            "answer_ms": answer_latency_ms,

            # Complete RAG pipeline
            "total_ms": total_latency_ms,
        },
    }