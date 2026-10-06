from ..storage.opensearch import (
    INDEX_NAME,
    get_opensearch_client,
)


def neural_sparse_search(
    query: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Perform neural sparse retrieval using OpenSearch.

    Flow:

        query
          ↓
        Neural sparse encoding
          ↓
        OpenSearch sparse retrieval
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
    # 3. Execute neural sparse search
    # --------------------------------------------

    response = client.search(
        index=INDEX_NAME,
        body={
            "size": top_k,

            "_source": [
                "chunk_id",
                "parent_id",
                "document_id",
                "ingestion_job_id",
                "filename",
                "text",
                "page",
                "section",
                "position",
            ],

            "query": {
                "neural_sparse": {
                    "sparse_embedding": {
                        "query_text": query,
                        "analyzer": "bert-uncased",
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
                "document_id": source.get("document_id"),
                "filename": source.get("filename"),
                "ingestion_job_id": source.get(
                    "ingestion_job_id"
                ),

                # Content
                "text": source["text"],

                # Location inside document
                "page": source.get("page"),
                "section": source.get("section"),
                "position": source.get("position"),

                # Neural sparse score
                "score": float(hit["_score"]),
            }
        )

    return results