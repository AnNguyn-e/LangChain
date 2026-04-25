"""
app/processors/base.py
──────────────────────────────────────────────────────────────
Abstract base class cho tất cả file processors.

Mỗi processor cụ thể (PDF, DOCX, ...) kế thừa BaseFileProcessor
và implement phương thức `process()`.

Re-export các utilities để các processor chỉ cần import từ base:
    from app.processors.base import BaseFileProcessor, TextCleaner, split_text, run_ocr
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

# ── Hằng số ─────────────────────────────────────────────────────────────────
from app.processors.constants import CHUNK_SIZE, CHUNK_OVERLAP

# ── Re-export tiện ích dùng chung ────────────────────────────────────────────
from app.processors._utils.text_cleaner import TextCleaner
from app.processors._utils.image_optimizer import ImageOptimizer, run_ocr
from app.processors._utils.text_splitter import split_text, split_text_by_sections


@dataclass
class ChunkResult:
    """Kết quả một chunk sau khi xử lý — trước khi lưu DB."""
    content: str
    content_type: str = "text"      # "text" | "ocr" | "table"
    page_number: Optional[int] = None
    page_number_end: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    section_title: Optional[str] = None
    heading_level: Optional[int] = None
    image_index: Optional[int] = None
    ocr_confidence: Optional[float] = None
    ocr_engine: Optional[str] = None
    chunk_strategy: str = "recursive"
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    is_table: bool = False
    is_header_footer: bool = False

__all__ = [
    "BaseFileProcessor",
    "TextCleaner",
    "ImageOptimizer",
    "run_ocr",
    "split_text",
    "split_text_by_sections",
    "ChunkResult",
]


class BaseFileProcessor(ABC):
    """
    Interface chung cho mọi file processor.

    Implement phương thức `process(file_path)` để:
      1. Đọc file
      2. Làm sạch nội dung
      3. Tách chunks (text / OCR / table)
      4. Trả về List[ChunkResult]

    Các ChunkResult này sẽ được ChunkPersister lưu vào DB
    và ChunkEmbedder nhúng vào vector store.
    """

    @abstractmethod
    def process(self, file_path: str) -> List[ChunkResult]:
        """
        Xử lý file và trả về danh sách chunks đã làm sạch.

        Args:
            file_path: Đường dẫn tuyệt đối tới file đã upload.

        Returns:
            List[ChunkResult]: Danh sách chunks, sẵn sàng để embed.
                               Trả về list rỗng nếu không trích xuất được gì.
        """
        ...

    # ── Helpers có thể dùng chung cho các subclass ───────────────────────────

    @staticmethod
    def _filter_chunks(
        chunks: List[ChunkResult],
        min_chars: int = 30,
    ) -> List[ChunkResult]:
        """Lọc bỏ các chunk quá ngắn (noise)."""
        return [c for c in chunks if len(c.content.strip()) >= min_chars]

    @staticmethod
    def _make_text_chunk(
        content: str,
        start_char: int,
        end_char: int,
        *,
        page_number: int | None = None,
        section_title: str | None = None,
        heading_level: int | None = None,
    ) -> ChunkResult:
        return ChunkResult(
            content=content,
            content_type="text",
            page_number=page_number,
            start_char=start_char,
            end_char=end_char,
            section_title=section_title,
            heading_level=heading_level,
        )

    @staticmethod
    def _make_ocr_chunk(
        content: str,
        *,
        page_number: int | None = None,
        image_index: int | None = None,
        ocr_confidence: float | None = None,
        section_title: str | None = None,
    ) -> ChunkResult:
        return ChunkResult(
            content=content,
            content_type="ocr",
            page_number=page_number,
            image_index=image_index,
            ocr_confidence=ocr_confidence,
            ocr_engine="rapidocr",
            section_title=section_title,
        )

    @staticmethod
    def _make_table_chunk(
        content: str,
        *,
        section_title: str | None = None,
        page_number: int | None = None,
    ) -> ChunkResult:
        return ChunkResult(
            content=content,
            content_type="table",
            is_table=True,
            section_title=section_title,
            page_number=page_number,
        )
