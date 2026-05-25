"""
Chat API with SSE Streaming
-----------------------------
Endpoints:
  POST   /api/chat                    → Submit query, returns SSE stream
  GET    /api/chat/history/{session}  → Retrieve conversation history
  DELETE /api/chat/history/{session}  → Clear session history
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.config import settings
from backend.database.connection import get_db
from backend.database.models import User
from backend.generation.hallucination_guard import HallucinationGuard
from backend.generation.llm_generator import GeminiGenerator
from backend.memory.session_manager import ConversationMemoryManager
from backend.retrieval.orchestrator import RetrievalOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Singletons (initialized once per worker)
_retrieval_orchestrator: Optional[RetrievalOrchestrator] = None
_generator: Optional[GeminiGenerator] = None
_memory_manager: Optional[ConversationMemoryManager] = None
_guard: Optional[HallucinationGuard] = None


def get_retrieval_orchestrator() -> RetrievalOrchestrator:
    global _retrieval_orchestrator
    if _retrieval_orchestrator is None:
        _retrieval_orchestrator = RetrievalOrchestrator()
    return _retrieval_orchestrator


def get_generator() -> GeminiGenerator:
    global _generator
    if _generator is None:
        _generator = GeminiGenerator()
    return _generator


def get_memory() -> ConversationMemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemoryManager()
    return _memory_manager


def get_guard() -> HallucinationGuard:
    global _guard
    if _guard is None:
        _guard = HallucinationGuard()
    return _guard


# ── Request/Response schemas ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    filters: Optional[dict] = None   # e.g. {"year": 2017, "author": "Vaswani"}
    stream: bool = True


# ── SSE helpers ───────────────────────────────────────────────────────────────

def sse_event(data: dict | str, event: str = "message") -> str:
    """Format a Server-Sent Event."""
    if isinstance(data, dict):
        payload = json.dumps(data)
    else:
        payload = data
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_chat_response(
    query: str,
    session_id: str,
    filters: Optional[dict],
    current_user: User,
) -> AsyncGenerator[str, None]:
    """
    Full RAG pipeline with SSE streaming:
    1. Sanitize input
    2. Retrieve context
    3. Validate grounding
    4. Stream LLM response
    5. Save to memory
    """
    guard = get_guard()
    orchestrator = get_retrieval_orchestrator()
    generator = get_generator()
    memory = get_memory()

    # ── 1. Sanitize input ─────────────────────────────────────────────────────
    clean_query = guard.sanitize_input(query)
    if not clean_query:
        yield sse_event({"error": "Invalid query"}, "error")
        return

    # ── 2. Emit retrieval start event ─────────────────────────────────────────
    yield sse_event({"status": "retrieving", "message": "Searching documents..."}, "status")

    # ── 3. Retrieve context ───────────────────────────────────────────────────
    try:
        retrieval_ctx = orchestrator.retrieve(
            query=clean_query,
            top_k=settings.top_k_retrieval,
            filters=filters,
        )
    except Exception as e:
        logger.error(f"Retrieval error: {e}", exc_info=True)
        yield sse_event({"error": f"Retrieval failed: {str(e)}"}, "error")
        return

    # ── 4. Validate grounding ─────────────────────────────────────────────────
    safety_check = guard.validate_retrieval_grounding(retrieval_ctx.results)
    if safety_check.should_refuse:
        yield sse_event({
            "status": "refused",
            "message": safety_check.reason,
            "confidence_score": safety_check.confidence_score,
        }, "refused")
        return

    # ── 5. Sanitize chunks ────────────────────────────────────────────────────
    safe_chunks = guard.sanitize_chunks(retrieval_ctx.results)

    # ── 6. Emit generation start ──────────────────────────────────────────────
    yield sse_event({
        "status": "generating",
        "message": "Generating response...",
        "chunks_found": len(safe_chunks),
        "confidence_score": safety_check.confidence_score,
    }, "status")

    # ── 7. Get conversation history ───────────────────────────────────────────
    history = memory.get_formatted_history(session_id)

    # ── 8. Stream LLM response ────────────────────────────────────────────────
    full_response = ""
    try:
        async for token in generator.generate_stream(clean_query, safe_chunks, history):
            full_response += token
            yield sse_event({"token": token}, "token")
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        yield sse_event({"error": f"Generation failed: {str(e)}"}, "error")
        return

    # ── 9. Build citation panel ───────────────────────────────────────────────
    from backend.generation.citation_formatter import CitationFormatter
    formatter = CitationFormatter()
    _, verified_citations, _ = formatter.verify_citations(full_response, safe_chunks)
    citation_panel = formatter.build_citation_panel(verified_citations)

    # ── 10. Save to memory ────────────────────────────────────────────────────
    memory.add_turn(
        session_id=session_id,
        user_message=clean_query,
        assistant_message=full_response,
        citations=citation_panel,
        confidence_score=safety_check.confidence_score,
    )

    # ── 11. Emit completion event ─────────────────────────────────────────────
    yield sse_event({
        "status": "complete",
        "citations": citation_panel,
        "confidence_score": safety_check.confidence_score,
        "retrieval_time_ms": retrieval_ctx.retrieval_time_ms,
        "chunks_used": len(safe_chunks),
        "session_id": session_id,
    }, "complete")

    yield sse_event({}, "done")


# ── Route handlers ────────────────────────────────────────────────────────────

@router.post("")
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Submit a query and receive a streaming SSE response.
    Returns Server-Sent Events with tokens, status updates, and citations.
    """
    memory = get_memory()

    # Create or validate session
    session_id = req.session_id
    if not session_id:
        session_id = memory.create_session(str(current_user.id))
    else:
        # Refresh TTL on active session
        memory.refresh_ttl(session_id)

    return StreamingResponse(
        stream_chat_response(
            query=req.query,
            session_id=session_id,
            filters=req.filters,
            current_user=current_user,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
        },
    )


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve conversation history for a session."""
    memory = get_memory()

    # Verify session belongs to user
    meta = memory.get_session_meta(session_id)
    if meta and meta.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    history = memory.get_history(session_id)

    return {
        "status": "success",
        "data": {
            "session_id": session_id,
            "history": history,
            "turn_count": len(history) // 2,
        },
        "message": "History retrieved",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Clear conversation history for a session."""
    memory = get_memory()
    success = memory.clear_history(session_id)

    return {
        "status": "success" if success else "error",
        "data": {"session_id": session_id},
        "message": "History cleared" if success else "Failed to clear history",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": str(uuid.uuid4()),
    }
