"""
PDFProcessor
──────────────────────────────────────────────────────────────
Xử lý file PDF:
  - Mỗi trang chạy song song (ThreadPoolExecutor)
  - Text: extract → clean → split chunks
  - Images: extract embedded images → ImageOptimizer → RapidOCR

Thư viện: pypdf
"""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from PIL import Image
from pypdf import PdfReader

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    run_ocr, split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS, OCR_MIN_CONF, MAX_WORKERS


class PDFProcessor(BaseFileProcessor):
    """Processor cho file *.pdf."""

    def process(self, file_path: str) -> List[ChunkResult]:
        reader = PdfReader(file_path)

        all_chunks: List[ChunkResult] = []
        page_results: dict[int, List[ChunkResult]] = {}

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self._process_page, page, i): i
                for i, page in enumerate(reader.pages)
            }
            for fut in as_completed(futures):
                page_num = futures[fut]
                try:
                    page_results[page_num] = fut.result()
                except Exception:
                    page_results[page_num] = []

        # Ghép chunks theo đúng thứ tự trang
        for i in sorted(page_results):
            all_chunks.extend(page_results[i])

        return all_chunks

    # ── Private ─────────────────────────────────────────────────────────────

    def _process_page(self, page, page_num: int) -> List[ChunkResult]:
        """Xử lý một trang PDF: text + embedded images."""
        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        # ── Text ────────────────────────────────────────────────────────────
        raw = page.extract_text() or ""
        clean = cleaner.clean(raw)
        if len(clean) >= MIN_CHUNK_CHARS:
            for content, s, e in split_text(clean):
                if len(content.strip()) >= MIN_CHUNK_CHARS:
                    chunks.append(self._make_text_chunk(
                        content, s, e,
                        page_number=page_num,
                    ))

        # ── Embedded images → OCR ────────────────────────────────────────────
        if hasattr(page, "images"):
            for img_idx, img_obj in enumerate(page.images):
                try:
                    # pypdf ≥ 3: img_obj là ImageFile, có .data
                    data = getattr(img_obj, "data", None) or img_obj.get("data", b"")
                    if not data:
                        continue
                    pil_img = Image.open(io.BytesIO(data))
                    ocr_text, conf = run_ocr(pil_img)
                    ocr_clean = cleaner.clean(ocr_text)
                    if len(ocr_clean.strip()) >= MIN_CHUNK_CHARS and conf >= OCR_MIN_CONF:
                        chunks.append(self._make_ocr_chunk(
                            ocr_clean,
                            page_number=page_num,
                            image_index=img_idx,
                            ocr_confidence=conf,
                        ))
                except Exception:
                    pass

        return chunks