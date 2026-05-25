"""
Search and Citation API
------------------------
Endpoints:
  GET /api/search              → Semantic search without chat context
  GET /api/citations/{chunk_id} → Retrieve specific source chunk
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth import get_current_user
from backend.config import settings
from backend.database.models import User
from backend.generation.hallucination_guard import HallucinationGuard
from backend.retrieval.embeddings import EmbeddingGenerator
from backend.retrieval.orchestrator import RetrievalOrchestrator
from backend.retrieval.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])

_orchestrator: Optional[RetrievalOrchestrator] = None
_embedder: Optional[EmbeddingGenerator] = None
_vector_store: Optional[ChromaVectorStore] = None


def get_orchestrator() -> RetrievalOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RetrievalOrchestrator()
    return _orchestrator


def get_embedder() -> EmbeddingGenerator:
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingGenerator()
    return _embedder


def get_vector_store() -> ChromaVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


@router.get("/api/search")
async def semantic_search(
    q: str = Query(..., min_length=3, description="Search query"),
    top_k: int = Query(settings.top_k_retrieval, ge=1, le=20),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic search across all indexed documents.
    Returns ranked chunks without generating an LLM response.
    """
    guard = HallucinationGuard()
    clean_query = guard.sanitize_input(q)

    # Build filters
    filters = {}
    if year:
        filters["year"] = year
    if author:
        filters["authors"] = author

    orchestrator = get_orchestrator()
    ctx = orchestrator.retrieve(
        query=clean_query,
        top_k=top_k,
        filters=filters if filters else None,
    )

    results = [
        {
            "chunk_id": r.chroma_id,
            "content": r.content[:500] + ("..." if len(r.content) > 500 else ""),
            "title": r.title,
            "authors": r.authors,
            "year": r.year,
            "page_number": r.page_number,
            "semantic_score": r.semantic_score,
            "rerank_score": r.rerank_score,
        }
        for r in ctx.results
    ]

    return {
        "status": "success",
        "data": {
            "query": clean_query,
            "expanded_queries": ctx.expanded_queries,
            "results": results,
            "total_candidates": ctx.total_candidates,
            "retrieval_time_ms": ctx.retrieval_time_ms,
        },
        "message": f"Found {len(results)} results",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


@router.get("/api/citations/{chunk_id}")
async def get_citation(
    chunk_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific source chunk by its ChromaDB ID."""
    vector_store = get_vector_store()

    chunk = vector_store.get_chunk_by_id(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail=f"Chunk not found: {chunk_id}")

    meta = chunk.metadata
    return {
        "status": "success",
        "data": {
            "chunk_id": chunk_id,
            "content": chunk.content,
            "title": meta.get("title", "Unknown"),
            "authors": meta.get("authors", []),
            "year": meta.get("year"),
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "document_id": chunk.document_id,
        },
        "message": "Citation retrieved",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }
