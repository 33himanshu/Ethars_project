"""
Tests for JWT authentication:
- Token creation and validation
- Password hashing
- Registration and login flows
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from jose import jwt

from backend.config import settings
from backend.api.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    hash_token,
)


class TestTokenCreation:
    def test_create_access_token_structure(self):
        token = create_access_token("user-123", "researcher")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == "user-123"
        assert payload["role"] == "researcher"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_structure(self):
        token = create_refresh_token("user-123")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert "jti" in payload  # Unique token ID

    def test_access_token_expiry(self):
        token = create_access_token("user-123", "researcher")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        exp = datetime.utcfromtimestamp(payload["exp"])
        iat = datetime.utcfromtimestamp(payload["iat"])
        diff_minutes = (exp - iat).total_seconds() / 60
        assert abs(diff_minutes - settings.jwt_access_token_expire_minutes) < 1

    def test_refresh_token_expiry(self):
        token = create_refresh_token("user-123")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        exp = datetime.utcfromtimestamp(payload["exp"])
        iat = datetime.utcfromtimestamp(payload["iat"])
        diff_days = (exp - iat).total_seconds() / 86400
        assert abs(diff_days - settings.jwt_refresh_token_expire_days) < 0.1

    def test_different_users_different_tokens(self):
        token1 = create_access_token("user-1", "researcher")
        token2 = create_access_token("user-2", "researcher")
        assert token1 != token2

    def test_admin_role_in_token(self):
        token = create_access_token("admin-1", "admin")
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        assert payload["role"] == "admin"


class TestPasswordHashing:
    def test_hash_is_different_from_plain(self):
        plain = "SecurePassword123!"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_correct_password(self):
        plain = "SecurePassword123!"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_different_hashes(self):
        """bcrypt uses random salt → same password produces different hashes."""
        plain = "SamePassword"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True

    def test_token_hash_deterministic(self):
        """SHA-256 hash of token should be deterministic."""
        token = "some-refresh-token-value"
        assert hash_token(token) == hash_token(token)

    def test_token_hash_length(self):
        h = hash_token("any-token")
        assert len(h) == 64
