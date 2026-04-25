"""
TXTProcessor
──────────────────────────────────────────────────────────────
Xử lý file văn bản thuần:
  *.txt, *.log, *.yaml, *.yml, *.toml, *.ini, *.cfg, *.env, ...

Chiến lược:
  - Thử các encoding phổ biến (utf-8, utf-16, latin-1)
  - Clean → split → trả về text chunks
"""

from __future__ import annotations

from typing import List

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS

# Thứ tự thử encoding
_ENCODINGS = ["utf-8", "utf-8-sig", "utf-16", "cp1258", "latin-1"]


class TXTProcessor(BaseFileProcessor):
    """Processor cho file văn bản thuần."""

    def process(self, file_path: str) -> List[ChunkResult]:
        raw = self._read_file(file_path)
        cleaner = TextCleaner()
        clean = cleaner.clean(raw)

        return [
            self._make_text_chunk(content, s, e)
            for content, s, e in split_text(clean)
            if len(content.strip()) >= MIN_CHUNK_CHARS
        ]

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(file_path: str) -> str:
        """Thử nhiều encoding, fallback về replace mode."""
        for enc in _ENCODINGS:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        # Cuối cùng: đọc binary và decode với replace
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")
