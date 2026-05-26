"""
Text Chunking Module
--------------------
Splits document text into overlapping, sentence-aware chunks.
- Chunk size: 512 tokens
- Overlap: 50 tokens
- Strategy: sentence-aware splitting to avoid mid-sentence cuts
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional

import tiktoken

from backend.config import settings

logger = logging.getLogger(__name__)

# Use cl100k_base tokenizer (compatible with most modern LLMs)
_TOKENIZER = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int]
    start_char: int
    end_char: int
    metadata: dict


class SentenceAwareChunker:
    """
    Splits text into chunks respecting sentence boundaries.
    Uses tiktoken for accurate token counting.
    """

    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = _TOKENIZER

    def chunk_document(
        self,
        full_text: str,
        page_map: Optional[dict[int, int]] = None,  # char_offset -> page_number
        doc_metadata: Optional[dict] = None,
    ) -> list[TextChunk]:
        """
        Chunk a full document text into overlapping sentence-aware chunks.

        Args:
            full_text: Complete document text
            page_map: Optional mapping of character offsets to page numbers
            doc_metadata: Document-level metadata to attach to each chunk

        Returns:
            List of TextChunk objects
        """
        if not full_text.strip():
            return []

        sentences = self._split_into_sentences(full_text)
        chunks = []
        current_tokens: list[str] = []
        current_text_parts: list[str] = []
        current_start_char = 0
        char_offset = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.tokenizer.encode(sentence)

            # If a single sentence exceeds chunk_size, split it by tokens
            if len(sentence_tokens) > self.chunk_size:
                # Flush current buffer first
                if current_tokens:
                    chunk = self._build_chunk(
                        chunk_index, current_text_parts, current_tokens,
                        current_start_char, char_offset, page_map, doc_metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    # Overlap: keep last overlap tokens
                    current_tokens, current_text_parts = self._apply_overlap(
                        current_tokens, current_text_parts
                    )
                    current_start_char = char_offset

                # Split long sentence into token windows
                for sub_chunk in self._split_by_tokens(sentence, sentence_tokens):
                    chunks.append(TextChunk(
                        chunk_index=chunk_index,
                        content=sub_chunk,
                        token_count=len(self.tokenizer.encode(sub_chunk)),
                        page_number=self._get_page(char_offset, page_map),
                        start_char=char_offset,
                        end_char=char_offset + len(sub_chunk),
                        metadata=doc_metadata or {},
                    ))
                    chunk_index += 1
                char_offset += len(sentence)
                continue

            # Check if adding this sentence exceeds chunk_size
            if len(current_tokens) + len(sentence_tokens) > self.chunk_size and current_tokens:
                chunk = self._build_chunk(
                    chunk_index, current_text_parts, current_tokens,
                    current_start_char, char_offset, page_map, doc_metadata
                )
                chunks.append(chunk)
                chunk_index += 1

                # Overlap: keep last overlap tokens
                current_tokens, current_text_parts = self._apply_overlap(
                    current_tokens, current_text_parts
                )
                current_start_char = char_offset

            current_text_parts.append(sentence)
            current_tokens.extend(sentence_tokens)
            char_offset += len(sentence)

        # Flush remaining text
        if current_tokens:
            chunk = self._build_chunk(
                chunk_index, current_text_parts, current_tokens,
                current_start_char, char_offset, page_map, doc_metadata
            )
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks from {len(full_text)} chars")
        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex (no NLTK dependency)."""
        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Split on sentence-ending punctuation followed by whitespace + capital
        sentence_endings = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|(?<=\n)\n'
        )
        parts = sentence_endings.split(text)
        # Re-attach the space that was consumed
        sentences = []
        for part in parts:
            stripped = part.strip()
            if stripped:
                sentences.append(stripped + " ")
        return sentences

    def _build_chunk(
        self, index, text_parts, tokens, start_char, end_char, page_map, metadata
    ) -> TextChunk:
        content = "".join(text_parts).strip()
        return TextChunk(
            chunk_index=index,
            content=content,
            token_count=len(tokens),
            page_number=self._get_page(start_char, page_map),
            start_char=start_char,
            end_char=end_char,
            metadata=metadata or {},
        )

    def _apply_overlap(
        self, tokens: list, text_parts: list
    ) -> tuple[list, list]:
        """Keep the last `chunk_overlap` tokens for the next chunk."""
        if len(tokens) <= self.chunk_overlap:
            return tokens[:], text_parts[:]
        # Approximate: keep last text_parts that sum to overlap tokens
        overlap_tokens = tokens[-self.chunk_overlap:]
        overlap_text = self.tokenizer.decode(overlap_tokens)
        return list(overlap_tokens), [overlap_text]

    def _split_by_tokens(self, text: str, tokens: list) -> list[str]:
        """Split a long text into token-sized windows."""
        chunks = []
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            window = tokens[i: i + self.chunk_size]
            chunks.append(self.tokenizer.decode(window))
        return chunks

    def _get_page(self, char_offset: int, page_map: Optional[dict]) -> Optional[int]:
        if not page_map:
            return None
        # Find the largest key <= char_offset
        page = None
        for offset, pg in sorted(page_map.items()):
            if offset <= char_offset:
                page = pg
            else:
                break
        return page
