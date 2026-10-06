from ..storage.opensearch import (
    INDEX_NAME,
    get_opensearch_client,
)


def create_bm25_index() -> None:
    """
    Create the OpenSearch index used for BM25 retrieval.
    """

    client = get_opensearch_client()

    # --------------------------------------------
    # Do not recreate an existing index
    # --------------------------------------------

    if client.indices.exists(index=INDEX_NAME):
        print(
            f"OpenSearch index '{INDEX_NAME}' already exists.",
            flush=True,
        )
        return

    # --------------------------------------------
    # Index mapping
    # --------------------------------------------

    body = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "chunk_id": {
                    "type": "keyword",
                },
                "parent_id": {
                    "type": "keyword",
                },
                "document_id": {
                    "type": "keyword",
                },
                "ingestion_job_id": {
                    "type": "keyword",
                },
                "filename": {
                    "type": "keyword",
                },
                "text": {
                    "type": "text",
                },
                "page": {
                    "type": "integer",
                },
                "section": {
                    "type": "keyword",
                },
                "position": {
                    "type": "integer",
                },
            }
        },
    }

    client.indices.create(
        index=INDEX_NAME,
        body=body,
    )

    print(
        f"Created OpenSearch index '{INDEX_NAME}'.",
        flush=True,
    )


def bm25_search(
    query: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Perform BM25 lexical retrieval using OpenSearch.

    Flow:

        query
          ↓
        OpenSearch BM25
          ↓
        top-K child chunks
          ↓
        document metadata
    """

    # --------------------------------------------
    # 1. Validate query
    # --------------------------------------------

    if not query.strip():
        return []

    # --------------------------------------------
    # 2. Get OpenSearch client
    # --------------------------------------------

    client = get_opensearch_client()

    # --------------------------------------------
    # 3. Execute BM25 search
    # --------------------------------------------

    response = client.search(
        index=INDEX_NAME,
        body={
            "size": top_k,
            "query": {
                "match": {
                    "text": {
                        "query": query,
                    }
                }
            },
        },
    )

    # --------------------------------------------
    # 4. Convert OpenSearch results
    # --------------------------------------------

    results = []

    for hit in response["hits"]["hits"]:

        source = hit["_source"]

        results.append(
            {
                # Chunk information
                "chunk_id": source["chunk_id"],
                "parent_id": source.get("parent_id"),

                # Document metadata
                "document_id": source["document_id"],
                "filename": source.get("filename"),

                # Content
                "text": source["text"],

                # Location inside document
                "page": source.get("page"),
                "section": source.get("section"),
                "position": source.get("position"),

                # BM25 score
                "score": float(hit["_score"]),
            }
        )

    return results