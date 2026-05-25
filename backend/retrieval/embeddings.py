"""
Embedding Generation Module
----------------------------
Uses sentence-transformers/all-MiniLM-L6-v2 for embedding generation.

Justification:
- all-MiniLM-L6-v2: Strong balance between accuracy (MTEB score ~56),
  latency (~14ms/sentence on CPU), and cost (free, local).
  384-dimensional vectors keep storage and search fast.
- Alternative: text-embedding-ada-002 (OpenAI) for higher accuracy
  at ~$0.0001/1K tokens — suitable for production with budget.

Includes:
- Batch embedding processor
- Redis-based embedding cache (TTL: 24h)
"""
import hashlib
import json
import logging
from typing import Optional

import numpy as np
import redis
from sentence_transformers import SentenceTransformer

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Redis cache client ────────────────────────────────────────────────────────
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=False)
    return _redis_client


# ── Embedding model (singleton) ───────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
    return _model


class EmbeddingGenerator:
    """
    Generates embeddings with Redis caching.
    Cache key: SHA-256 of text content.
    Cache TTL: 24 hours.
    """

    CACHE_TTL = 86400  # 24 hours
    CACHE_PREFIX = "emb:"

    def __init__(self):
        self.model = get_model()
        self.redis = get_redis()
        self.dimension = settings.embedding_dimension

    def embed(self, text: str) -> list[float]:
        """Embed a single text string. Uses cache if available."""
        cache_key = self._cache_key(text)

        # Try cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,  # L2 normalize for cosine similarity
            show_progress_bar=False,
        ).tolist()

        # Store in cache
        self._set_cached(cache_key, embedding)
        return embedding

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """
        Embed a batch of texts efficiently.
        Checks cache for each text, only computes missing embeddings.
        """
        if not texts:
            return []

        results: list[Optional[list[float]]] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            cached = self._get_cached(cache_key)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        logger.info(
            f"Embedding batch: {len(texts)} total, "
            f"{len(uncached_texts)} cache misses"
        )

        # Batch encode uncached texts
        if uncached_texts:
            embeddings = self.model.encode(
                uncached_texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=len(uncached_texts) > 10,
            )

            for idx, (orig_idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                embedding = embeddings[idx].tolist()
                results[orig_idx] = embedding
                # Cache the result
                self._set_cached(self._cache_key(text), embedding)

        return results  # type: ignore

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a search query.
        Queries are prefixed with 'query: ' for asymmetric search models.
        """
        return self.embed(f"query: {query}")

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _cache_key(self, text: str) -> str:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.CACHE_PREFIX}{text_hash}"

    def _get_cached(self, key: str) -> Optional[list[float]]:
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")
        return None

    def _set_cached(self, key: str, embedding: list[float]) -> None:
        try:
            self.redis.setex(key, self.CACHE_TTL, json.dumps(embedding))
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
