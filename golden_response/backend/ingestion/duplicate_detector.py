"""
Duplicate Detection Utility
----------------------------
Uses SHA-256 hash of file content to detect duplicate uploads.
"""
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str | Path) -> str:
    """
    Compute SHA-256 hash of a file.
    Reads in 64KB chunks to handle large files efficiently.
    """
    sha256 = hashlib.sha256()
    file_path = Path(file_path)

    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)

    digest = sha256.hexdigest()
    logger.debug(f"SHA-256 for {file_path.name}: {digest}")
    return digest


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes (e.g., uploaded file content)."""
    return hashlib.sha256(data).hexdigest()
