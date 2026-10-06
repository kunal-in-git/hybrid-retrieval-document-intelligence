from sqlalchemy import select

from ..db import SessionLocal
from ..models import Document
from ..storage.opensearch import (
    INDEX_NAME,
    get_opensearch_client,
)


def backfill_filenames() -> None:
    """
    Backfill filename metadata in OpenSearch.

    PostgreSQL is the source of truth for document metadata.
    Existing neural sparse embeddings are preserved.
    """

    client = get_opensearch_client()

    db = SessionLocal()

    try:
        response = client.search(
            index=INDEX_NAME,
            body={
                "size": 1000,
                "_source": [
                    "chunk_id",
                    "document_id",
                    "filename",
                ],
                "query": {
                    "match_all": {}
                },
            },
        )

        hits = response["hits"]["hits"]

        print(
            f"Found {len(hits)} OpenSearch documents.",
            flush=True,
        )

        updated = 0
        skipped = 0
        missing_documents = 0

        for hit in hits:

            source = hit["_source"]

            chunk_id = source.get("chunk_id")
            document_id = source.get("document_id")

            if not document_id:
                print(
                    f"Skipping {chunk_id}: "
                    "missing document_id",
                    flush=True,
                )
                skipped += 1
                continue

            document = db.scalar(
                select(Document).where(
                    Document.id == document_id
                )
            )

            if document is None:
                print(
                    f"Skipping {chunk_id}: "
                    f"document {document_id} not found",
                    flush=True,
                )
                missing_documents += 1
                continue

            filename = document.filename

            client.update(
                index=INDEX_NAME,
                id=hit["_id"],
                body={
                    "doc": {
                        "filename": filename
                    }
                },
                refresh=False,
            )

            updated += 1

        client.indices.refresh(
            index=INDEX_NAME
        )

        print()
        print("=" * 60)
        print("OpenSearch filename backfill complete")
        print("=" * 60)
        print(f"Total documents : {len(hits)}")
        print(f"Updated         : {updated}")
        print(f"Skipped         : {skipped}")
        print(
            f"Missing DB docs : {missing_documents}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    backfill_filenames()