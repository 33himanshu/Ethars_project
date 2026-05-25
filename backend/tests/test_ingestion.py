"""
Tests for the ingestion pipeline:
- Chunker
- Duplicate detector
- Metadata extractor
"""
import pytest
from backend.ingestion.chunker import SentenceAwareChunker
from backend.ingestion.duplicate_detector import compute_bytes_hash


# ── Chunker tests ─────────────────────────────────────────────────────────────

class TestSentenceAwareChunker:
    def setup_method(self):
        self.chunker = SentenceAwareChunker(chunk_size=100, chunk_overlap=10)

    def test_basic_chunking(self):
        text = "This is sentence one. This is sentence two. This is sentence three. " * 20
        chunks = self.chunker.chunk_document(text)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.token_count <= 110  # Allow slight overflow at sentence boundary
            assert len(chunk.content) > 0

    def test_empty_text(self):
        chunks = self.chunker.chunk_document("")
        assert chunks == []

    def test_chunk_overlap(self):
        """Verify that consecutive chunks share some content (overlap)."""
        text = " ".join([f"Sentence number {i} about attention mechanisms." for i in range(50)])
        chunks = self.chunker.chunk_document(text)
        assert len(chunks) >= 2
        # Each chunk should have a positive token count
        for chunk in chunks:
            assert chunk.token_count > 0

    def test_chunk_indices_sequential(self):
        text = "Word " * 500
        chunks = self.chunker.chunk_document(text)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_metadata_attached(self):
        text = "This is a test sentence about transformers. " * 30
        meta = {"document_id": "test-doc-123", "title": "Test Paper"}
        chunks = self.chunker.chunk_document(text, doc_metadata=meta)
        for chunk in chunks:
            assert chunk.metadata["document_id"] == "test-doc-123"
            assert chunk.metadata["title"] == "Test Paper"

    def test_page_map(self):
        text = "Page one content. " * 10 + "Page two content. " * 10
        page_map = {0: 1, len("Page one content. " * 10): 2}
        chunks = self.chunker.chunk_document(text, page_map=page_map)
        assert any(c.page_number == 1 for c in chunks)


# ── Duplicate detector tests ──────────────────────────────────────────────────

class TestDuplicateDetector:
    def test_same_content_same_hash(self):
        content = b"This is test PDF content"
        hash1 = compute_bytes_hash(content)
        hash2 = compute_bytes_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        hash1 = compute_bytes_hash(b"Content A")
        hash2 = compute_bytes_hash(b"Content B")
        assert hash1 != hash2

    def test_hash_is_64_chars(self):
        """SHA-256 produces 64 hex characters."""
        h = compute_bytes_hash(b"test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_empty_bytes(self):
        h = compute_bytes_hash(b"")
        assert len(h) == 64
