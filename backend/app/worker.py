import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import redis
from sqlalchemy import select

from .config import STORAGE_DIR
from .db import SessionLocal
from .embeddings import embed_documents
from .ingestion.chunker import (
    create_child_chunks,
    create_parent_chunks,
)
from .ingestion.parser import extract_pages
from .ingestion.structure import detect_sections
from .models import Chunk, Document, IngestionJob
from .retrieval.indexer import index_document_chunks

# --------------------------------------------------
# Redis configuration
# --------------------------------------------------

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

QUEUE_NAME = "document_ingestion"


redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,
)


# --------------------------------------------------
# Process one ingestion job
# --------------------------------------------------


def process_job(job_id: str) -> None:
    db = SessionLocal()

    try:
        # --------------------------------------------
        # 1. Get ingestion job
        # --------------------------------------------

        job = db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))

        if job is None:
            print(
                f"Job {job_id} not found",
                flush=True,
            )
            return

        # --------------------------------------------
        # 2. Get document
        # --------------------------------------------

        document = db.scalar(select(Document).where(Document.id == job.document_id))

        if document is None:
            job.status = "FAILED"
            job.error_message = "QUEUED: Document not found"
            job.completed_at = datetime.now(timezone.utc)

            db.commit()
            return

        # --------------------------------------------
        # 3. Mark job as started (first step: PARSING)
        #
        # Each status is committed BEFORE its step runs, so
        # if a step fails, the committed status tells us
        # which step it was (used in the error handler).
        # --------------------------------------------

        job.status = "PARSING"
        job.started_at = datetime.now(timezone.utc)

        db.commit()

        print(
            f"Processing document {document.id}: " f"{document.filename}",
            flush=True,
        )

        # --------------------------------------------
        # 4. Resolve document path
        # --------------------------------------------

        file_path = Path(STORAGE_DIR) / document.storage_key

        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        # --------------------------------------------
        # 5. Parse PDF (status is already PARSING)
        # --------------------------------------------

        print(
            f"Parsing {document.filename}...",
            flush=True,
        )

        pages = extract_pages(file_path)

        if not pages:
            raise ValueError("No text could be extracted from the PDF")

        print(
            f"Extracted {len(pages)} pages",
            flush=True,
        )

        # --------------------------------------------
        # 6. Chunk document
        # --------------------------------------------

        job.status = "CHUNKING"
        db.commit()

        print(
            "Creating sections and chunks...",
            flush=True,
        )

        sections = detect_sections(pages)

        parents = create_parent_chunks(sections)

        children = create_child_chunks(parents)

        print(
            f"Pages: {len(pages)} | "
            f"Parents: {len(parents)} | "
            f"Children: {len(children)}",
            flush=True,
        )

        if not children:
            raise ValueError("No child chunks were created from the document")

        # --------------------------------------------
        # 7. Generate embeddings
        # --------------------------------------------

        job.status = "EMBEDDING"
        db.commit()

        print(
            f"Generating embeddings for " f"{len(children)} child chunks...",
            flush=True,
        )

        child_texts = [child["text"] for child in children]

        embeddings = embed_documents(child_texts)

        print(
            f"Generated {len(embeddings)} embeddings",
            flush=True,
        )

        # --------------------------------------------
        # 8. Validate embedding count
        # --------------------------------------------

        if len(embeddings) != len(children):
            raise ValueError(
                f"Embedding count mismatch: "
                f"{len(embeddings)} embeddings "
                f"for {len(children)} children"
            )

        # --------------------------------------------
        # 9. Validate embedding dimensions
        # --------------------------------------------

        expected_dimension = 768

        for index, embedding in enumerate(embeddings):
            if len(embedding) != expected_dimension:
                raise ValueError(
                    f"Invalid embedding dimension "
                    f"for child {index}: "
                    f"expected {expected_dimension}, "
                    f"got {len(embedding)}"
                )

        print(
            f"Embedding dimension verified: " f"{expected_dimension}",
            flush=True,
        )

        # --------------------------------------------
        # 10. Create parent chunk rows
        # --------------------------------------------

        parent_rows = []

        for index, parent_data in enumerate(parents):
            parent = Chunk(
                ingestion_job_id=job.id,
                parent_id=None,
                text=parent_data["text"],
                page=parent_data["page"],
                section=parent_data["section"],
                position=index,
            )

            db.add(parent)

            parent_rows.append(parent)

        # --------------------------------------------
        # 11. Flush parents
        #
        # This gives parent rows their UUIDs so
        # children can reference them.
        # --------------------------------------------

        db.flush()

        # --------------------------------------------
        # 12. Create child rows + embeddings
        # --------------------------------------------

        for index, child_data in enumerate(children):
            parent = parent_rows[child_data["parent_index"]]

            child = Chunk(
                ingestion_job_id=job.id,
                parent_id=parent.id,
                text=child_data["text"],
                page=child_data["page"],
                section=child_data["section"],
                position=child_data["position"],
                embedding=embeddings[index],
            )

            db.add(child)

        # --------------------------------------------
        # 13. Commit chunks + embeddings
        # --------------------------------------------

        db.commit()

        print(
            f"Created {len(parents)} parent chunks "
            f"and {len(children)} child chunks "
            f"with embeddings for "
            f"{document.filename}",
            flush=True,
        )

        # --------------------------------------------
        # 14. Index child chunks into OpenSearch
        # --------------------------------------------

        job.status = "INDEXING"
        db.commit()

        print(
            f"Indexing {len(children)} child chunks " f"into OpenSearch...",
            flush=True,
        )

        indexed_count = index_document_chunks(
            db=db,
            ingestion_job_id=job.id,
        )

        print(
            f"Indexed {indexed_count} chunks into OpenSearch",
            flush=True,
        )

        # --------------------------------------------
        # 15. Mark job successful
        # --------------------------------------------

        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)

        db.commit()

        print(
            f"Job {job.id} completed successfully",
            flush=True,
        )

    # --------------------------------------------
    # Error handling
    # --------------------------------------------

    except Exception as exc:

        db.rollback()

        try:
            job = db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))

            if job:
                # After rollback, job.status is the last COMMITTED
                # step, i.e. the step that was running when it failed.
                # Record it BEFORE overwriting the status with FAILED.
                job.error_message = f"{job.status}: {exc}"
                job.status = "FAILED"
                job.completed_at = datetime.now(timezone.utc)

                db.commit()

        except Exception as failure_exc:

            print(
                f"Failed to update failed job " f"{job_id}: {failure_exc}",
                flush=True,
            )

        print(
            f"Job {job_id} failed: {exc}",
            flush=True,
        )

    # --------------------------------------------
    # Always close DB session
    # --------------------------------------------

    finally:
        db.close()


