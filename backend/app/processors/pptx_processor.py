"""
PPTXProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.pptx (và *.ppt qua python-pptx):

  Mỗi slide:
    Text:
      - Title shape → section_title
      - TextFrame → collect text lines → clean → split chunks
    Tables (trong slide):
      - Mỗi table → header + data rows → table chunks
    Images (embedded):
      - MSO_SHAPE_TYPE.PICTURE (13) → OCR

Thư viện: python-pptx
"""

from __future__ import annotations

import io
from typing import List

from PIL import Image

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    run_ocr, split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS, OCR_MIN_CONF

_ROWS_PER_CHUNK = 20
_MSO_PICTURE = 13   # MSO_SHAPE_TYPE.PICTURE


class PPTXProcessor(BaseFileProcessor):
    """Processor cho file *.pptx / *.ppt."""

    def process(self, file_path: str) -> List[ChunkResult]:
        from pptx import Presentation  # noqa: PLC0415

        prs = Presentation(file_path)
        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_title = self._get_slide_title(slide)
            slide_texts: List[str] = []

            for shape in slide.shapes:
                # ── Text ─────────────────────────────────────────────────────
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        line = " ".join(run.text for run in para.runs).strip()
                        if line and line != slide_title:
                            slide_texts.append(line)

                # ── Table ────────────────────────────────────────────────────
                if shape.has_table:
                    chunks.extend(self._extract_table(
                        shape.table, slide_num, slide_title, cleaner
                    ))

                # ── Image → OCR ──────────────────────────────────────────────
                if shape.shape_type == _MSO_PICTURE:
                    chunks.extend(self._ocr_shape(
                        shape, slide_num, slide_title, cleaner
                    ))

            # Gộp text của slide lại → split
            if slide_texts:
                combined = cleaner.clean("\n".join(slide_texts))
                for content, s, e in split_text(combined):
                    if len(content.strip()) >= MIN_CHUNK_CHARS:
                        chunks.append(self._make_text_chunk(
                            content, s, e,
                            page_number=slide_num,
                            section_title=slide_title or f"Slide {slide_num}",
                        ))

        return self._filter_chunks(chunks)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _get_slide_title(slide) -> str | None:
        """Lấy nội dung title shape nếu có."""
        try:
            title_shape = slide.shapes.title
            if title_shape and title_shape.has_text_frame:
                return title_shape.text_frame.text.strip() or None
        except Exception:
            pass
        return None

    def _extract_table(
        self, table, slide_num: int, slide_title: str | None, cleaner: TextCleaner
    ) -> List[ChunkResult]:
        """Chuyển PPTX table → table chunks."""
        chunks: List[ChunkResult] = []
        rows = table.rows
        if not rows:
            return chunks

        headers = [
            cleaner.clean_table_cell(cell.text)
            for cell in rows[0].cells
        ]
        rows_text: List[str] = []

        for row in rows[1:]:
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
                    section_title=f"Slide {slide_num} – Table | Rows {i + 1}–{i + len(batch)}",
                    page_number=slide_num,
                ))
        return chunks

    def _ocr_shape(
        self, shape, slide_num: int, slide_title: str | None, cleaner: TextCleaner
    ) -> List[ChunkResult]:
        """OCR một ảnh trong slide."""
        try:
            img_bytes = shape.image.blob
            pil_img = Image.open(io.BytesIO(img_bytes))
            ocr_text, conf = run_ocr(pil_img)
            ocr_clean = cleaner.clean(ocr_text)
            if len(ocr_clean.strip()) >= MIN_CHUNK_CHARS and conf >= OCR_MIN_CONF:
                return [self._make_ocr_chunk(
                    ocr_clean,
                    page_number=slide_num,
                    ocr_confidence=conf,
                    section_title=f"Slide {slide_num} – Image",
                )]
        except Exception:
            pass
        return []
