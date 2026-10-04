import uuid

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
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    existing_document = db.scalar(
        select(Document).where(
            Document.filename == file.filename
        )
    )

    if existing_document is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A document named '{file.filename}' already exists",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB limit",
        )

    document_id = uuid.uuid4()

    storage_key = f"documents/{document_id}_{file.filename}"

    file_path = save_file(
        file_bytes,
        storage_key,
    )

    content_hash = calculate_sha256(file_path)

    document = Document(
        id=document_id,
        filename=file.filename,
        storage_key=storage_key,
        content_hash=content_hash,
        file_size=len(file_bytes),
        mime_type=file.content_type,
        status="UPLOADED",
    )

    db.add(document)
    db.flush()

    job = IngestionJob(
        document_id=document.id,
        document_name=document.filename,
        status="QUEUED",
    )

    db.add(job)
    db.flush()

    document.active_job_id = job.id

    db.commit()

    try:
        enqueue_ingestion_job(str(job.id))
    except Exception as exc:
        job.status = "FAILED"
        job.error_message = f"Failed to enqueue ingestion job: {exc}"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Document uploaded but ingestion job could not be queued",
        )

    return {
        "document_id": str(document.id),
        "job_id": str(job.id),
        "filename": document.filename,
        "status": document.status,
    }