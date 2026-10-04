import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
        # Existing document was successfully processed
        # -----------------------------------------------------
        if existing_document.status == "READY":

            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=409,
                detail=(
                    f"This document has already been successfully "
                    f"ingested as '{existing_document.filename}'"
                ),
            )

        # -----------------------------------------------------
        # Existing document is currently being processed
        # -----------------------------------------------------
        if existing_document.status in {
            "UPLOADED",
            "PROCESSING",
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
        # Existing document previously failed
        #
        # We retry ingestion by creating a NEW JOB.
        # We do NOT create another Document.
        # -----------------------------------------------------
        if existing_document.status == "FAILED":

            # Delete the newly uploaded duplicate file.
            # We can reuse the original stored file because
            # the content hash is identical.
            file_path.unlink(missing_ok=True)

            job = IngestionJob(
                document_id=existing_document.id,
                document_name=existing_document.filename,
                status="QUEUED",
                stage=None,
                retry_count=0,
            )

            db.add(job)
            db.flush()

            existing_document.active_job_id = job.id
            existing_document.status = "UPLOADED"

            db.commit()

            try:
                enqueue_ingestion_job(str(job.id))

            except Exception as exc:
                job.status = "FAILED"
                job.error_message = (
                    f"Failed to enqueue ingestion job: {exc}"
                )

                existing_document.status = "FAILED"

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
                "status": existing_document.status,
                "message": "Previous ingestion failed. A new ingestion job has been queued.",
            }

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
        status="UPLOADED",
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
        stage=None,
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
            f"Failed to enqueue ingestion job: {exc}"
        )

        document.status = "FAILED"

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
        "status": document.status,
        "message": "Document uploaded and ingestion job queued.",
    }