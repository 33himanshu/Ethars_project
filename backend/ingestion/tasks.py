"""
Async Ingestion Task Handler
-----------------------------
Celery tasks for background document processing.
Implements retry logic (max 3 retries) and graceful failure logging.
"""
import logging
import uuid
from pathlib import Path

from celery import Celery
from celery.utils.log import get_task_logger
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings

# ── Celery app ───────────────────────────────────────────────────────────────
celery_app = Celery(
    "rag_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

task_logger = get_task_logger(__name__)
logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="ingestion.process_document",
)
def process_document_task(self, document_id: str, file_path: str, user_id: str):
    """
    Main ingestion pipeline task.
    Steps:
      1. Parse PDF
      2. Extract metadata
      3. Chunk text
      4. Generate embeddings
      5. Index into ChromaDB
      6. Update PostgreSQL record
    """
    from backend.ingestion.pdf_parser import PDFParser
    from backend.ingestion.metadata_extractor import MetadataExtractor
    from backend.ingestion.chunker import SentenceAwareChunker
    from backend.retrieval.embeddings import EmbeddingGenerator
    from backend.retrieval.vector_store import ChromaVectorStore
    import asyncio

    task_logger.info(f"Starting ingestion for document {document_id}")

    try:
        # ── Step 1: Parse PDF ────────────────────────────────────────────────
        task_logger.info(f"[{document_id}] Parsing PDF: {file_path}")
        parser = PDFParser()
        parsed_doc = parser.parse(file_path)

        # ── Step 2: Extract metadata ─────────────────────────────────────────
        task_logger.info(f"[{document_id}] Extracting metadata")
        extractor = MetadataExtractor()
        metadata = extractor.extract(parsed_doc, Path(file_path).name)

        # ── Step 3: Chunk text ───────────────────────────────────────────────
        task_logger.info(f"[{document_id}] Chunking document")
        chunker = SentenceAwareChunker()

        # Build page map: character offset -> page number
        page_map = {}
        char_offset = 0
        for page in parsed_doc.pages:
            page_map[char_offset] = page.page_number
            char_offset += len(page.text) + 2  # +2 for "\n\n"

        doc_meta = {
            "document_id": document_id,
            "title": metadata.title,
            "authors": metadata.authors,
            "year": metadata.publication_year,
            "doi": metadata.doi,
        }
        chunks = chunker.chunk_document(parsed_doc.full_text, page_map, doc_meta)
        task_logger.info(f"[{document_id}] Created {len(chunks)} chunks")

        # ── Step 4 & 5: Embed and index ──────────────────────────────────────
        task_logger.info(f"[{document_id}] Generating embeddings and indexing")
        embedder = EmbeddingGenerator()
        vector_store = ChromaVectorStore()

        texts = [c.content for c in chunks]
        embeddings = embedder.embed_batch(texts)

        chroma_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chroma_id = f"{document_id}_chunk_{chunk.chunk_index}"
            chroma_ids.append(chroma_id)
            vector_store.add_chunk(
                chroma_id=chroma_id,
                text=chunk.content,
                embedding=embedding,
                metadata={
                    **chunk.metadata,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number or 0,
                    "token_count": chunk.token_count,
                    "document_id": document_id,
                },
            )

        # ── Step 6: Update database ──────────────────────────────────────────
        task_logger.info(f"[{document_id}] Updating database record")
        asyncio.run(
            _update_document_record(
                document_id=document_id,
                metadata=metadata,
                chunks=chunks,
                chroma_ids=chroma_ids,
                page_count=parsed_doc.page_count,
            )
        )

        task_logger.info(f"[{document_id}] Ingestion complete")
        return {"status": "success", "document_id": document_id, "chunk_count": len(chunks)}

    except Exception as exc:
        task_logger.error(f"[{document_id}] Ingestion failed: {exc}", exc_info=True)
        # Update DB with failure status
        try:
            import asyncio
            asyncio.run(_mark_document_failed(document_id, str(exc)))
        except Exception as db_exc:
            task_logger.error(f"Failed to update DB failure status: {db_exc}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


async def _update_document_record(
    document_id: str,
    metadata,
    chunks: list,
    chroma_ids: list[str],
    page_count: int,
):
    """Update PostgreSQL document record after successful ingestion."""
    from backend.database.connection import AsyncSessionLocal
    from backend.database.models import Document, DocumentChunk, DocumentStatus
    from sqlalchemy import select
    import uuid as uuid_mod

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == uuid_mod.UUID(document_id))
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return

        doc.title = metadata.title
        doc.authors = metadata.authors
        doc.publication_year = metadata.publication_year
        doc.abstract = metadata.abstract
        doc.page_count = page_count
        doc.status = DocumentStatus.indexed
        doc.chroma_collection = settings.chroma_collection
        doc.doc_metadata = {
            "doi": metadata.doi,
            "venue": metadata.venue,
            "keywords": metadata.keywords,
        }

        # Insert chunk records
        for chunk, chroma_id in zip(chunks, chroma_ids):
            db_chunk = DocumentChunk(
                document_id=uuid_mod.UUID(document_id),
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                chroma_id=chroma_id,
                chunk_metadata=chunk.metadata,
            )
            session.add(db_chunk)

        await session.commit()


async def _mark_document_failed(document_id: str, error_message: str):
    """Mark a document as failed in PostgreSQL."""
    from backend.database.connection import AsyncSessionLocal
    from backend.database.models import Document, DocumentStatus
    from sqlalchemy import select
    import uuid as uuid_mod

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == uuid_mod.UUID(document_id))
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = DocumentStatus.failed
            doc.error_message = error_message[:500]
            doc.retry_count += 1
            await session.commit()
