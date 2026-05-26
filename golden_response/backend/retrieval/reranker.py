"""
Re-ranking Module
------------------
Uses cross-encoder/ms-marco-MiniLM-L-6-v2 to re-rank retrieved chunks.

Justification:
- Cross-encoders jointly encode query+document, capturing fine-grained
  relevance signals that bi-encoders miss.
- ms-marco-MiniLM-L-6-v2 is fast (~50ms for 10 pairs) and accurate.
- Applied after hybrid fusion to select the best top-k chunks.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from sentence_transformers import CrossEncoder

from backend.config import settings
from backend.retrieval.hybrid_fusion import FusedResult

logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Singleton cross-encoder
_cross_encoder: Optional[CrossEncoder] = None


def get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        logger.info(f"Loading cross-encoder: {RERANKER_MODEL}")
        _cross_encoder = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _cross_encoder


@dataclass
class RankedResult:
    chroma_id: str
    content: str
    rerank_score: float       # Cross-encoder relevance score
    rrf_score: float          # Original RRF score
    semantic_score: Optional[float]
    metadata: dict
    document_id: str
    page_number: Optional[int]
    chunk_index: int
    title: str
    authors: list[str]
    year: Optional[int]


class CrossEncoderReranker:
    """
    Re-ranks a list of FusedResult objects using a cross-encoder model.
    Returns top-k results after re-ranking.
    """

    def __init__(self):
        self.model = get_cross_encoder()

    def rerank(
        self,
        query: str,
        candidates: list[FusedResult],
        top_k: int = settings.top_k_retrieval,
    ) -> list[RankedResult]:
        """
        Re-rank candidates using cross-encoder relevance scores.

        Args:
            query: Original user query
            candidates: Fused retrieval results to re-rank
            top_k: Number of results to return after re-ranking

        Returns:
            Top-k re-ranked results
        """
        if not candidates:
            return []

        # Prepare query-document pairs for cross-encoder
        pairs = [(query, c.content) for c in candidates]

        # Score all pairs
        scores = self.model.predict(pairs, show_progress_bar=False)

        # Combine scores with candidates
        scored = list(zip(scores, candidates))
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, candidate in scored[:top_k]:
            meta = candidate.metadata
            results.append(RankedResult(
                chroma_id=candidate.chroma_id,
                content=candidate.content,
                rerank_score=float(score),
                rrf_score=candidate.rrf_score,
                semantic_score=candidate.semantic_score,
                metadata=meta,
                document_id=candidate.document_id,
                page_number=candidate.page_number,
                chunk_index=candidate.chunk_index,
                title=str(meta.get("title", "Unknown")),
                authors=self._parse_authors(meta.get("authors", "")),
                year=self._parse_year(meta.get("year")),
            ))

        logger.info(
            f"Re-ranked {len(candidates)} candidates → top {len(results)} results"
        )
        return results

    def _parse_authors(self, authors_val) -> list[str]:
        if isinstance(authors_val, list):
            return authors_val
        if isinstance(authors_val, str) and authors_val:
            return [a.strip() for a in authors_val.split(",") if a.strip()]
        return []

    def _parse_year(self, year_val) -> Optional[int]:
        try:
            return int(year_val) if year_val else None
        except (ValueError, TypeError):
            return None
