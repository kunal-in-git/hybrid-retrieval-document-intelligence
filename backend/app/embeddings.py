import os

import ollama


OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "nomic-embed-text",
)

client = ollama.Client(
    host=OLLAMA_HOST,
)


def embed_documents(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for multiple document chunks.
    """

    if not texts:
        return []

    response = client.embed(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return response["embeddings"]


def embed_query(
    query: str,
) -> list[float]:
    """
    Generate an embedding for a user query.
    """

    response = client.embed(
        model=EMBEDDING_MODEL,
        input=query,
    )

    return response["embeddings"][0]