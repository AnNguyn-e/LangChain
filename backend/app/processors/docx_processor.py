"""
DOCXProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.docx (và *.doc thông qua python-docx):

  Text:
    - Duyệt từng paragraph, giữ thứ tự văn bản
    - Nhận diện heading qua paragraph.style.name
    - Gom text theo section (H1/H2) → split_text_by_sections

  Tables:
    - Mỗi table → mỗi hàng → "col1: val | col2: val"
    - Gộp nhiều hàng thành 1 chunk (ROWS_PER_CHUNK)

  Images (embedded):
    - Đọc từ document.part.rels → OCR

Thư viện: python-docx
"""

from __future__ import annotations

import io
from typing import List, Tuple

from PIL import Image

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    run_ocr, split_text, split_text_by_sections, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS, OCR_MIN_CONF

_ROWS_PER_CHUNK = 20


class DOCXProcessor(BaseFileProcessor):
    """Processor cho file *.docx / *.doc."""

    def process(self, file_path: str) -> List[ChunkResult]:
        import docx as python_docx  # noqa: PLC0415 (lazy import)

        doc = python_docx.Document(file_path)
        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        # ── 1. Text + Headings ───────────────────────────────────────────────
        chunks.extend(self._extract_text(doc, cleaner))

        # ── 2. Tables ────────────────────────────────────────────────────────
        chunks.extend(self._extract_tables(doc))

        # ── 3. Embedded images → OCR ─────────────────────────────────────────
        chunks.extend(self._extract_images(doc, cleaner))

        return self._filter_chunks(chunks)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _extract_text(self, doc, cleaner: TextCleaner) -> List[ChunkResult]:
        """Gom paragraph theo section heading rồi split."""
        sections: List[Tuple[str, str | None]] = []
        current_title: str | None = None
        current_paras: List[str] = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name: str = (para.style.name or "").lower()
            heading_level = self._heading_level(style_name)

            if heading_level is not None:
                # Lưu section cũ trước khi bắt đầu section mới
                if current_paras:
                    sections.append(
                        ("\n\n".join(current_paras), current_title)
                    )
                    current_paras = []
                current_title = text
            else:
                current_paras.append(text)

        # Section cuối
        if current_paras:
            sections.append(("\n\n".join(current_paras), current_title))

        chunks: List[ChunkResult] = []
        for raw_text, title in sections:
            clean = cleaner.clean(raw_text)
            for content, s, e in split_text(clean):
                if len(content.strip()) >= MIN_CHUNK_CHARS:
                    chunks.append(self._make_text_chunk(
                        content, s, e,
                        section_title=title,
                    ))
        return chunks

    def _extract_tables(self, doc) -> List[ChunkResult]:
        """Chuyển mỗi table thành table chunks."""
        chunks: List[ChunkResult] = []
        cleaner = TextCleaner()

        for tbl_idx, table in enumerate(doc.tables):
            if not table.rows:
                continue

            headers = [
                cleaner.clean_table_cell(cell.text)
                for cell in table.rows[0].cells
            ]
            rows_text: List[str] = []

            for row in table.rows[1:]:
                cells = [cleaner.clean_table_cell(c.text) for c in row.cells]
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
                        section_title=f"Table {tbl_idx + 1} | Rows {i + 1}–{i + len(batch)}",
                    ))
        return chunks

    def _extract_images(self, doc, cleaner: TextCleaner) -> List[ChunkResult]:
        """Duyệt relationships của DOCX để tìm ảnh nhúng → OCR."""
        chunks: List[ChunkResult] = []
        for idx, rel in enumerate(doc.part.rels.values()):
            if "image" not in rel.reltype:
                continue
            try:
                img_bytes = rel.target_part.blob
                pil_img = Image.open(io.BytesIO(img_bytes))
                ocr_text, conf = run_ocr(pil_img)
                ocr_clean = cleaner.clean(ocr_text)
                if len(ocr_clean.strip()) >= MIN_CHUNK_CHARS and conf >= OCR_MIN_CONF:
                    chunks.append(self._make_ocr_chunk(
                        ocr_clean,
                        image_index=idx,
                        ocr_confidence=conf,
                    ))
            except Exception:
                pass
        return chunks

    @staticmethod
    def _heading_level(style_name: str) -> int | None:
        """Trả về cấp heading (1-6) hoặc None nếu không phải heading."""
        for lvl in range(1, 7):
            if f"heading {lvl}" in style_name:
                return lvl
        return None
