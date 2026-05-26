"""
BM25 Keyword Retrieval Module
------------------------------
Implements BM25 keyword search using the rank_bm25 library.
Complements semantic search for exact keyword matching.
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


@dataclass
class BM25Result:
    chroma_id: str
    content: str
    score: float          # Normalized BM25 score (0-1)
    metadata: dict
    document_id: str
    page_number: Optional[int]
    chunk_index: int


class BM25Retriever:
    """
    In-memory BM25 index built from document chunks.
    Rebuilt on each query (suitable for moderate corpus sizes).
    For large corpora, consider persisting the index.
    """

    def __init__(self):
        self._corpus: list[dict] = []   # List of chunk dicts
        self._tokenized: list[list[str]] = []
        self._bm25: Optional[BM25Okapi] = None

    def build_index(self, chunks: list[dict]) -> None:
        """
        Build BM25 index from a list of chunk dicts.
        Each dict must have: chroma_id, content, metadata, document_id, page_number, chunk_index
        """
        self._corpus = chunks
        self._tokenized = [self._tokenize(c["content"]) for c in chunks]
        self._bm25 = BM25Okapi(self._tokenized)
        logger.info(f"BM25 index built with {len(chunks)} documents")

    def search(self, query: str, top_k: int = 10) -> list[BM25Result]:
        """
        Search the BM25 index for the given query.

        Returns:
            List of BM25Result sorted by score (descending)
        """
        if self._bm25 is None or not self._corpus:
            logger.warning("BM25 index is empty. Call build_index() first.")
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Normalize scores to 0-1 range
        max_score = max(scores) if max(scores) > 0 else 1.0
        normalized_scores = scores / max_score

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:top_k]

        results = []
        for idx in top_indices:
            if normalized_scores[idx] <= 0:
                continue
            chunk = self._corpus[idx]
            meta = chunk.get("metadata", {})
            results.append(BM25Result(
                chroma_id=chunk["chroma_id"],
                content=chunk["content"],
                score=float(normalized_scores[idx]),
                metadata=meta,
                document_id=str(chunk.get("document_id", meta.get("document_id", ""))),
                page_number=chunk.get("page_number", meta.get("page_number")),
                chunk_index=int(chunk.get("chunk_index", meta.get("chunk_index", 0))),
            ))

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        # Remove punctuation except hyphens in compound words
        text = re.sub(r"[^\w\s-]", " ", text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 1]


class BM25IndexManager:
    """
    Manages BM25 index lifecycle.
    Loads chunks from ChromaDB or PostgreSQL for indexing.
    """

    def __init__(self):
        self.retriever = BM25Retriever()
        self._indexed = False

    def load_from_chroma(self, vector_store) -> None:
        """Load all chunks from ChromaDB and build BM25 index."""
        from backend.retrieval.vector_store import ChromaVectorStore

        logger.info("Loading chunks from ChromaDB for BM25 indexing...")
        collection = vector_store.collection

        # Get all documents from ChromaDB
        all_data = collection.get(include=["documents", "metadatas"])

        if not all_data["ids"]:
            logger.warning("No chunks found in ChromaDB for BM25 indexing")
            return

        chunks = []
        for i, chroma_id in enumerate(all_data["ids"]):
            meta = all_data["metadatas"][i] or {}
            chunks.append({
                "chroma_id": chroma_id,
                "content": all_data["documents"][i],
                "metadata": meta,
                "document_id": str(meta.get("document_id", "")),
                "page_number": meta.get("page_number"),
                "chunk_index": int(meta.get("chunk_index", 0)),
            })

        self.retriever.build_index(chunks)
        self._indexed = True
        logger.info(f"BM25 index loaded with {len(chunks)} chunks")

    def search(self, query: str, top_k: int = 10) -> list[BM25Result]:
        if not self._indexed:
            logger.warning("BM25 index not loaded")
            return []
        return self.retriever.search(query, top_k)

    def add_chunks(self, new_chunks: list[dict]) -> None:
        """Incrementally add new chunks and rebuild index."""
        self.retriever._corpus.extend(new_chunks)
        self.retriever._tokenized.extend(
            [self.retriever._tokenize(c["content"]) for c in new_chunks]
        )
        self.retriever._bm25 = BM25Okapi(self.retriever._tokenized)
        logger.info(f"Added {len(new_chunks)} chunks to BM25 index")
