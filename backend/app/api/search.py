from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..context.builder import expand_to_parents
from ..db import get_db
from ..retrieval.bm25 import bm25_search
from ..retrieval.dense import dense_search
from ..retrieval.pipeline import hybrid_search
from ..retrieval.neural_sparse import neural_sparse_search

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
    )


# ==================================================
# Dense Search
# ==================================================


@router.get("/dense")
def dense_search_endpoint(
    query: str,
    top_k: int = 10,
    db: Session = Depends(get_db),
):
    child_results = dense_search(
        db=db,
        query=query,
        top_k=top_k,
    )

    # parent_results = expand_to_parents(
    #     db=db,
    #     results=child_results,
    # )

    return {
        "query": query,
        "children": child_results,
        "parents": parent_results,
    }


# ==================================================
# BM25 Search
# ==================================================
@router.get("/bm25")
def bm25_search_endpoint(
    query: str,
    top_k: int = 10,
):
    results = bm25_search(
        query=query,
        top_k=top_k,
    )

    return {
        "query": query,
        "results": results,
    }


@router.get("/search/neural-sparse")
def search_neural_sparse(
    q: str,
    top_k: int = 10,
):
    return {
        "query": q,
        "results": neural_sparse_search(
            query=q,
            top_k=top_k,
        ),
    }


# ==================================================
# Hybrid Search
# ==================================================


@router.get("/hybrid")
def hybrid_search_endpoint(
    query: str,
    top_k: int = 10,
    db: Session = Depends(get_db),
):
    """
    Hybrid retrieval using:

        Dense Search
             +
        BM25 Search
             ↓
          RRF Fusion
             ↓
       Parent Expansion
             ↓
          Context
    """

    result = hybrid_search(
        db=db,
        query=query,
        retrieval_top_k=top_k,
        rerank_top_k=5,
    )

    return result
