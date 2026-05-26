"""
Context Window Manager
-----------------------
Manages the LLM context window to stay within token limits.
- Max context: 6000 tokens
- Reserved for response: 1000 tokens
- Available for chunks + history: 5000 tokens
- Truncates lowest-ranked chunks first if limit exceeded
"""
import logging
from dataclasses import dataclass

import tiktoken

from backend.config import settings
from backend.retrieval.reranker import RankedResult

logger = logging.getLogger(__name__)

_TOKENIZER = tiktoken.get_encoding("cl100k_base")


@dataclass
class ManagedContext:
    chunks: list[RankedResult]
    history_turns: list[dict]
    total_tokens: int
    chunks_truncated: int
    history_truncated: int


def count_tokens(text: str) -> int:
    """Count tokens in a string using tiktoken."""
    return len(_TOKENIZER.encode(text))


class ContextWindowManager:
    """
    Fits retrieved chunks and conversation history into the context window.
    Priority: recent history > high-ranked chunks > older history > low-ranked chunks
    """

    def __init__(
        self,
        max_context_tokens: int = settings.max_context_tokens,
        reserved_response_tokens: int = settings.reserved_response_tokens,
    ):
        self.max_context_tokens = max_context_tokens
        self.reserved_response_tokens = reserved_response_tokens
        self.available_tokens = max_context_tokens - reserved_response_tokens

    def fit(
        self,
        chunks: list[RankedResult],
        history: list[dict],
        system_prompt_tokens: int = 200,
    ) -> ManagedContext:
        """
        Fit chunks and history into the available token budget.

        Args:
            chunks: Re-ranked retrieval results (ordered by relevance)
            history: Conversation history turns (ordered oldest → newest)
            system_prompt_tokens: Estimated tokens for system prompt overhead

        Returns:
            ManagedContext with fitted chunks and history
        """
        budget = self.available_tokens - system_prompt_tokens
        chunks_truncated = 0
        history_truncated = 0

        # ── Fit conversation history (keep most recent turns) ─────────────────
        fitted_history = []
        history_tokens = 0
        history_budget = min(budget // 3, 1500)  # Max 1/3 of budget for history

        for turn in reversed(history):  # Most recent first
            turn_text = f"{turn['role']}: {turn['content']}"
            turn_tokens = count_tokens(turn_text)
            if history_tokens + turn_tokens <= history_budget:
                fitted_history.insert(0, turn)
                history_tokens += turn_tokens
            else:
                history_truncated += 1

        # ── Fit chunks (highest ranked first) ────────────────────────────────
        chunk_budget = budget - history_tokens
        fitted_chunks = []
        chunk_tokens = 0

        for chunk in chunks:  # Already sorted by relevance (highest first)
            chunk_text = chunk.content
            ct = count_tokens(chunk_text)
            if chunk_tokens + ct <= chunk_budget:
                fitted_chunks.append(chunk)
                chunk_tokens += ct
            else:
                chunks_truncated += 1
                logger.debug(
                    f"Truncated chunk {chunk.chroma_id} "
                    f"({ct} tokens, budget remaining: {chunk_budget - chunk_tokens})"
                )

        total_tokens = history_tokens + chunk_tokens + system_prompt_tokens

        if chunks_truncated > 0:
            logger.warning(
                f"Context window: truncated {chunks_truncated} chunks, "
                f"{history_truncated} history turns. "
                f"Total tokens: {total_tokens}/{self.max_context_tokens}"
            )

        return ManagedContext(
            chunks=fitted_chunks,
            history_turns=fitted_history,
            total_tokens=total_tokens,
            chunks_truncated=chunks_truncated,
            history_truncated=history_truncated,
        )

    def format_chunks_for_prompt(self, chunks: list[RankedResult]) -> str:
        """Format chunks as numbered context blocks for the LLM prompt."""
        if not chunks:
            return "No relevant context found."

        formatted = []
        for i, chunk in enumerate(chunks, 1):
            authors_str = ", ".join(chunk.authors) if chunk.authors else "Unknown"
            year_str = str(chunk.year) if chunk.year else "Unknown"
            page_str = f"p.{chunk.page_number}" if chunk.page_number else "unknown page"

            formatted.append(
                f"[CHUNK {i}] ID: {chunk.chroma_id}\n"
                f"Source: {chunk.title} | {authors_str} ({year_str}) | {page_str}\n"
                f"Content: {chunk.content}\n"
                f"---"
            )

        return "\n\n".join(formatted)

    def format_history_for_prompt(self, history: list[dict]) -> str:
        """Format conversation history for the LLM prompt."""
        if not history:
            return "No previous conversation."

        lines = []
        for turn in history:
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)
