import os

from opensearchpy import OpenSearch


OPENSEARCH_HOST = os.getenv(
    "OPENSEARCH_HOST",
    "http://opensearch:9200",
)

INDEX_NAME = os.getenv(
    "OPENSEARCH_INDEX",
    "document_chunks",
)


def get_opensearch_client() -> OpenSearch:
    """
    Create an OpenSearch client.
    """

    client = OpenSearch(
        hosts=[OPENSEARCH_HOST],
    )

    return client