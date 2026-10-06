import os
from functools import lru_cache

from sentence_transformers import SparseEncoder


SPLADE_MODEL = os.getenv(
    "SPLADE_MODEL",
    "naver/splade-cocondenser-ensembledistil",
)


@lru_cache(maxsize=1)
def get_splade_model() -> SparseEncoder:
    """
    Load the SPLADE model once per process.

    The model is cached so we don't reload the ~439 MB
    model for every request.
    """

    print(
        f"Loading SPLADE model: {SPLADE_MODEL}",
        flush=True,
    )

    model = SparseEncoder(
        SPLADE_MODEL,
        device="cpu",
    )

    print(
        "SPLADE model loaded",
        flush=True,
    )

    return model


def _decode_embedding(
    model: SparseEncoder,
    embedding,
) -> dict[str, float]:
    """
    Convert a sparse tensor into:

        {
            "token": weight,
            ...
        }

    OpenSearch rank_features stores sparse
    token -> weight mappings.
    """

    decoded = model.decode(
        embedding,
        top_k=None,
    )

    return {
        token: float(weight)
        for token, weight in decoded
        if weight > 0
    }


def embed_splade_documents(
    texts: list[str],
) -> list[dict[str, float]]:
    """
    Generate SPLADE sparse embeddings for documents.
    """

    if not texts:
        return []

    model = get_splade_model()

    embeddings = model.encode_document(
        texts,
        batch_size=8,
        show_progress_bar=False,
        convert_to_tensor=False,
        convert_to_sparse_tensor=True,
    )

    return [
        _decode_embedding(
            model,
            embedding,
        )
        for embedding in embeddings
    ]


def embed_splade_query(
    query: str,
) -> dict[str, float]:
    """
    Generate a SPLADE sparse embedding for a query.
    """

    if not query.strip():
        return {}

    model = get_splade_model()

    embedding = model.encode_query(
        query,
        convert_to_tensor=True,
        convert_to_sparse_tensor=True,
    )

    return _decode_embedding(
        model,
        embedding,
    )