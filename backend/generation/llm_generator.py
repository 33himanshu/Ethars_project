"""
LLM Generation Module
----------------------
Uses Google Gemini 2.5 Flash for citation-aware response generation.
Supports both streaming (SSE) and non-streaming modes.
"""
import logging
from typing import AsyncGenerator, Optional

import google.generativeai as genai

from backend.config import settings
from backend.generation.context_manager import ContextWindowManager
from backend.generation.citation_formatter import CitationFormatter
from backend.retrieval.reranker import RankedResult

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.google_api_key)

# ── System prompt template ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an academic research assistant with expertise in analyzing scientific papers.

CRITICAL RULES:
1. Answer ONLY using the provided context chunks below.
2. For EVERY factual claim, cite the source using format: [LastName et al., Year, chunk_id]
3. If the context does not contain sufficient information, respond EXACTLY with:
   "I cannot find sufficient evidence in the provided documents."
4. Never fabricate citations, statistics, or claims not present in the context.
5. Be precise, academic, and concise.

CONTEXT CHUNKS:
{context_chunks}

CONVERSATION HISTORY:
{conversation_history}"""

USER_PROMPT_TEMPLATE = "User Query: {query}"


class GeminiGenerator:
    """
    Generates citation-aware responses using Gemini 2.5 Flash.
    """

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,          # Low temperature for factual accuracy
                top_p=0.95,
                max_output_tokens=settings.reserved_response_tokens,
            ),
        )
        self.context_manager = ContextWindowManager()
        self.citation_formatter = CitationFormatter()

    def generate(
        self,
        query: str,
        chunks: list[RankedResult],
        history: list[dict],
    ) -> dict:
        """
        Generate a non-streaming response.

        Returns:
            dict with keys: answer, citations, confidence_score, token_usage
        """
        prompt_parts = self._build_prompt(query, chunks, history)
        if prompt_parts is None:
            return self._refusal_response()

        try:
            response = self.model.generate_content(prompt_parts)
            raw_text = response.text

            # Verify and clean citations
            cleaned_text, verified_citations, hallucinated = (
                self.citation_formatter.verify_citations(raw_text, chunks)
            )

            confidence = self._compute_confidence(chunks)
            token_usage = self._extract_token_usage(response)

            return {
                "answer": cleaned_text,
                "citations": self.citation_formatter.build_citation_panel(verified_citations),
                "confidence_score": confidence,
                "hallucinated_citations": hallucinated,
                "token_usage": token_usage,
            }

        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise

    async def generate_stream(
        self,
        query: str,
        chunks: list[RankedResult],
        history: list[dict],
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using SSE.
        Yields text tokens as they are generated.
        """
        prompt_parts = self._build_prompt(query, chunks, history)
        if prompt_parts is None:
            yield self._refusal_text()
            return

        try:
            response = self.model.generate_content(
                prompt_parts,
                stream=True,
            )

            full_text = ""
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    yield chunk.text

            # Post-generation: verify citations (log only, don't modify stream)
            _, _, hallucinated = self.citation_formatter.verify_citations(
                full_text, chunks
            )
            if hallucinated:
                logger.warning(
                    f"Stream contained {len(hallucinated)} hallucinated citations: "
                    f"{hallucinated}"
                )

        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            yield f"\n\n[Error generating response: {str(e)}]"

    # ── Prompt building ───────────────────────────────────────────────────────

    def _build_prompt(
        self,
        query: str,
        chunks: list[RankedResult],
        history: list[dict],
    ) -> Optional[list[str]]:
        """Build the full prompt with context and history."""
        managed = self.context_manager.fit(chunks, history)

        if not managed.chunks:
            logger.warning("No chunks fit in context window")
            return None

        context_text = self.context_manager.format_chunks_for_prompt(managed.chunks)
        history_text = self.context_manager.format_history_for_prompt(managed.history_turns)

        system = SYSTEM_PROMPT.format(
            context_chunks=context_text,
            conversation_history=history_text,
        )
        user = USER_PROMPT_TEMPLATE.format(query=query)

        return [system, user]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _compute_confidence(self, chunks: list[RankedResult]) -> float:
        """
        Compute confidence score as average semantic similarity of top chunks.
        """
        if not chunks:
            return 0.0
        scores = [c.semantic_score for c in chunks if c.semantic_score is not None]
        if not scores:
            return 0.5
        return round(sum(scores) / len(scores), 3)

    def _extract_token_usage(self, response) -> dict:
        """Extract token usage from Gemini response metadata."""
        try:
            usage = response.usage_metadata
            return {
                "prompt_tokens": usage.prompt_token_count,
                "completion_tokens": usage.candidates_token_count,
                "total_tokens": usage.total_token_count,
            }
        except Exception:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _refusal_response(self) -> dict:
        return {
            "answer": "I cannot find sufficient evidence in the provided documents.",
            "citations": [],
            "confidence_score": 0.0,
            "hallucinated_citations": [],
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def _refusal_text(self) -> str:
        return "I cannot find sufficient evidence in the provided documents."
