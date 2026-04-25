"""
ImageProcessor
──────────────────────────────────────────────────────────────
Xử lý file ảnh độc lập (không nhúng trong PDF/DOCX):
  *.png, *.jpg, *.jpeg, *.bmp, *.tiff, *.tif, *.webp, *.gif

Pipeline:
  1. Mở ảnh bằng PIL
  2. Xử lý đa trang (TIFF multi-frame, GIF animated) — mỗi frame 1 chunk
  3. ImageOptimizer: resize → grayscale → denoise → binarize
  4. RapidOCR → TextCleaner.clean() → ChunkResult(content_type="ocr")

Nếu OCR confidence < OCR_MIN_CONF hoặc text quá ngắn: bỏ qua frame đó.
"""

from __future__ import annotations

import io
from typing import List

from PIL import Image, UnidentifiedImageError

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    run_ocr, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS, OCR_MIN_CONF


class ImageProcessor(BaseFileProcessor):
    """Processor cho file ảnh (PNG, JPG, TIFF, WEBP, GIF, BMP...)."""

    def process(self, file_path: str) -> List[ChunkResult]:
        try:
            img = Image.open(file_path)
        except (UnidentifiedImageError, OSError):
            return []

        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        frames = self._iter_frames(img)
        for frame_idx, frame in enumerate(frames):
            ocr_text, conf = run_ocr(frame)
            clean = cleaner.clean(ocr_text)

            if len(clean.strip()) < MIN_CHUNK_CHARS or conf < OCR_MIN_CONF:
                continue

            chunks.append(self._make_ocr_chunk(
                clean,
                page_number=frame_idx,
                image_index=frame_idx,
                ocr_confidence=conf,
                section_title=f"Frame {frame_idx}" if frame_idx > 0 else None,
            ))

        return chunks

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _iter_frames(img: Image.Image):
        """
        Yield từng frame của ảnh.
        Hỗ trợ multi-page TIFF, animated GIF.
        Ảnh đơn: yield chính nó.
        """
        try:
            frame_idx = 0
            while True:
                img.seek(frame_idx)
                # Copy frame để tránh lỗi khi seek tiếp
                buf = io.BytesIO()
                img.copy().save(buf, format="PNG")
                buf.seek(0)
                yield Image.open(buf)
                frame_idx += 1
        except EOFError:
            # Hết frame
            pass
        except Exception:
            # Ảnh không hỗ trợ seek → yield trực tiếp
            yield img
