import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Document, IngestionJob
from ..queue import enqueue_ingestion_job
from ..storage import calculate_sha256, save_file


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Validate filename
    # ---------------------------------------------------------
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    # ---------------------------------------------------------
    # 2. Validate file type
    # ---------------------------------------------------------
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # ---------------------------------------------------------
    # 3. Read file
    # ---------------------------------------------------------
    file_bytes = await file.read()

    # ---------------------------------------------------------
    # 4. Validate file size
    # ---------------------------------------------------------
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB limit",
        )

    # ---------------------------------------------------------
    # 5. Generate document ID for a new document
    # ---------------------------------------------------------
    document_id = uuid.uuid4()

    # ---------------------------------------------------------
    # 6. Sanitize filename
    # ---------------------------------------------------------
    safe_filename = Path(file.filename).name

    # ---------------------------------------------------------
    # 7. Create storage key
    # ---------------------------------------------------------
    storage_key = f"documents/{document_id}_{safe_filename}"

    # ---------------------------------------------------------
    # 8. Save uploaded file
    # ---------------------------------------------------------
    file_path = save_file(
        file_bytes,
        storage_key,
    )

    # ---------------------------------------------------------
    # 9. Calculate SHA-256 content hash
    # ---------------------------------------------------------
    content_hash = calculate_sha256(file_path)

    # ---------------------------------------------------------
    # 10. Check whether this content already exists
    # ---------------------------------------------------------
    existing_document = db.scalar(
        select(Document).where(
            Document.content_hash == content_hash
        )
    )

    # =========================================================
    # CASE 1: Document already exists
    # =========================================================
    if existing_document is not None:

        # -----------------------------------------------------
        # The document's state is its active job's status
        # -----------------------------------------------------
        active_job = None

        if existing_document.active_job_id is not None:
            active_job = db.get(
                IngestionJob,
                existing_document.active_job_id,
            )

        active_status = active_job.status if active_job else None

        # -----------------------------------------------------
        # Already successfully ingested
        # -----------------------------------------------------
        if active_status == "COMPLETED":

            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=409,
                detail=(
                    f"This document has already been successfully "
                    f"ingested as '{existing_document.filename}'"
                ),
            )

        # -----------------------------------------------------
        # Currently being ingested
        # -----------------------------------------------------
        if active_status in {
            "QUEUED",
            "PARSING",
            "CHUNKING",
            "EMBEDDING",
            "INDEXING",
        }:

            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=409,
                detail=(
                    f"This document is already being processed "
                    f"as '{existing_document.filename}'"
                ),
            )

        # -----------------------------------------------------
        # Previous attempt failed (or never started)
        #
        # Retry by creating a NEW job for the SAME document.
        # The original stored file is reused (same content hash),
        # so the newly uploaded duplicate is deleted.
        # -----------------------------------------------------
        file_path.unlink(missing_ok=True)

        job = IngestionJob(
            document_id=existing_document.id,
            document_name=existing_document.filename,
            status="QUEUED",
            retry_count=0,
        )

        db.add(job)
        db.flush()

        existing_document.active_job_id = job.id

        db.commit()

        try:
            enqueue_ingestion_job(str(job.id))

        except Exception as exc:
            job.status = "FAILED"
            job.error_message = (
                f"QUEUED: Failed to enqueue ingestion job: {exc}"
            )

            db.commit()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Document exists but the retry ingestion "
                    "job could not be queued"
                ),
            )

        return {
            "document_id": str(existing_document.id),
            "job_id": str(job.id),
            "filename": existing_document.filename,
            "content_hash": existing_document.content_hash,
            "status": job.status,
            "message": "Previous ingestion failed. A new ingestion job has been queued.",
        }

    # =========================================================
    # Filename already used by a DIFFERENT document
    #
    # documents.filename is UNIQUE (ingestion_jobs.document_name
    # references it), so inserting would fail with a 500.
    # =========================================================
    filename_taken = db.scalar(
        select(Document).where(
            Document.filename == safe_filename
        )
    )

    if filename_taken is not None:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=409,
            detail=(
                f"A different document named '{safe_filename}' "
                f"already exists. Rename the file and upload again."
            ),
        )

    # =========================================================
    # CASE 2: New document
    # =========================================================

    # ---------------------------------------------------------
    # 11. Create Document record
    # ---------------------------------------------------------
    document = Document(
        id=document_id,
        filename=safe_filename,
        storage_key=storage_key,
        content_hash=content_hash,
        file_size=len(file_bytes),
        mime_type=file.content_type,
    )

    db.add(document)
    db.flush()

    # ---------------------------------------------------------
    # 12. Create ingestion job
    # ---------------------------------------------------------
    job = IngestionJob(
        document_id=document.id,
        document_name=document.filename,
        status="QUEUED",
        retry_count=0,
    )

    db.add(job)
    db.flush()

    # ---------------------------------------------------------
    # 13. Set active job
    # ---------------------------------------------------------
    document.active_job_id = job.id

    # ---------------------------------------------------------
    # 14. Commit database transaction
    # ---------------------------------------------------------
    db.commit()

    # ---------------------------------------------------------
    # 15. Add job to Redis queue
    # ---------------------------------------------------------
    try:
        enqueue_ingestion_job(str(job.id))

    except Exception as exc:
        job.status = "FAILED"
        job.error_message = (
            f"QUEUED: Failed to enqueue ingestion job: {exc}"
        )

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Document uploaded but ingestion job "
                "could not be queued"
            ),
        )

    # ---------------------------------------------------------
    # 16. Return response
    # ---------------------------------------------------------
    return {
        "document_id": str(document.id),
        "job_id": str(job.id),
        "filename": document.filename,
        "content_hash": document.content_hash,
        "status": job.status,
        "message": "Document uploaded and ingestion job queued.",
    }


@router.get("")
def list_documents(
    document_ids: list[uuid.UUID] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Latest ingestion job per document
    #
    # DISTINCT ON (document_id) keeps the first row of each
    # document_id group; ordering by created_at DESC makes
    # that first row the newest job.
    #
    # Optional filter: when document_ids are given (polling),
    # only those documents are returned.
    #
    #   GET /documents                                   -> all
    #   GET /documents?document_ids=<id>&document_ids=<id> -> only these
    # ---------------------------------------------------------
    query = (
        select(IngestionJob)
        .distinct(IngestionJob.document_id)
        .order_by(
            IngestionJob.document_id,
            IngestionJob.created_at.desc(),
        )
    )

    if document_ids:
        query = query.where(
            IngestionJob.document_id.in_(document_ids)
        )

    latest_jobs = db.scalars(query).all()

    # ---------------------------------------------------------
    # 2. Newest first
    #
    # DISTINCT ON forces the SQL ORDER BY to start with
    # document_id, so we sort by time afterwards in Python.
    # ---------------------------------------------------------
    latest_jobs = sorted(
        latest_jobs,
        key=lambda job: job.created_at,
        reverse=True,
    )

    # ---------------------------------------------------------
    # 3. Build response
    # ---------------------------------------------------------
    documents = []

    for job in latest_jobs:
        documents.append(
            {
                "document_id": str(job.document_id),
                "filename": job.document_name,
                "job_id": str(job.id),
                "status": job.status,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
            }
        )

    return {
        "documents": documents,
    }
