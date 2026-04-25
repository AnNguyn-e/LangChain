"""
ExcelProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.xlsx / *.xls:

  - Đọc tất cả sheets
  - Mỗi sheet: xử lý như CSV (header + data rows → table chunks)
  - Hỗ trợ merged cells (openpyxl forward-fill)
  - Section title ghi rõ: "SheetName | Rows A–B"

Thư viện: openpyxl (xlsx), xlrd (xls legacy)
"""

from __future__ import annotations

import os
from typing import List

from app.processors.base import BaseFileProcessor, TextCleaner, ChunkResult
from app.processors.constants import MIN_CHUNK_CHARS

_ROWS_PER_CHUNK = 20


class ExcelProcessor(BaseFileProcessor):
    """Processor cho file *.xlsx / *.xls."""

    def process(self, file_path: str) -> List[ChunkResult]:
        import pandas as pd  # noqa: PLC0415

        ext = os.path.splitext(file_path)[1].lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"

        try:
            xls = pd.ExcelFile(file_path, engine=engine)
        except Exception:
            return []

        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        for sheet_name in xls.sheet_names:
            try:
                df = (
                    xls.parse(sheet_name, dtype=str, header=0)
                    .fillna("")
                    .astype(str)
                )
            except Exception:
                continue

            if df.empty:
                continue

            headers = [str(c).strip() for c in df.columns]
            rows_text: List[str] = []

            for _, row in df.iterrows():
                cells = [cleaner.clean_table_cell(row[c]) for c in df.columns]
                line = " | ".join(
                    f"{h}: {v}" for h, v in zip(headers, cells) if h or v
                )
                if line.strip():
                    rows_text.append(line)

            for i in range(0, len(rows_text), _ROWS_PER_CHUNK):
                batch = rows_text[i: i + _ROWS_PER_CHUNK]
                content = "\n".join(batch)
                if len(content.strip()) >= MIN_CHUNK_CHARS:
                    chunks.append(self._make_table_chunk(
                        content,
                        section_title=f"{sheet_name} | Rows {i + 1}–{i + len(batch)}",
                    ))

        return chunks
