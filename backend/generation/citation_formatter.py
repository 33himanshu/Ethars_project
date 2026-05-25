"""
Citation Formatter and Verifier
---------------------------------
Formats citations in [Author, Year, Chunk ID] format.
Verifies that every cited chunk ID exists in the retrieved context.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional

from backend.retrieval.reranker import RankedResult

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    chunk_id: str
    title: str
    authors: list[str]
    year: Optional[int]
    page_number: Optional[int]
    content_snippet: str
    is_verified: bool


class CitationFormatter:
    """
    Parses citations from LLM output and verifies them against
    the retrieved context chunks.
    """

    # Pattern: [Author, Year, chunk_id] or [Author et al., Year, chunk_id]
    CITATION_PATTERN = re.compile(
        r"\[([^\]]+?,\s*\d{4},\s*[^\]]+?)\]"
    )

    def format_citation(self, chunk: RankedResult) -> str:
        """
        Format a chunk as a citation string.
        Example: [Vaswani et al., 2017, doc123_chunk_5]
        """
        if chunk.authors:
            if len(chunk.authors) > 2:
                author_str = f"{chunk.authors[0].split()[-1]} et al."
            elif len(chunk.authors) == 2:
                author_str = f"{chunk.authors[0].split()[-1]} & {chunk.authors[1].split()[-1]}"
            else:
                author_str = chunk.authors[0].split()[-1]
        else:
            author_str = "Unknown"

        year_str = str(chunk.year) if chunk.year else "n.d."
        return f"[{author_str}, {year_str}, {chunk.chroma_id}]"

    def extract_citations_from_text(self, text: str) -> list[str]:
        """Extract all citation references from LLM-generated text."""
        matches = self.CITATION_PATTERN.findall(text)
        return [f"[{m}]" for m in matches]

    def verify_citations(
        self,
        text: str,
        retrieved_chunks: list[RankedResult],
    ) -> tuple[str, list[Citation], list[str]]:
        """
        Verify all citations in the text against retrieved chunks.

        Returns:
            - cleaned_text: Text with unverified citations marked
            - verified_citations: List of verified Citation objects
            - hallucinated_ids: List of chunk IDs not in retrieved context
        """
        retrieved_ids = {chunk.chroma_id: chunk for chunk in retrieved_chunks}
        cited_ids = self._extract_chunk_ids(text)

        verified_citations: list[Citation] = []
        hallucinated_ids: list[str] = []

        for chunk_id in cited_ids:
            if chunk_id in retrieved_ids:
                chunk = retrieved_ids[chunk_id]
                verified_citations.append(Citation(
                    chunk_id=chunk_id,
                    title=chunk.title,
                    authors=chunk.authors,
                    year=chunk.year,
                    page_number=chunk.page_number,
                    content_snippet=chunk.content[:200] + "...",
                    is_verified=True,
                ))
            else:
                hallucinated_ids.append(chunk_id)
                logger.warning(f"Hallucinated citation detected: {chunk_id}")

        # Mark hallucinated citations in text
        cleaned_text = text
        for bad_id in hallucinated_ids:
            cleaned_text = re.sub(
                rf"\[[^\]]*{re.escape(bad_id)}[^\]]*\]",
                "[UNVERIFIED CITATION]",
                cleaned_text,
            )

        return cleaned_text, verified_citations, hallucinated_ids

    def build_citation_panel(self, citations: list[Citation]) -> list[dict]:
        """Build structured citation data for the frontend citation panel."""
        return [
            {
                "chunk_id": c.chunk_id,
                "title": c.title,
                "authors": c.authors,
                "year": c.year,
                "page_number": c.page_number,
                "snippet": c.content_snippet,
                "is_verified": c.is_verified,
            }
            for c in citations
        ]

    def _extract_chunk_ids(self, text: str) -> list[str]:
        """Extract chunk IDs from citation patterns in text."""
        chunk_ids = []
        for match in self.CITATION_PATTERN.finditer(text):
            parts = match.group(1).split(",")
            if len(parts) >= 3:
                # Last part is the chunk ID
                chunk_id = parts[-1].strip()
                chunk_ids.append(chunk_id)
        return chunk_ids
