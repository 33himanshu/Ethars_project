"""
Pytest configuration and shared fixtures.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables before any imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://rag_user:testpassword@localhost:5432/rag_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-only")
os.environ.setdefault("APP_SECRET_KEY", "test-app-secret-key-for-testing-only")
os.environ.setdefault("CHROMA_HOST", "localhost")
os.environ.setdefault("CHROMA_PORT", "8001")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("backend.retrieval.embeddings.get_redis") as mock:
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model."""
    import numpy as np
    with patch("backend.retrieval.embeddings.get_model") as mock:
        model_mock = MagicMock()
        # Return a fixed 384-dim embedding
        model_mock.encode.return_value = np.random.rand(384).astype("float32")
        mock.return_value = model_mock
        yield model_mock


@pytest.fixture
def mock_chroma():
    """Mock ChromaDB client."""
    with patch("backend.retrieval.vector_store.chromadb.HttpClient") as mock:
        client_mock = MagicMock()
        collection_mock = MagicMock()
        collection_mock.count.return_value = 10
        collection_mock.query.return_value = {
            "ids": [["chunk_1", "chunk_2"]],
            "distances": [[0.1, 0.3]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[
                {"document_id": "doc1", "title": "Test", "chunk_index": 0, "page_number": 1},
                {"document_id": "doc1", "title": "Test", "chunk_index": 1, "page_number": 2},
            ]],
        }
        client_mock.get_or_create_collection.return_value = collection_mock
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def sample_ranked_results():
    """Sample RankedResult objects for testing."""
    from backend.retrieval.reranker import RankedResult
    return [
        RankedResult(
            chroma_id=f"doc1_chunk_{i}",
            content=f"The Transformer model uses self-attention. Chunk {i}.",
            rerank_score=0.9 - i * 0.1,
            rrf_score=0.8 - i * 0.1,
            semantic_score=0.85 - i * 0.05,
            metadata={"title": "Attention Is All You Need", "year": 2017},
            document_id="doc1",
            page_number=i + 1,
            chunk_index=i,
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar"],
            year=2017,
        )
        for i in range(5)
    ]
