import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Document
from ..retrieval.pipeline import hybrid_search

from .dataset import EVAL_DATASET
from .metrics import recall_at_k, reciprocal_rank

STAGES = [
    "dense",
    "bm25",
    "neural_sparse",
    "rrf",
    "reranked",
]


def resolve_document_ids(
    db: Session,
    filenames: list[str],
) -> list[str]:
    """
    Resolve evaluation document filenames to the
    current Document UUIDs in the database.
    """

    if not filenames:
        return []

    documents = db.scalars(
        select(Document).where(Document.filename.in_(filenames))
    ).all()

    return [str(document.id) for document in documents]


def evaluate(
    db: Session,
    retrieval_top_k: int = 10,
    evaluation_k: int = 5,
) -> dict:
    """
    Run the retrieval pipeline once per evaluation query
    and calculate retrieval metrics and latency.
    """

    per_query_results = []

    # Dynamic metric key
    recall_key = f"recall@{evaluation_k}"

    # --------------------------------------------------
    # Run retrieval once for every query
    # --------------------------------------------------

    for item in EVAL_DATASET:

        query = item["query"]

        # Human-readable ground truth
        relevant_filenames = item["relevant_documents"]

        # Resolve filenames to database UUIDs
        relevant_documents = resolve_document_ids(
            db=db,
            filenames=relevant_filenames,
        )

        # Prevent silent zero scores
        if not relevant_documents:
            raise ValueError(
                "No documents found for evaluation " f"filenames: {relevant_filenames}"
            )

        # --------------------------------------------------
        # Start TOTAL question timer
        # --------------------------------------------------

        question_start_time = time.perf_counter()

        # --------------------------------------------------
        # Run retrieval ONCE
        # --------------------------------------------------

        retrieval = hybrid_search(
            db=db,
            query=query,
            retrieval_top_k=retrieval_top_k,
            rerank_top_k=retrieval_top_k,
        )

        # --------------------------------------------------
        # Total question time
        #
        # This includes everything inside hybrid_search:
        # Dense
        # BM25
        # Neural Sparse
        # RRF
        # Reranking
        # Parent expansion
        # LLM answer generation
        # --------------------------------------------------

        question_total_latency_ms = (time.perf_counter() - question_start_time) * 1000

        # --------------------------------------------------
        # Get detailed retrieval timings
        # from hybrid_search()
        # --------------------------------------------------

        latency = retrieval.get(
            "latency",
            {},
        )

        dense_latency_ms = latency.get(
            "dense_ms",
            0.0,
        )

        bm25_latency_ms = latency.get(
            "bm25_ms",
            0.0,
        )

        neural_sparse_latency_ms = latency.get(
            "neural_sparse_ms",
            0.0,
        )

        rrf_latency_ms = latency.get(
            "rrf_ms",
            0.0,
        )

        rerank_latency_ms = latency.get(
            "rerank_ms",
            0.0,
        )

        parent_latency_ms = latency.get(
            "parent_ms",
            0.0,
        )

        retrieval_total_latency_ms = latency.get(
            "retrieval_total_ms",
            0.0,
        )

        answer_latency_ms = latency.get(
            "answer_ms",
            0.0,
        )

        pipeline_total_latency_ms = latency.get(
            "total_ms",
            0.0,
        )

        # --------------------------------------------------
        # Debug output
        # --------------------------------------------------

        print()
        print("=" * 80)
        print(f"QUERY: {query}")

        print("EXPECTED FILENAMES: " f"{relevant_filenames}")

        print("RESOLVED DOCUMENT IDS: " f"{relevant_documents}")

        # --------------------------------------------------
        # Timing output
        # --------------------------------------------------

        print()
        print("RETRIEVAL LATENCY:")

        print(f"  Dense Retrieval:       " f"{dense_latency_ms:.2f} ms")

        print(f"  BM25 Retrieval:        " f"{bm25_latency_ms:.2f} ms")

        print(f"  Neural Sparse:         " f"{neural_sparse_latency_ms:.2f} ms")

        print(f"  RRF Fusion:            " f"{rrf_latency_ms:.2f} ms")

        print(f"  Cross-Encoder Rerank:  " f"{rerank_latency_ms:.2f} ms")

        print(f"  Parent Expansion:      " f"{parent_latency_ms:.2f} ms")

        print(f"  -------------------------------")

        print(f"  TOTAL RETRIEVAL:       " f"{retrieval_total_latency_ms:.2f} ms")

        print(f"  LLM ANSWER:            " f"{answer_latency_ms:.2f} ms")

        print(f"  PIPELINE TOTAL:        " f"{pipeline_total_latency_ms:.2f} ms")

        print(f"  TOTAL QUESTION TIME:   " f"{question_total_latency_ms:.2f} ms")

        # --------------------------------------------------
        # Dense results
        # --------------------------------------------------

        print("\nDENSE TOP RESULTS:")

        for result in retrieval["dense_results"][:5]:

            print(f"  {result.get('document_id')} | " f"{result.get('filename')}")

        # --------------------------------------------------
        # BM25 results
        # --------------------------------------------------

        print("\nBM25 TOP RESULTS:")

        for result in retrieval["bm25_results"][:5]:

            print(f"  {result.get('document_id')} | " f"{result.get('filename')}")

        # --------------------------------------------------
        # Neural Sparse results
        # --------------------------------------------------

        print("\nNEURAL SPARSE TOP RESULTS:")

        for result in retrieval["neural_sparse_results"][:5]:

            print(f"  {result.get('document_id')} | " f"{result.get('filename')}")

        # --------------------------------------------------
        # RRF results
        # --------------------------------------------------

        print("\nRRF TOP RESULTS:")

        for result in retrieval["fused_results"][:5]:

            print(f"  {result.get('document_id')} | " f"{result.get('filename')}")

        # --------------------------------------------------
        # Reranked results
        # --------------------------------------------------

        print("\nRERANKED TOP RESULTS:")

        for result in retrieval["reranked_results"][:5]:

            print(f"  {result.get('document_id')} | " f"{result.get('filename')}")

        # --------------------------------------------------
        # Organize retrieval stages
        # --------------------------------------------------

        stages = {
            "dense": retrieval["dense_results"],
            "bm25": retrieval["bm25_results"],
            "neural_sparse": retrieval["neural_sparse_results"],
            "rrf": retrieval["fused_results"],
            "reranked": retrieval["reranked_results"],
        }

        # --------------------------------------------------
        # Store per-query evaluation result
        # --------------------------------------------------

        query_result = {
            "query": query,
            "relevant_documents": (relevant_filenames),
            "relevant_document_ids": (relevant_documents),
            # Total time for this question
            "question_total_latency_ms": (question_total_latency_ms),
            # Detailed retrieval timings
            "latency": {
                "dense_ms": dense_latency_ms,
                "bm25_ms": bm25_latency_ms,
                "neural_sparse_ms": (neural_sparse_latency_ms),
                "rrf_ms": rrf_latency_ms,
                "rerank_ms": rerank_latency_ms,
                "parent_ms": parent_latency_ms,
                "retrieval_total_ms": retrieval_total_latency_ms,
                "answer_ms": answer_latency_ms,
                "total_ms": pipeline_total_latency_ms,
            },
            "stages": {},
        }

        # --------------------------------------------------
        # Calculate metrics
        # --------------------------------------------------

        for stage_name in STAGES:

            results = stages[stage_name]

            recall = recall_at_k(
                results=results,
                relevant_documents=(relevant_documents),
                k=evaluation_k,
            )

            mrr = reciprocal_rank(
                results=results,
                relevant_documents=(relevant_documents),
            )

            query_result["stages"][stage_name] = {
                recall_key: recall,
                "mrr": mrr,
                "results": results,
            }

        per_query_results.append(query_result)

    # --------------------------------------------------
    # Aggregate metrics
    # --------------------------------------------------

    aggregate = {}

    for stage_name in STAGES:

        recalls = [item["stages"][stage_name][recall_key] for item in per_query_results]

        mrrs = [item["stages"][stage_name]["mrr"] for item in per_query_results]

        aggregate[stage_name] = {
            recall_key: (sum(recalls) / len(recalls) if recalls else 0.0),
            "mrr": (sum(mrrs) / len(mrrs) if mrrs else 0.0),
        }

    # --------------------------------------------------
    # Aggregate latency
    # --------------------------------------------------

    def average_latency(key: str) -> float:
        values = [
            item["latency"].get(
                key,
                0.0,
            )
            for item in per_query_results
        ]

        return sum(values) / len(values) if values else 0.0

    average_latencies = {
        "dense_ms": average_latency("dense_ms"),
        "bm25_ms": average_latency("bm25_ms"),
        "neural_sparse_ms": average_latency("neural_sparse_ms"),
        "rrf_ms": average_latency("rrf_ms"),
        "rerank_ms": average_latency("rerank_ms"),
        "parent_ms": average_latency("parent_ms"),
        "retrieval_total_ms": average_latency("retrieval_total_ms"),
        "answer_ms": average_latency("answer_ms"),
        "total_ms": average_latency("total_ms"),
        "question_total_ms": (
            sum(item["question_total_latency_ms"] for item in per_query_results)
            / len(per_query_results)
            if per_query_results
            else 0.0
        ),
    }

    # --------------------------------------------------
    # Print aggregate latency
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("AVERAGE LATENCY ACROSS ALL QUESTIONS")
    print("=" * 80)

    print(f"Dense Retrieval:       " f"{average_latencies['dense_ms']:.2f} ms")

    print(f"BM25 Retrieval:        " f"{average_latencies['bm25_ms']:.2f} ms")

    print(f"Neural Sparse:         " f"{average_latencies['neural_sparse_ms']:.2f} ms")

    print(f"RRF Fusion:            " f"{average_latencies['rrf_ms']:.2f} ms")

    print(f"Cross-Encoder Rerank:  " f"{average_latencies['rerank_ms']:.2f} ms")

    print(f"Parent Expansion:      " f"{average_latencies['parent_ms']:.2f} ms")

    print(
        f"Average Retrieval:     " f"{average_latencies['retrieval_total_ms']:.2f} ms"
    )

    print(f"Average LLM Answer:    " f"{average_latencies['answer_ms']:.2f} ms")

    print(f"Average Pipeline:      " f"{average_latencies['total_ms']:.2f} ms")

    print(f"Average Question Time: " f"{average_latencies['question_total_ms']:.2f} ms")

    # --------------------------------------------------
    # Final evaluation output
    # --------------------------------------------------

    return {
        "aggregate": aggregate,
        "average_latency": (average_latencies),
        "per_query": per_query_results,
    }
