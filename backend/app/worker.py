import json
import os
import time
from datetime import datetime, timezone

import redis
from sqlalchemy import select

from .db import SessionLocal
from .models import Chunk, IngestionJob, Document
from pathlib import Path

from .config import STORAGE_DIR
from .ingestion.parser import extract_pages
from .ingestion.chunker import create_chunks

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,
)

QUEUE_NAME = "document_ingestion"

def process_job(job_id: str) -> None:
    db = SessionLocal()

    try:
        job = db.scalar(select(IngestionJob).where(IngestionJob.id == job_id))

        if job is None:
            print(
                f"Job {job_id} not found",
                flush=True,
            )
            return

        document = db.scalar(select(Document).where(Document.id == job.document_id))

        if document is None:
            job.status = "FAILED"
            job.error_message = "Document not found"
            db.commit()
            return

        job.status = "PROCESSING"
        job.stage = "PARSING"
        job.started_at = datetime.now(timezone.utc)

        document.status = "PROCESSING"

        db.commit()

        print(
            f"Processing document {document.id}",
            flush=True,
        )

        file_path = Path(STORAGE_DIR) / document.storage_key

        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        job.stage = "PARSING"
        db.commit()

        pages = extract_pages(file_path)

        print(
            f"Extracted {len(pages)} pages from {document.filename}",
            flush=True,
        )

        job.stage = "CHUNKING"
        db.commit()

        chunks = create_chunks(pages)

        for chunk_data in chunks:
            chunk = Chunk(
                ingestion_job_id=job.id,
                parent_id=None,
                text=chunk_data["text"],
                page=chunk_data["page"],
                section=chunk_data["section"],
                position=chunk_data["position"],
            )

            db.add(chunk)

        db.commit()

        print(
            f"Created {len(chunks)} chunks from {document.filename}",
            flush=True,
        )

        job.status = "SUCCESS"
        job.stage = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)

        document.status = "READY"

        db.commit()

        print(
            f"Job {job.id} completed",
            flush=True,
        )

    except Exception as exc:
        db.rollback()

        try:
            job = db.scalar(
                select(IngestionJob).where(
                    IngestionJob.id == job_id
                )
            )

            if job:
                job.status = "FAILED"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)

                document = db.scalar(
                    select(Document).where(
                        Document.id == job.document_id
                    )
                )

                if document:
                    document.status = "FAILED"

                db.commit()

        except Exception as failure_exc:
            print(
                f"Failed to update failed job {job_id}: {failure_exc}",
                flush=True,
            )

        print(
            f"Job {job_id} failed: {exc}",
            flush=True,
        )

    finally:
        db.close()

def main():
    print(
        "Ingestion worker started",
        flush=True,
    )

    while True:
        try:
            result = redis_client.blpop(
                QUEUE_NAME,
                timeout=0,
            )

            if result is None:
                continue

            _, message = result

            payload = json.loads(message)

            job_id = payload["job_id"]

            process_job(job_id)

        except redis.exceptions.RedisError as exc:
            print(
                f"Redis error: {exc}",
                flush=True,
            )

            time.sleep(5)

        except Exception as exc:
            print(
                f"Unexpected worker error: {exc}",
                flush=True,
            )

            time.sleep(5)

if __name__ == "__main__":
    main()
