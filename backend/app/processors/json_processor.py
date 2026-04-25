"""
JSONProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.json:

Hỗ trợ 3 dạng phổ biến:
  1. List of objects (records) — giống CSV, xử lý thành table chunks
  2. Dict phẳng / lồng nhau — flatten thành "key.sub: value"
  3. JSON Lines (*.jsonl) — mỗi dòng là 1 JSON object

Nếu parse thất bại → fallback TXTProcessor.
"""

from __future__ import annotations

import json
from typing import Any, List

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS

_ROWS_PER_CHUNK = 20


class JSONProcessor(BaseFileProcessor):
    """Processor cho file *.json / *.jsonl."""

    def process(self, file_path: str) -> List[ChunkResult]:
        raw = self._read(file_path)
        cleaner = TextCleaner()

        # ── Thử parse JSON thuần ─────────────────────────────────────────
        data = None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            pass

        if data is not None:
            return self._process_data(data, cleaner)

        # ── Thử JSON Lines ───────────────────────────────────────────────
        records = self._try_jsonl(raw)
        if records:
            return self._process_data(records, cleaner)

        # ── Fallback: xử lý như plain text ──────────────────────────────
        clean = cleaner.clean(raw)
        return [
            self._make_text_chunk(content, s, e)
            for content, s, e in split_text(clean)
            if len(content.strip()) >= MIN_CHUNK_CHARS
        ]

    # ── Dispatch theo kiểu dữ liệu ───────────────────────────────────────────

    def _process_data(self, data: Any, cleaner: TextCleaner) -> List[ChunkResult]:
        if isinstance(data, list):
            return self._process_list(data, cleaner)
        else:
            return self._process_object(data, cleaner)

    def _process_list(self, records: list, cleaner: TextCleaner) -> List[ChunkResult]:
        """
        List of objects → table chunks (như CSV).
        List of primitives → join thành text chunk.
        """
        # List of dicts (records) → table-style
        if records and isinstance(records[0], dict):
            return self._records_to_table_chunks(records, cleaner)

        # List of primitives / mixed
        lines = [str(item) for item in records if item is not None]
        text = cleaner.clean("\n".join(lines))
        return [
            self._make_text_chunk(c, s, e)
            for c, s, e in split_text(text)
            if len(c.strip()) >= MIN_CHUNK_CHARS
        ]

    def _process_object(self, data: Any, cleaner: TextCleaner) -> List[ChunkResult]:
        """Dict / nested → flatten thành key: value rồi split."""
        flat = self._flatten(data)
        text = cleaner.clean(flat)
        return [
            self._make_text_chunk(c, s, e)
            for c, s, e in split_text(text)
            if len(c.strip()) >= MIN_CHUNK_CHARS
        ]

    def _records_to_table_chunks(
        self, records: List[dict], cleaner: TextCleaner
    ) -> List[ChunkResult]:
        """Chuyển list of dicts thành table chunks nhóm _ROWS_PER_CHUNK hàng."""
        # Gom tất cả keys
        all_keys: list = []
        for rec in records:
            for k in rec.keys():
                if k not in all_keys:
                    all_keys.append(k)

        rows_text: List[str] = []
        for rec in records:
            cells = []
            for k in all_keys:
                v = rec.get(k, "")
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                cells.append(f"{k}: {cleaner.clean_table_cell(str(v))}")
            line = " | ".join(c for c in cells if c.strip())
            if line.strip():
                rows_text.append(line)

        chunks: List[ChunkResult] = []
        for i in range(0, len(rows_text), _ROWS_PER_CHUNK):
            batch = rows_text[i: i + _ROWS_PER_CHUNK]
            content = "\n".join(batch)
            if len(content.strip()) >= MIN_CHUNK_CHARS:
                chunks.append(self._make_table_chunk(
                    content,
                    section_title=f"Records {i + 1}–{i + len(batch)}",
                ))
        return chunks

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _flatten(obj: Any, prefix: str = "") -> str:
        """Flatten JSON object → multi-line "key.sub: value"."""
        lines: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else str(k)
                lines.append(JSONProcessor._flatten(v, key))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                lines.append(JSONProcessor._flatten(item, f"{prefix}[{i}]"))
        else:
            lines.append(f"{prefix}: {obj}")
        return "\n".join(lines)

    @staticmethod
    def _try_jsonl(raw: str) -> List[dict] | None:
        """Thử parse JSON Lines — mỗi dòng là 1 JSON object."""
        records: List[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(obj)
            except json.JSONDecodeError:
                return None  # Không phải JSONL
        return records if records else None

    @staticmethod
    def _read(file_path: str) -> str:
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")
