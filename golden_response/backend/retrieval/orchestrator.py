"""
Full Retrieval Orchestrator
----------------------------
Coordinates the complete retrieval pipeline:
1. Query expansion (3 variants)
2. Multi-query semantic search (ChromaDB)
3. BM25 keyword search
4. Hybrid RRF fusion
5. Cross-encoder re-ranking
6. Similarity threshold filtering
"""
import logging
from dataclasses import dataclass
from typing import Optional

from backend.config import settings
from backend.retrieval.embeddings import EmbeddingGenerator
from backend.retrieval.vector_store import ChromaVectorStore
from backend.retrieval.bm25_retriever import BM25IndexManager
from backend.retrieval.hybrid_fusion import ReciprocalRankFusion
from backend.retrieval.reranker import CrossEncoderReranker, RankedResult
from backend.retrieval.query_expander import QueryExpander

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    query: str
    expanded_queries: list[str]
    results: list[RankedResult]
    total_candidates: int
    retrieval_time_ms: float
    passed_threshold: bool


class RetrievalOrchestrator:
    """
    Single entry point for the full hybrid retrieval pipeline.
    """

    def __init__(self):
        self.embedder = EmbeddingGenerator()
        self.vector_store = ChromaVectorStore()
        self.bm25_manager = BM25IndexManager()
        self.fusion = ReciprocalRankFusion()
        self.reranker = CrossEncoderReranker()
        self.query_expander = QueryExpander()
        self._bm25_loaded = False

    def _ensure_bm25_loaded(self) -> None:
        """Lazy-load BM25 index from ChromaDB."""
        if not self._bm25_loaded:
            self.bm25_manager.load_from_chroma(self.vector_store)
            self._bm25_loaded = True

    def retrieve(
        self,
        query: str,
        top_k: int = settings.top_k_retrieval,
        filters: Optional[dict] = None,
        skip_expansion: bool = False,
    ) -> RetrievalContext:
        """
        Execute the full retrieval pipeline.

        Args:
            query: User's natural language query
            top_k: Final number of results to return
            filters: Optional metadata filters (author, year, title)
            skip_expansion: Skip query expansion (for follow-up queries)

        Returns:
            RetrievalContext with ranked results and metadata
        """
        import time
        start_time = time.time()

        # ── Step 1: Query expansion ──────────────────────────────────────────
        if skip_expansion:
            expanded_queries = [query]
        else:
            expanded_queries = self.query_expander.expand(query)

        # ── Step 2: Multi-query semantic search ──────────────────────────────
        seen_semantic_ids: set[str] = set()
        all_semantic_results = []

        for q in expanded_queries:
            q_embedding = self.embedder.embed_query(q)
            results = self.vector_store.search(
                query_embedding=q_embedding,
                top_k=top_k * 3,  # Retrieve more candidates for fusion
                filters=filters,
            )
            for r in results:
                if r.chroma_id not in seen_semantic_ids:
                    seen_semantic_ids.add(r.chroma_id)
                    all_semantic_results.append(r)

        logger.info(f"Semantic search: {len(all_semantic_results)} unique results")

        # ── Step 3: BM25 keyword search ───────────────────────────────────────
        self._ensure_bm25_loaded()
        bm25_results = self.bm25_manager.search(query, top_k=top_k * 3)
        logger.info(f"BM25 search: {len(bm25_results)} results")

        # ── Step 4: Hybrid RRF fusion ─────────────────────────────────────────
        fused_results = self.fusion.fuse(
            semantic_results=all_semantic_results,
            bm25_results=bm25_results,
            top_k=top_k * 2,  # Pass more to re-ranker
        )
        total_candidates = len(fused_results)

        # ── Step 5: Cross-encoder re-ranking ─────────────────────────────────
        ranked_results = self.reranker.rerank(
            query=query,
            candidates=fused_results,
            top_k=top_k,
        )

        # ── Step 6: Similarity threshold check ───────────────────────────────
        # Use semantic_score for threshold check; fall back to normalized rerank_score
        passed_threshold = any(
            (r.semantic_score or 0) >= settings.similarity_threshold
            for r in ranked_results
        )

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Retrieval complete: {len(ranked_results)} results in {elapsed_ms:.1f}ms, "
            f"threshold_passed={passed_threshold}"
        )

        return RetrievalContext(
            query=query,
            expanded_queries=expanded_queries,
            results=ranked_results,
            total_candidates=total_candidates,
            retrieval_time_ms=elapsed_ms,
            passed_threshold=passed_threshold,
        )

    def refresh_bm25_index(self) -> None:
        """Force reload of BM25 index (call after new documents are indexed)."""
        self._bm25_loaded = False
        self._ensure_bm25_loaded()
