"""
Document Management API
------------------------
Endpoints:
  POST   /api/documents/upload  → Upload and ingest document
  GET    /api/documents         → List all indexed documents
  DELETE /api/documents/{id}    → Remove document from index
"""
import logging
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_role
from backend.config import settings
from backend.database.connection import get_db
from backend.database.models import Document, DocumentStatus, User, UserRole
from backend.ingestion.duplicate_detector import compute_bytes_hash
from backend.ingestion.tasks import process_document_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024  # bytes


@router.post("/upload", status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.researcher, UserRole.admin)),
):
    """
    Upload a PDF document for ingestion.
    - Validates file type and size
    - Checks for duplicates via SHA-256 hash
    - Queues async ingestion task via Celery
    """
    # ── Validate file type ────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Only PDF files are accepted. Got: {file.content_type}",
        )

    # ── Read file content ─────────────────────────────────────────────────────
    content = await file.read()

    # ── Validate file size ────────────────────────────────────────────────────
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB",
        )

    # ── Duplicate detection ───────────────────────────────────────────────────
    file_hash = compute_bytes_hash(content)
    existing = await db.execute(
        select(Document).where(Document.file_hash == file_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Document already exists (duplicate detected by SHA-256 hash)",
        )

    # ── Save file to disk ─────────────────────────────────────────────────────
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename.replace(' ', '_')}"
    file_path = upload_dir / safe_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # ── Create DB record ──────────────────────────────────────────────────────
    doc = Document(
        id=uuid.UUID(doc_id),
        owner_id=current_user.id,
        title=file.filename.rsplit(".", 1)[0],
        file_path=str(file_path),
        file_hash=file_hash,
        file_size_bytes=len(content),
        status=DocumentStatus.pending,
    )
    db.add(doc)
    await db.commit()

    # ── Queue ingestion task ──────────────────────────────────────────────────
    process_document_task.delay(doc_id, str(file_path), str(current_user.id))

    logger.info(f"Document {doc_id} queued for ingestion by user {current_user.id}")

    return {
        "status": "success",
        "data": {
            "document_id": doc_id,
            "filename": file.filename,
            "file_hash": file_hash,
            "status": "pending",
            "message": "Document queued for processing",
        },
        "message": "Upload accepted",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


@router.get("")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents accessible to the current user."""
    query = select(Document)

    # Admins see all documents; researchers see only their own
    if current_user.role != UserRole.admin:
        query = query.where(Document.owner_id == current_user.id)

    if status:
        try:
            status_enum = DocumentStatus(status)
            query = query.where(Document.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "status": "success",
        "data": {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "authors": doc.authors,
                    "publication_year": doc.publication_year,
                    "status": doc.status.value,
                    "page_count": doc.page_count,
                    "file_size_bytes": doc.file_size_bytes,
                    "created_at": doc.created_at.isoformat(),
                }
                for doc in documents
            ],
            "page": page,
            "page_size": page_size,
        },
        "message": "Documents retrieved",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a document and all its chunks from the index."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    result = await db.execute(select(Document).where(Document.id == doc_uuid))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Authorization check
    if current_user.role != UserRole.admin and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    # Remove from ChromaDB
    try:
        from backend.retrieval.vector_store import ChromaVectorStore
        vector_store = ChromaVectorStore()
        vector_store.delete_document(document_id)
    except Exception as e:
        logger.warning(f"Failed to delete from ChromaDB: {e}")

    # Remove file from disk
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"Failed to delete file: {e}")

    # Delete from PostgreSQL (cascades to chunks)
    await db.delete(doc)
    await db.commit()

    return {
        "status": "success",
        "data": {"document_id": document_id},
        "message": "Document deleted successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }
