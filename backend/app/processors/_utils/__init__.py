"""
app/processors/_utils
─────────────────────
Các tiện ích dùng chung cho tất cả processors:
  - TextCleaner    : làm sạch văn bản
  - ImageOptimizer : tối ưu ảnh trước OCR
  - run_ocr        : chạy RapidOCR
  - split_text     : tách chunks
"""

from app.processors._utils.text_cleaner import TextCleaner
from app.processors._utils.image_optimizer import ImageOptimizer, run_ocr
from app.processors._utils.text_splitter import split_text

__all__ = [
    "TextCleaner",
    "ImageOptimizer",
    "run_ocr",
    "split_text",
]
