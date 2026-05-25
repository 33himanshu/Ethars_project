"""
ChromaDB Vector Store Module
-----------------------------
Manages the ChromaDB collection for semantic vector search.

Justification for ChromaDB:
- Open-source, no vendor lock-in
- Simple Python SDK with async-friendly interface
- Supports both local (embedded) and client-server modes
- Built-in metadata filtering
- Easy Docker deployment
"""
import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chroma_id: str
    content: str
    score: float          # Cosine similarity (0-1, higher = more similar)
    metadata: dict
    document_id: str
    page_number: Optional[int]
    chunk_index: int


class ChromaVectorStore:
    """
    Wrapper around ChromaDB for vector storage and retrieval.
    Connects to ChromaDB server (HTTP client mode for production).
    """

    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = settings.chroma_collection
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine distance
            )
        return self._collection

    def add_chunk(
        self,
        chroma_id: str,
        text: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        """Add a single chunk to the vector store."""
        # ChromaDB metadata values must be str, int, float, or bool
        clean_meta = self._sanitize_metadata(metadata)
        self.collection.add(
            ids=[chroma_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[clean_meta],
        )

    def add_chunks_batch(
        self,
        chroma_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """Batch add chunks for efficiency."""
        clean_metas = [self._sanitize_metadata(m) for m in metadatas]
        self.collection.add(
            ids=chroma_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=clean_metas,
        )
        logger.info(f"Added {len(chroma_ids)} chunks to ChromaDB")

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        Semantic vector search.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: ChromaDB where clause, e.g. {"year": {"$gte": 2020}}

        Returns:
            List of SearchResult sorted by similarity (descending)
        """
        where = self._build_where_clause(filters) if filters else None

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self.collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = self.collection.query(**query_kwargs)

        search_results = []
        if not results["ids"] or not results["ids"][0]:
            return []

        for i, chroma_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - (distance / 2)
            score = 1.0 - (distance / 2.0)
            meta = results["metadatas"][0][i] or {}
            content = results["documents"][0][i] or ""

            search_results.append(SearchResult(
                chroma_id=chroma_id,
                content=content,
                score=score,
                metadata=meta,
                document_id=str(meta.get("document_id", "")),
                page_number=meta.get("page_number"),
                chunk_index=int(meta.get("chunk_index", 0)),
            ))

        return sorted(search_results, key=lambda x: x.score, reverse=True)

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to a document."""
        self.collection.delete(
            where={"document_id": {"$eq": document_id}}
        )
        logger.info(f"Deleted all chunks for document {document_id}")

    def get_chunk_by_id(self, chroma_id: str) -> Optional[SearchResult]:
        """Retrieve a specific chunk by its ChromaDB ID."""
        result = self.collection.get(
            ids=[chroma_id],
            include=["documents", "metadatas"],
        )
        if not result["ids"]:
            return None
        meta = result["metadatas"][0] or {}
        return SearchResult(
            chroma_id=chroma_id,
            content=result["documents"][0],
            score=1.0,
            metadata=meta,
            document_id=str(meta.get("document_id", "")),
            page_number=meta.get("page_number"),
            chunk_index=int(meta.get("chunk_index", 0)),
        )

    def count(self) -> int:
        return self.collection.count()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sanitize_metadata(self, metadata: dict) -> dict:
        """Ensure all metadata values are ChromaDB-compatible types."""
        clean = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = ""
            elif isinstance(v, list):
                clean[k] = ", ".join(str(i) for i in v)
            else:
                clean[k] = str(v)
        return clean

    def _build_where_clause(self, filters: dict) -> dict:
        """
        Build ChromaDB where clause from user-friendly filter dict.
        Example input: {"author": "Vaswani", "year": 2017}
        """
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                conditions.append({key: value})
            else:
                conditions.append({key: {"$eq": value}})

        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
