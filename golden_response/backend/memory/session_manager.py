"""
Conversation Memory Manager
-----------------------------
Manages conversation history using Redis (primary) with PostgreSQL backup.
- Stores last 10 turns per session
- 24-hour TTL per session
- Redis key structure: session:{session_id}:history
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import redis

from backend.config import settings

logger = logging.getLogger(__name__)

# Redis key patterns
SESSION_HISTORY_KEY = "session:{session_id}:history"
SESSION_META_KEY = "session:{session_id}:meta"


class ConversationMemoryManager:
    """
    Manages per-session conversation history in Redis.
    """

    MAX_TURNS = settings.conversation_history_turns  # 10 turns
    TTL = settings.session_ttl_seconds               # 24 hours

    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    def get_history(self, session_id: str) -> list[dict]:
        """
        Retrieve conversation history for a session.

        Returns:
            List of turn dicts: [{"role": "user"|"assistant", "content": "..."}]
        """
        key = SESSION_HISTORY_KEY.format(session_id=session_id)
        try:
            data = self.redis.get(key)
            if data:
                history = json.loads(data)
                # Return last MAX_TURNS turns
                return history[-self.MAX_TURNS * 2:]  # *2 for user+assistant pairs
            return []
        except Exception as e:
            logger.error(f"Failed to get history for session {session_id}: {e}")
            return []

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        citations: Optional[list] = None,
        confidence_score: Optional[float] = None,
    ) -> None:
        """
        Add a user-assistant turn to the session history.
        Maintains rolling window of MAX_TURNS turns.
        """
        key = SESSION_HISTORY_KEY.format(session_id=session_id)
        try:
            # Get existing history
            existing = self.get_history(session_id)

            # Add new turns
            existing.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat(),
            })
            existing.append({
                "role": "assistant",
                "content": assistant_message,
                "citations": citations or [],
                "confidence_score": confidence_score,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Keep only last MAX_TURNS * 2 messages
            trimmed = existing[-(self.MAX_TURNS * 2):]

            # Save back to Redis with TTL refresh
            self.redis.setex(key, self.TTL, json.dumps(trimmed))
            logger.debug(f"Added turn to session {session_id}, total: {len(trimmed)}")

        except Exception as e:
            logger.error(f"Failed to add turn for session {session_id}: {e}")

    def clear_history(self, session_id: str) -> bool:
        """Clear all conversation history for a session."""
        key = SESSION_HISTORY_KEY.format(session_id=session_id)
        try:
            self.redis.delete(key)
            logger.info(f"Cleared history for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear history for session {session_id}: {e}")
            return False

    def create_session(self, user_id: str) -> str:
        """Create a new session and return the session ID."""
        session_id = str(uuid.uuid4())
        meta_key = SESSION_META_KEY.format(session_id=session_id)
        meta = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "session_id": session_id,
        }
        try:
            self.redis.setex(meta_key, self.TTL, json.dumps(meta))
        except Exception as e:
            logger.error(f"Failed to create session metadata: {e}")
        return session_id

    def get_session_meta(self, session_id: str) -> Optional[dict]:
        """Get session metadata."""
        meta_key = SESSION_META_KEY.format(session_id=session_id)
        try:
            data = self.redis.get(meta_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session meta: {e}")
            return None

    def refresh_ttl(self, session_id: str) -> None:
        """Refresh TTL for an active session."""
        for key_template in [SESSION_HISTORY_KEY, SESSION_META_KEY]:
            key = key_template.format(session_id=session_id)
            try:
                self.redis.expire(key, self.TTL)
            except Exception as e:
                logger.warning(f"Failed to refresh TTL for {key}: {e}")

    def get_formatted_history(self, session_id: str) -> list[dict]:
        """Get history formatted for LLM context (role + content only)."""
        history = self.get_history(session_id)
        return [
            {"role": turn["role"], "content": turn["content"]}
            for turn in history
        ]
