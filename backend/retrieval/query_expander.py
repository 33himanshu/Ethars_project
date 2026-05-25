"""
Query Expansion Module
-----------------------
Generates 3 alternative phrasings of the user query using Gemini.
Multi-query retrieval: run all variants, deduplicate, merge before re-ranking.
"""
import logging
import re
from typing import Optional

import google.generativeai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.google_api_key)


class QueryExpander:
    """
    Uses Gemini to generate semantically equivalent query variants.
    Falls back to the original query if expansion fails.
    """

    EXPANSION_PROMPT = """You are a search query optimizer for academic research.
Given the user's query, generate exactly 3 alternative phrasings that capture
the same information need but use different vocabulary and structure.

Rules:
- Each variant must be semantically equivalent to the original
- Use academic/technical language appropriate for research papers
- Vary the phrasing (e.g., different word order, synonyms, more specific terms)
- Output ONLY the 3 variants, one per line, numbered 1. 2. 3.
- Do NOT include the original query

Original query: {query}

3 alternative phrasings:"""

    def __init__(self):
        self.model = genai.GenerativeModel(settings.gemini_model)

    def expand(self, query: str, num_variants: int = 3) -> list[str]:
        """
        Generate query variants.

        Args:
            query: Original user query
            num_variants: Number of variants to generate (default 3)

        Returns:
            List containing original query + variants (deduplicated)
        """
        try:
            prompt = self.EXPANSION_PROMPT.format(query=query)
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300,
                ),
            )
            variants = self._parse_variants(response.text)
            all_queries = [query] + variants[:num_variants]
            logger.info(f"Query expanded: '{query}' → {len(all_queries)} variants")
            return all_queries

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}. Using original query only.")
            return [query]

    def _parse_variants(self, text: str) -> list[str]:
        """Parse numbered list from LLM response."""
        lines = text.strip().split("\n")
        variants = []
        for line in lines:
            # Remove numbering like "1.", "1)", "- "
            cleaned = re.sub(r"^\s*[\d]+[.)]\s*|^\s*[-•]\s*", "", line).strip()
            if cleaned and len(cleaned) > 10:
                variants.append(cleaned)
        return variants[:3]


class MultiQueryRetriever:
    """
    Runs retrieval for all query variants and merges results.
    Deduplicates by chroma_id before passing to re-ranker.
    """

    def __init__(self, vector_store, bm25_manager, embedder):
        self.vector_store = vector_store
        self.bm25_manager = bm25_manager
        self.embedder = embedder
        self.expander = QueryExpander()

    def retrieve_multi_query(
        self,
        query: str,
        top_k_per_query: int = 10,
        filters: Optional[dict] = None,
    ) -> list:
        """
        Expand query, retrieve for each variant, deduplicate results.

        Returns:
            Deduplicated list of SearchResult objects
        """
        from backend.retrieval.vector_store import SearchResult

        queries = self.expander.expand(query)
        seen_ids: set[str] = set()
        all_results: list[SearchResult] = []

        for q in queries:
            query_embedding = self.embedder.embed_query(q)
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k_per_query,
                filters=filters,
            )
            for r in results:
                if r.chroma_id not in seen_ids:
                    seen_ids.add(r.chroma_id)
                    all_results.append(r)

        logger.info(
            f"Multi-query retrieval: {len(queries)} queries → "
            f"{len(all_results)} unique semantic results"
        )
        return all_results