# --------------------------------------------------
# Worker main loop
# --------------------------------------------------


def main():

    print(
        "Ingestion worker started",
        flush=True,
    )

    print(
        f"Listening on Redis queue: {QUEUE_NAME}",
        flush=True,
    )

    while True:

        try:

            # BLPOP blocks until a job is available.
            result = redis_client.blpop(
                QUEUE_NAME,
                timeout=0,
            )

            if result is None:
                continue

            # Redis returns:
            #
            # (
            #     queue_name,
            #     message
            # )
            #
            _, message = result

            # ----------------------------------------
            # Parse queue message
            # ----------------------------------------

            payload = json.loads(message)

            job_id = payload["job_id"]

            print(
                f"Received ingestion job: {job_id}",
                flush=True,
            )

            # ----------------------------------------
            # Process job
            # ----------------------------------------

            process_job(job_id)

        # --------------------------------------------
        # Redis errors
        # --------------------------------------------

        except redis.exceptions.RedisError as exc:

            print(
                f"Redis error: {exc}",
                flush=True,
            )

            time.sleep(5)

        # --------------------------------------------
        # Unexpected worker errors
        # --------------------------------------------

        except Exception as exc:

            print(
                f"Unexpected worker error: {exc}",
                flush=True,
            )

            time.sleep(5)


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    main()
