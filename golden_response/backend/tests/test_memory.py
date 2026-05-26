"""
Tests for the conversation memory manager.
"""
import json
import pytest
from unittest.mock import MagicMock, patch


class TestConversationMemoryManager:
    def setup_method(self):
        """Set up a memory manager with a mocked Redis client."""
        with patch("backend.memory.session_manager.redis.from_url") as mock_redis_factory:
            self.mock_redis = MagicMock()
            mock_redis_factory.return_value = self.mock_redis

            from backend.memory.session_manager import ConversationMemoryManager
            self.manager = ConversationMemoryManager()
            self.manager.redis = self.mock_redis

    def test_get_history_empty(self):
        self.mock_redis.get.return_value = None
        history = self.manager.get_history("session-123")
        assert history == []

    def test_get_history_with_data(self):
        turns = [
            {"role": "user", "content": "What is attention?", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Attention is...", "timestamp": "2024-01-01T00:00:01"},
        ]
        self.mock_redis.get.return_value = json.dumps(turns)
        history = self.manager.get_history("session-123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_add_turn_stores_in_redis(self):
        self.mock_redis.get.return_value = None  # Empty history
        self.manager.add_turn(
            session_id="session-123",
            user_message="What is the Transformer?",
            assistant_message="The Transformer is a model...",
            citations=[{"chunk_id": "doc1_chunk_1"}],
            confidence_score=0.87,
        )
        # Verify setex was called
        assert self.mock_redis.setex.called
        call_args = self.mock_redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        data = json.loads(call_args[0][2])

        assert "session-123" in key
        assert ttl == self.manager.TTL
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "What is the Transformer?"
        assert data[1]["role"] == "assistant"
        assert data[1]["confidence_score"] == 0.87

    def test_add_turn_rolling_window(self):
        """Verify that history is trimmed to MAX_TURNS * 2 messages."""
        # Pre-populate with MAX_TURNS * 2 messages
        existing = []
        for i in range(self.manager.MAX_TURNS):
            existing.append({"role": "user", "content": f"Q{i}", "timestamp": "t"})
            existing.append({"role": "assistant", "content": f"A{i}", "timestamp": "t"})

        self.mock_redis.get.return_value = json.dumps(existing)
        self.manager.add_turn("session-123", "New Q", "New A")

        call_args = self.mock_redis.setex.call_args
        data = json.loads(call_args[0][2])
        # Should not exceed MAX_TURNS * 2
        assert len(data) <= self.manager.MAX_TURNS * 2

    def test_clear_history(self):
        self.mock_redis.delete.return_value = 1
        result = self.manager.clear_history("session-123")
        assert result is True
        self.mock_redis.delete.assert_called_once()

    def test_create_session_returns_uuid(self):
        self.mock_redis.setex.return_value = True
        session_id = self.manager.create_session("user-456")
        assert len(session_id) == 36  # UUID format
        assert "-" in session_id

    def test_get_formatted_history(self):
        turns = [
            {"role": "user", "content": "Q1", "timestamp": "t", "citations": []},
            {"role": "assistant", "content": "A1", "timestamp": "t", "confidence_score": 0.9},
        ]
        self.mock_redis.get.return_value = json.dumps(turns)
        formatted = self.manager.get_formatted_history("session-123")
        assert len(formatted) == 2
        # Should only have role and content
        assert "role" in formatted[0]
        assert "content" in formatted[0]

    def test_redis_error_returns_empty(self):
        self.mock_redis.get.side_effect = Exception("Redis connection error")
        history = self.manager.get_history("session-123")
        assert history == []
