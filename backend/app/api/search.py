from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..context.builder import expand_to_parents
from ..db import get_db
from ..retrieval.dense import dense_search


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


@router.post("/dense")
def dense_search_endpoint(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    """
    Dense vector search endpoint.
    """

    child_results = dense_search(
        db=db,
        query=request.query,
        top_k=request.top_k,
    )

    parent_results = expand_to_parents(
        db=db,
        results=child_results,
    )

    return {
        "query": request.query,
        "children": child_results,
        "parents": parent_results,
    }