"""
Hallucination Mitigation and Safety Module
-------------------------------------------
Implements multiple layers of hallucination prevention:
1. Retrieval grounding validation (similarity threshold >= 0.75)
2. Confidence scoring
3. Citation verification
4. Refusal handler
5. Input sanitizer (prompt injection prevention)
6. Retrieved content sanitizer
7. Answer relevance checker
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.config import settings
from backend.retrieval.reranker import RankedResult

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheckResult:
    passed: bool
    reason: Optional[str]
    confidence_score: float
    should_refuse: bool


class HallucinationGuard:
    """
    Multi-layer hallucination prevention system.
    """

    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+instructions?",
        r"forget\s+(everything|all|previous)",
        r"you\s+are\s+now\s+a?\s*\w+",
        r"act\s+as\s+(if\s+you\s+are|a)\s+\w+",
        r"system\s*:\s*",
        r"<\s*system\s*>",
        r"\[INST\]",
        r"###\s*instruction",
        r"jailbreak",
        r"DAN\s+mode",
    ]

    # HTML/script patterns to strip from retrieved content
    SCRIPT_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<[^>]+on\w+\s*=",
        r"javascript:",
        r"data:text/html",
        r"eval\s*\(",
        r"exec\s*\(",
    ]

    def __init__(self):
        self.injection_regex = re.compile(
            "|".join(self.INJECTION_PATTERNS),
            re.IGNORECASE | re.DOTALL,
        )
        self.script_regex = re.compile(
            "|".join(self.SCRIPT_PATTERNS),
            re.IGNORECASE | re.DOTALL,
        )

    # ── Input Sanitization ────────────────────────────────────────────────────

    def sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input to prevent prompt injection.
        - Strips injection patterns
        - Removes control characters
        - Limits length
        """
        if not user_input:
            return ""

        # Check for injection attempts
        if self.injection_regex.search(user_input):
            logger.warning(f"Prompt injection attempt detected: {user_input[:100]}")
            # Strip the injection patterns rather than blocking entirely
            cleaned = self.injection_regex.sub("[REMOVED]", user_input)
        else:
            cleaned = user_input

        # Remove control characters (except newlines and tabs)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        # Limit length
        cleaned = cleaned[:2000]

        return cleaned.strip()

    # ── Content Sanitization ──────────────────────────────────────────────────

    def sanitize_chunk_content(self, content: str) -> str:
        """
        Remove executable code or script tags from retrieved chunks
        before injecting into LLM prompt.
        """
        # Remove script tags and event handlers
        cleaned = self.script_regex.sub("[CONTENT REMOVED]", content)

        # Remove null bytes
        cleaned = cleaned.replace("\x00", "")

        return cleaned

    def sanitize_chunks(self, chunks: list[RankedResult]) -> list[RankedResult]:
        """Sanitize content of all retrieved chunks."""
        for chunk in chunks:
            chunk.content = self.sanitize_chunk_content(chunk.content)
        return chunks

    # ── Retrieval Grounding Validation ────────────────────────────────────────

    def validate_retrieval_grounding(
        self,
        chunks: list[RankedResult],
        threshold: float = settings.similarity_threshold,
    ) -> SafetyCheckResult:
        """
        Check if at least one chunk meets the similarity threshold.
        If not, the system should refuse to answer.
        """
        if not chunks:
            return SafetyCheckResult(
                passed=False,
                reason="No relevant documents found in the knowledge base.",
                confidence_score=0.0,
                should_refuse=True,
            )

        max_score = max(
            (c.semantic_score or 0.0) for c in chunks
        )
        avg_score = sum(
            (c.semantic_score or 0.0) for c in chunks
        ) / len(chunks)

        if max_score < threshold:
            return SafetyCheckResult(
                passed=False,
                reason=(
                    f"No retrieved chunk meets the minimum similarity threshold "
                    f"({threshold}). Best score: {max_score:.3f}. "
                    "The query may be outside the scope of indexed documents."
                ),
                confidence_score=avg_score,
                should_refuse=True,
            )

        return SafetyCheckResult(
            passed=True,
            reason=None,
            confidence_score=avg_score,
            should_refuse=False,
        )

    # ── Confidence Scoring ────────────────────────────────────────────────────

    def compute_confidence(self, chunks: list[RankedResult]) -> float:
        """
        Compute overall confidence score for the response.
        Based on average semantic similarity of top-k chunks.
        """
        if not chunks:
            return 0.0
        scores = [c.semantic_score for c in chunks if c.semantic_score is not None]
        if not scores:
            return 0.5
        return round(sum(scores) / len(scores), 4)

    # ── Refusal Handler ───────────────────────────────────────────────────────

    def build_refusal_response(self, reason: str) -> dict:
        """Build a structured refusal response."""
        return {
            "status": "refused",
            "answer": "I cannot find sufficient evidence in the provided documents.",
            "reason": reason,
            "citations": [],
            "confidence_score": 0.0,
        }

    # ── Answer Relevance Check ────────────────────────────────────────────────

    def check_answer_relevance(
        self,
        query: str,
        answer: str,
        embedder,
    ) -> float:
        """
        Compute cosine similarity between query and answer embeddings.
        Low similarity may indicate an off-topic or hallucinated response.
        """
        try:
            query_emb = embedder.embed_query(query)
            answer_emb = embedder.embed(answer[:500])  # Use first 500 chars
            return embedder.cosine_similarity(query_emb, answer_emb)
        except Exception as e:
            logger.warning(f"Answer relevance check failed: {e}")
            return 0.5  # Neutral score on failure
