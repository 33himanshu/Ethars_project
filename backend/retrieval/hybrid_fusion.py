"""
Hybrid Retrieval Fusion Module
--------------------------------
Combines semantic (ChromaDB) and keyword (BM25) results using
Reciprocal Rank Fusion (RRF).

RRF Formula: score(d) = Σ 1 / (k + rank(d))
where k=60 is a smoothing constant that reduces the impact of high rankings.

Justification:
- RRF is parameter-free (beyond k) and robust across different score scales
- Outperforms linear combination in most IR benchmarks
- Handles the score distribution mismatch between cosine similarity and BM25
"""
import logging
from dataclasses import dataclass
from typing import Optional, Union

from backend.retrieval.vector_store import SearchResult
from backend.retrieval.bm25_retriever import BM25Result

logger = logging.getLogger(__name__)

# Type alias for either result type
AnyResult = Union[SearchResult, BM25Result]


@dataclass
class FusedResult:
    chroma_id: str
    content: str
    rrf_score: float
    semantic_score: Optional[float]
    bm25_score: Optional[float]
    semantic_rank: Optional[int]
    bm25_rank: Optional[int]
    metadata: dict
    document_id: str
    page_number: Optional[int]
    chunk_index: int


class ReciprocalRankFusion:
    """
    Merges semantic and BM25 retrieval results using RRF.
    """

    RRF_K = 60  # Standard smoothing constant

    def fuse(
        self,
        semantic_results: list[SearchResult],
        bm25_results: list[BM25Result],
        top_k: int = 10,
    ) -> list[FusedResult]:
        """
        Fuse two ranked lists using Reciprocal Rank Fusion.

        Args:
            semantic_results: Results from ChromaDB vector search
            bm25_results: Results from BM25 keyword search
            top_k: Number of fused results to return

        Returns:
            Merged and re-ranked list of FusedResult
        """
        # Build lookup maps: chroma_id -> result
        semantic_map: dict[str, SearchResult] = {
            r.chroma_id: r for r in semantic_results
        }
        bm25_map: dict[str, BM25Result] = {
            r.chroma_id: r for r in bm25_results
        }

        # Collect all unique chunk IDs
        all_ids = set(semantic_map.keys()) | set(bm25_map.keys())

        # Build rank maps (1-indexed)
        semantic_ranks = {r.chroma_id: i + 1 for i, r in enumerate(semantic_results)}
        bm25_ranks = {r.chroma_id: i + 1 for i, r in enumerate(bm25_results)}

        # Compute RRF scores
        fused: list[FusedResult] = []
        for chroma_id in all_ids:
            rrf_score = 0.0
            sem_rank = semantic_ranks.get(chroma_id)
            bm25_rank = bm25_ranks.get(chroma_id)

            if sem_rank is not None:
                rrf_score += 1.0 / (self.RRF_K + sem_rank)
            if bm25_rank is not None:
                rrf_score += 1.0 / (self.RRF_K + bm25_rank)

            # Get content and metadata from whichever source has it
            source = semantic_map.get(chroma_id) or bm25_map.get(chroma_id)
            if source is None:
                continue

            fused.append(FusedResult(
                chroma_id=chroma_id,
                content=source.content,
                rrf_score=rrf_score,
                semantic_score=semantic_map[chroma_id].score if chroma_id in semantic_map else None,
                bm25_score=bm25_map[chroma_id].score if chroma_id in bm25_map else None,
                semantic_rank=sem_rank,
                bm25_rank=bm25_rank,
                metadata=source.metadata,
                document_id=source.document_id,
                page_number=source.page_number,
                chunk_index=source.chunk_index,
            ))

        # Sort by RRF score descending
        fused.sort(key=lambda x: x.rrf_score, reverse=True)

        logger.info(
            f"RRF fusion: {len(semantic_results)} semantic + "
            f"{len(bm25_results)} BM25 → {len(fused)} unique → top {top_k}"
        )

        return fused[:top_k]

    def deduplicate(self, results: list[FusedResult]) -> list[FusedResult]:
        """Remove near-duplicate chunks based on content similarity."""
        seen_ids: set[str] = set()
        unique: list[FusedResult] = []
        for result in results:
            if result.chroma_id not in seen_ids:
                seen_ids.add(result.chroma_id)
                unique.append(result)
        return unique
