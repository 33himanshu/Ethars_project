"""
Metadata Extractor
------------------
Extracts structured metadata from parsed PDF documents.
Attempts to identify title, authors, year, and abstract using
heuristics and regex patterns common in academic papers.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional

from backend.ingestion.pdf_parser import ParsedDocument

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    title: str
    authors: list[str]
    publication_year: Optional[int]
    abstract: Optional[str]
    doi: Optional[str]
    venue: Optional[str]       # Journal / conference name
    keywords: list[str]
    raw_metadata: dict


class MetadataExtractor:
    """
    Extracts and enriches metadata from a ParsedDocument.
    Combines PDF metadata fields with heuristic text analysis.
    """

    def extract(self, parsed_doc: ParsedDocument, filename: str = "") -> DocumentMetadata:
        first_page_text = parsed_doc.pages[0].text if parsed_doc.pages else ""

        title = self._resolve_title(parsed_doc, first_page_text, filename)
        authors = self._resolve_authors(parsed_doc, first_page_text)
        year = self._resolve_year(parsed_doc, first_page_text)
        abstract = self._resolve_abstract(parsed_doc, first_page_text)
        doi = self._extract_doi(parsed_doc.full_text)
        venue = self._extract_venue(first_page_text)
        keywords = self._extract_keywords(parsed_doc.full_text)

        return DocumentMetadata(
            title=title,
            authors=authors,
            publication_year=year,
            abstract=abstract,
            doi=doi,
            venue=venue,
            keywords=keywords,
            raw_metadata=parsed_doc.metadata,
        )

    # ── Title ────────────────────────────────────────────────────────────────

    def _resolve_title(
        self, doc: ParsedDocument, first_page: str, filename: str
    ) -> str:
        # Prefer PDF metadata title
        if doc.title and len(doc.title) > 5 and doc.title != "Untitled":
            return doc.title.strip()

        # Heuristic: first non-empty line of first page (often the title)
        for line in first_page.split("\n"):
            line = line.strip()
            if len(line) > 10 and not line.startswith("http"):
                return line[:300]

        # Fallback to filename
        return filename.replace("_", " ").replace("-", " ").rsplit(".", 1)[0]

    # ── Authors ──────────────────────────────────────────────────────────────

    def _resolve_authors(self, doc: ParsedDocument, first_page: str) -> list[str]:
        if doc.authors:
            return doc.authors

        # Heuristic: look for "Author Name1, Author Name2" pattern near top
        # Common in academic papers: lines after title, before abstract
        lines = first_page.split("\n")[:20]
        for line in lines:
            line = line.strip()
            # Skip lines that look like titles or institutions
            if re.search(r"\b(university|institute|department|abstract)\b", line, re.I):
                continue
            # Match patterns like "John Doe, Jane Smith" or "J. Doe and J. Smith"
            if re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", line) and len(line) < 200:
                parts = re.split(r",\s*|\s+and\s+", line)
                candidates = [p.strip() for p in parts if re.search(r"[A-Z]", p)]
                if 1 <= len(candidates) <= 20:
                    return candidates

        return []

    # ── Year ─────────────────────────────────────────────────────────────────

    def _resolve_year(self, doc: ParsedDocument, first_page: str) -> Optional[int]:
        if doc.publication_year:
            return doc.publication_year

        # Search first page for 4-digit year between 1900-2030
        match = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", first_page)
        if match:
            return int(match.group())
        return None

    # ── Abstract ─────────────────────────────────────────────────────────────

    def _resolve_abstract(self, doc: ParsedDocument, first_page: str) -> Optional[str]:
        if doc.abstract:
            return doc.abstract

        # Try to find abstract section in first page
        pattern = re.compile(
            r"abstract[:\s—]+(.*?)(?=\n\s*\n|\n[A-Z][a-z]+\s*\n|\n1\.?\s)",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(first_page)
        if match:
            return match.group(1).strip()[:2000]
        return None

    # ── DOI ──────────────────────────────────────────────────────────────────

    def _extract_doi(self, full_text: str) -> Optional[str]:
        match = re.search(r"\b(10\.\d{4,}/[^\s]+)", full_text[:2000])
        if match:
            return match.group(1).rstrip(".,;)")
        return None

    # ── Venue ─────────────────────────────────────────────────────────────────

    def _extract_venue(self, first_page: str) -> Optional[str]:
        """Look for conference/journal name patterns."""
        patterns = [
            r"(?:proceedings of|in|published in)\s+([A-Z][^\n]{5,80})",
            r"((?:NeurIPS|ICML|ICLR|ACL|EMNLP|CVPR|ICCV|ECCV|AAAI|IJCAI)[^\n]{0,50})",
        ]
        for pat in patterns:
            match = re.search(pat, first_page, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        return None

    # ── Keywords ─────────────────────────────────────────────────────────────

    def _extract_keywords(self, full_text: str) -> list[str]:
        pattern = re.compile(
            r"keywords?[:\s—]+(.*?)(?=\n\s*\n|\n[A-Z])",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(full_text[:3000])
        if match:
            kw_text = match.group(1).strip()
            keywords = re.split(r"[,;·•]\s*", kw_text)
            return [k.strip() for k in keywords if 2 < len(k.strip()) < 60][:20]
        return []
