"""
Tests for the generation pipeline:
- Context window manager
- Citation formatter and verifier
- Hallucination guard (answer relevance)
"""
import pytest
from backend.generation.context_manager import ContextWindowManager, count_tokens
from backend.generation.citation_formatter import CitationFormatter
from backend.retrieval.reranker import RankedResult


def make_ranked_result(
    chroma_id: str,
    content: str,
    semantic_score: float = 0.85,
    title: str = "Attention Is All You Need",
    authors: list = None,
    year: int = 2017,
    page: int = 1,
) -> RankedResult:
    return RankedResult(
        chroma_id=chroma_id,
        content=content,
        rerank_score=0.9,
        rrf_score=0.8,
        semantic_score=semantic_score,
        metadata={"title": title, "year": year},
        document_id="doc1",
        page_number=page,
        chunk_index=0,
        title=title,
        authors=authors or ["Vaswani", "Shazeer", "Parmar"],
        year=year,
    )


# ── Context Window Manager tests ──────────────────────────────────────────────

class TestContextWindowManager:
    def setup_method(self):
        self.manager = ContextWindowManager(
            max_context_tokens=500,
            reserved_response_tokens=100,
        )

    def test_fit_small_context(self):
        chunks = [make_ranked_result(f"chunk_{i}", f"Short content {i}.") for i in range(3)]
        history = [{"role": "user", "content": "Previous question"}]
        result = self.manager.fit(chunks, history)
        assert len(result.chunks) > 0
        assert result.total_tokens > 0

    def test_fit_truncates_large_context(self):
        # Create chunks that together exceed the budget
        long_content = "word " * 200  # ~200 tokens each
        chunks = [make_ranked_result(f"chunk_{i}", long_content) for i in range(10)]
        result = self.manager.fit(chunks, [])
        # Should truncate to fit within budget
        assert result.chunks_truncated > 0
        assert len(result.chunks) < 10

    def test_fit_empty_chunks(self):
        result = self.manager.fit([], [])
        assert result.chunks == []
        assert result.history_turns == []

    def test_format_chunks_for_prompt(self):
        chunks = [
            make_ranked_result("doc1_chunk_3", "The Transformer uses self-attention.", page=5)
        ]
        formatted = self.manager.format_chunks_for_prompt(chunks)
        assert "CHUNK 1" in formatted
        assert "doc1_chunk_3" in formatted
        assert "Attention Is All You Need" in formatted
        assert "p.5" in formatted
        assert "self-attention" in formatted

    def test_format_history_for_prompt(self):
        history = [
            {"role": "user", "content": "What is attention?"},
            {"role": "assistant", "content": "Attention is a mechanism..."},
        ]
        formatted = self.manager.format_history_for_prompt(history)
        assert "User: What is attention?" in formatted
        assert "Assistant: Attention is a mechanism..." in formatted

    def test_format_empty_history(self):
        result = self.manager.format_history_for_prompt([])
        assert "No previous conversation" in result

    def test_count_tokens(self):
        text = "Hello world"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)


# ── Citation Formatter tests ──────────────────────────────────────────────────

class TestCitationFormatter:
    def setup_method(self):
        self.formatter = CitationFormatter()

    def test_format_citation_single_author(self):
        chunk = make_ranked_result("doc1_chunk_5", "content", authors=["Vaswani"])
        citation = self.formatter.format_citation(chunk)
        assert "Vaswani" in citation
        assert "2017" in citation
        assert "doc1_chunk_5" in citation

    def test_format_citation_multiple_authors(self):
        chunk = make_ranked_result(
            "doc1_chunk_5", "content",
            authors=["Vaswani", "Shazeer", "Parmar", "Uszkoreit"]
        )
        citation = self.formatter.format_citation(chunk)
        assert "et al." in citation

    def test_format_citation_two_authors(self):
        chunk = make_ranked_result(
            "doc1_chunk_5", "content",
            authors=["Vaswani", "Shazeer"]
        )
        citation = self.formatter.format_citation(chunk)
        assert "&" in citation

    def test_verify_citations_all_valid(self):
        chunks = [
            make_ranked_result("doc1_chunk_1", "Self-attention content"),
            make_ranked_result("doc1_chunk_2", "Multi-head attention content"),
        ]
        text = "The model uses self-attention [Vaswani, 2017, doc1_chunk_1] and multi-head attention [Vaswani, 2017, doc1_chunk_2]."
        cleaned, verified, hallucinated = self.formatter.verify_citations(text, chunks)
        assert len(hallucinated) == 0
        assert len(verified) == 2

    def test_verify_citations_detects_hallucination(self):
        chunks = [make_ranked_result("doc1_chunk_1", "Real content")]
        text = "The model uses attention [Vaswani, 2017, doc1_chunk_1] and also [Vaswani, 2017, fake_chunk_999]."
        cleaned, verified, hallucinated = self.formatter.verify_citations(text, chunks)
        assert "fake_chunk_999" in hallucinated
        assert len(verified) == 1
        assert "UNVERIFIED CITATION" in cleaned

    def test_extract_citations_from_text(self):
        text = "See [Vaswani et al., 2017, doc1_chunk_3] for details."
        citations = self.formatter.extract_citations_from_text(text)
        assert len(citations) == 1
        assert "doc1_chunk_3" in citations[0]

    def test_build_citation_panel(self):
        from backend.generation.citation_formatter import Citation
        citations = [
            Citation(
                chunk_id="doc1_chunk_1",
                title="Attention Is All You Need",
                authors=["Vaswani"],
                year=2017,
                page_number=3,
                content_snippet="The Transformer model...",
                is_verified=True,
            )
        ]
        panel = self.formatter.build_citation_panel(citations)
        assert len(panel) == 1
        assert panel[0]["chunk_id"] == "doc1_chunk_1"
        assert panel[0]["is_verified"] is True
        assert panel[0]["year"] == 2017
