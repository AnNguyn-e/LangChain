"""
app/processors/__init__.py
──────────────────────────────────────────────────────────────
Registry & Factory cho toàn bộ file processors.

Cách dùng:
    from app.processors import get_processor, SUPPORTED_EXTENSIONS

    processor = get_processor("report.pdf")
    chunks = processor.process("/uploads/report.pdf")

Thêm định dạng mới:
    1. Tạo class kế thừa BaseFileProcessor trong module riêng
    2. Đăng ký vào _REGISTRY bên dưới
    3. Không cần sửa gì thêm — factory tự nhận diện
"""

from __future__ import annotations

import os
from typing import Dict, Type

from app.processors.base import BaseFileProcessor

# ── Lazy imports (tránh load thư viện nặng khi không cần) ────────────────────
def _load_pdf():
    from app.processors.pdf_processor import PDFProcessor
    return PDFProcessor

def _load_docx():
    from app.processors.docx_processor import DOCXProcessor
    return DOCXProcessor

def _load_txt():
    from app.processors.txt_processor import TXTProcessor
    return TXTProcessor

def _load_image():
    from app.processors.image_processor import ImageProcessor
    return ImageProcessor

def _load_html():
    from app.processors.html_processor import HTMLProcessor
    return HTMLProcessor

def _load_csv():
    from app.processors.csv_processor import CSVProcessor
    return CSVProcessor

def _load_excel():
    from app.processors.excel_processor import ExcelProcessor
    return ExcelProcessor

def _load_pptx():
    from app.processors.pptx_processor import PPTXProcessor
    return PPTXProcessor

def _load_markdown():
    from app.processors.markdown_processor import MarkdownProcessor
    return MarkdownProcessor

def _load_json():
    from app.processors.json_processor import JSONProcessor
    return JSONProcessor


# ── Registry: ext → loader function ──────────────────────────────────────────
# Dùng loader thay vì import trực tiếp để tránh circular import
# và giảm thời gian startup khi chỉ dùng 1-2 loại processor.
_REGISTRY: Dict[str, callable] = {
    # PDF
    "pdf":      _load_pdf,

    # Word
    "docx":     _load_docx,
    "doc":      _load_docx,

    # Plain text & code
    "txt":      _load_txt,
    "log":      _load_txt,
    "yaml":     _load_txt,
    "yml":      _load_txt,
    "toml":     _load_txt,
    "ini":      _load_txt,
    "cfg":      _load_txt,
    "env":      _load_txt,

    # Images
    "png":      _load_image,
    "jpg":      _load_image,
    "jpeg":     _load_image,
    "bmp":      _load_image,
    "tiff":     _load_image,
    "tif":      _load_image,
    "webp":     _load_image,
    "gif":      _load_image,

    # Web
    "html":     _load_html,
    "htm":      _load_html,

    # Spreadsheet
    "csv":      _load_csv,
    "tsv":      _load_csv,
    "xlsx":     _load_excel,
    "xls":      _load_excel,

    # Presentation
    "pptx":     _load_pptx,
    "ppt":      _load_pptx,

    # Markup / Structured
    "md":       _load_markdown,
    "markdown": _load_markdown,
    "json":     _load_json,
    "jsonl":    _load_json,
}

# ── Public API ────────────────────────────────────────────────────────────────

#: Tập hợp tất cả extension được hỗ trợ (dùng để validate khi upload)
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(_REGISTRY.keys())


def get_processor(file_path: str) -> BaseFileProcessor:
    """
    Factory: trả về processor phù hợp với extension của file.

    Args:
        file_path: Tên file hoặc đường dẫn đầy đủ.

    Returns:
        Instance của processor tương ứng.

    Raises:
        ValueError: Nếu extension không được hỗ trợ.

    Example:
        >>> proc = get_processor("contract.pdf")
        >>> chunks = proc.process("/data/uploads/contract.pdf")
    """
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    loader = _REGISTRY.get(ext)

    if loader is None:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Không hỗ trợ định dạng '.{ext}'. "
            f"Các định dạng được hỗ trợ: {supported}"
        )

    processor_class: Type[BaseFileProcessor] = loader()
    return processor_class()


def is_supported(file_path: str) -> bool:
    """Kiểm tra nhanh xem extension có được hỗ trợ không."""
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    return ext in SUPPORTED_EXTENSIONS


__all__ = [
    "get_processor",
    "is_supported",
    "SUPPORTED_EXTENSIONS",
    "BaseFileProcessor",
]
