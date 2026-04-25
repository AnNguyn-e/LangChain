"""
CSVProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.csv:

  - Thử nhiều encoding (utf-8, utf-8-sig, latin-1, cp1258)
  - Thử auto-detect delimiter (csv.Sniffer)
  - Mỗi hàng → "col1: val1 | col2: val2 | ..."
  - Gộp ROWS_PER_CHUNK hàng thành 1 table chunk
  - Hàng có toàn giá trị rỗng bị bỏ qua
"""

from __future__ import annotations

import csv
import io
from typing import List

from app.processors.base import BaseFileProcessor, TextCleaner, ChunkResult
from app.processors.constants import MIN_CHUNK_CHARS

_ROWS_PER_CHUNK = 20
_ENCODINGS = ["utf-8-sig", "utf-8", "cp1258", "latin-1"]


class CSVProcessor(BaseFileProcessor):
    """Processor cho file *.csv."""

    def process(self, file_path: str) -> List[ChunkResult]:
        raw = self._read(file_path)
        if not raw:
            return []

        dialect, headers, rows = self._parse(raw)
        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        for i in range(0, len(rows), _ROWS_PER_CHUNK):
            batch = rows[i: i + _ROWS_PER_CHUNK]
            lines: List[str] = []
            for row in batch:
                cells = [cleaner.clean_table_cell(v) for v in row]
                line = " | ".join(
                    f"{h}: {v}" for h, v in zip(headers, cells) if h or v
                )
                if line.strip():
                    lines.append(line)

            content = "\n".join(lines)
            if len(content.strip()) >= MIN_CHUNK_CHARS:
                chunks.append(self._make_table_chunk(
                    content,
                    section_title=f"Rows {i + 1}–{i + len(batch)}",
                ))

        return chunks

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _read(file_path: str) -> str:
        """Đọc file với fallback encoding."""
        for enc in _ENCODINGS:
            try:
                with open(file_path, "r", encoding=enc, newline="") as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")

    @staticmethod
    def _parse(raw: str):
        """Detect delimiter → parse header + rows."""
        sample = raw[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # fallback: comma

        reader = csv.reader(io.StringIO(raw), dialect)
        all_rows = list(reader)

        if not all_rows:
            return dialect, [], []

        headers = [h.strip() for h in all_rows[0]]
        data_rows = [
            row for row in all_rows[1:]
            if any(v.strip() for v in row)  # bỏ hàng rỗng
        ]
        return dialect, headers, data_rows
