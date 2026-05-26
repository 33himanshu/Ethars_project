"""
PDF Parser Module
-----------------
Extracts text and metadata from PDF files using PyMuPDF (fitz).
Falls back to pdfplumber for complex layouts, then Tesseract OCR for scanned PDFs.
"""
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    is_ocr: bool = False


@dataclass
class ParsedDocument:
    title: str
    authors: list[str]
    publication_year: Optional[int]
    abstract: Optional[str]
    pages: list[PageContent]
    full_text: str
    page_count: int
    metadata: dict = field(default_factory=dict)


class PDFParser:
    """
    Multi-strategy PDF parser:
    1. PyMuPDF (fastest, handles most PDFs)
    2. pdfplumber (better for complex table/column layouts)
    3. Tesseract OCR (fallback for scanned/image-only PDFs)
    """

    MIN_TEXT_LENGTH_PER_PAGE = 50  # chars; below this triggers OCR fallback

    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Main entry point. Returns a ParsedDocument."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info(f"Parsing PDF: {file_path.name}")

        # Strategy 1: PyMuPDF
        pages = self._parse_with_pymupdf(file_path)

        # Check if text extraction was successful
        total_text = sum(len(p.text) for p in pages)
        if total_text < self.MIN_TEXT_LENGTH_PER_PAGE * len(pages):
            logger.warning(f"Low text yield with PyMuPDF ({total_text} chars), trying pdfplumber")
            pages = self._parse_with_pdfplumber(file_path)

        # Strategy 3: OCR fallback for pages still lacking text
        pages = self._ocr_fallback(file_path, pages)

        full_text = "\n\n".join(p.text for p in pages if p.text.strip())
        metadata = self._extract_pymupdf_metadata(file_path)

        return ParsedDocument(
            title=metadata.get("title", file_path.stem),
            authors=self._parse_authors(metadata.get("author", "")),
            publication_year=self._extract_year(metadata),
            abstract=self._extract_abstract(full_text),
            pages=pages,
            full_text=full_text,
            page_count=len(pages),
            metadata=metadata,
        )

    # ── Strategy 1: PyMuPDF ──────────────────────────────────────────────────

    def _parse_with_pymupdf(self, file_path: Path) -> list[PageContent]:
        pages = []
        with fitz.open(str(file_path)) as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text")
                pages.append(PageContent(page_number=i + 1, text=text.strip()))
        return pages

    def _extract_pymupdf_metadata(self, file_path: Path) -> dict:
        with fitz.open(str(file_path)) as doc:
            meta = doc.metadata or {}
        return {k: v for k, v in meta.items() if v}

    # ── Strategy 2: pdfplumber ───────────────────────────────────────────────

    def _parse_with_pdfplumber(self, file_path: Path) -> list[PageContent]:
        pages = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append(PageContent(page_number=i + 1, text=text.strip()))
        return pages

    # ── Strategy 3: OCR fallback ─────────────────────────────────────────────

    def _ocr_fallback(self, file_path: Path, pages: list[PageContent]) -> list[PageContent]:
        """Apply Tesseract OCR to pages with insufficient text."""
        result = []
        with fitz.open(str(file_path)) as doc:
            for page_content in pages:
                if len(page_content.text) < self.MIN_TEXT_LENGTH_PER_PAGE:
                    logger.info(f"Applying OCR to page {page_content.page_number}")
                    fitz_page = doc[page_content.page_number - 1]
                    pix = fitz_page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img, lang="eng")
                    result.append(PageContent(
                        page_number=page_content.page_number,
                        text=ocr_text.strip(),
                        is_ocr=True,
                    ))
                else:
                    result.append(page_content)
        return result

    # ── Metadata helpers ─────────────────────────────────────────────────────

    def _parse_authors(self, author_str: str) -> list[str]:
        if not author_str:
            return []
        # Handle semicolon or comma-separated author lists
        if ";" in author_str:
            return [a.strip() for a in author_str.split(";") if a.strip()]
        return [a.strip() for a in author_str.split(",") if a.strip()]

    def _extract_year(self, metadata: dict) -> Optional[int]:
        import re
        for key in ("creationDate", "modDate", "date"):
            val = metadata.get(key, "")
            match = re.search(r"(19|20)\d{2}", str(val))
            if match:
                return int(match.group())
        return None

    def _extract_abstract(self, full_text: str) -> Optional[str]:
        """Heuristic: extract text between 'Abstract' and 'Introduction' headings."""
        import re
        pattern = re.compile(
            r"abstract[:\s]+(.*?)(?=\n\s*\n|\nintroduction|\n1\.?\s+introduction)",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(full_text[:3000])  # Only look in first 3000 chars
        if match:
            return match.group(1).strip()[:1500]
        return None
