"""
HTMLProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.html / *.htm:

  1. Parse HTML bằng BeautifulSoup (lxml parser nếu có, fallback html.parser)
  2. Loại bỏ: <script>, <style>, <head>, <noscript>, <iframe>, comment
  3. Giữ lại: <img alt="..."> → dùng alt text làm nội dung
  4. Giữ thứ tự semantic: heading → paragraph → list items
  5. Clean → split → trả về text chunks

Thư viện: beautifulsoup4 (bs4)
"""

from __future__ import annotations

import re
from typing import List

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS

# Tag loại bỏ hoàn toàn (kể cả nội dung bên trong)
_REMOVE_TAGS = [
    "script", "style", "noscript", "iframe",
    "head", "meta", "link", "svg", "canvas",
]

# Regex xoá nhiều dòng trống liên tiếp
_BLANK_RE = re.compile(r"\n{3,}")


class HTMLProcessor(BaseFileProcessor):
    """Processor cho file *.html / *.htm."""

    def process(self, file_path: str) -> List[ChunkResult]:
        from bs4 import BeautifulSoup, Comment  # noqa: PLC0415

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        # Chọn parser: ưu tiên lxml (nhanh hơn), fallback html.parser
        try:
            soup = BeautifulSoup(raw, "lxml")
        except Exception:
            soup = BeautifulSoup(raw, "html.parser")

        # ── Loại bỏ các tag không cần thiết ────────────────────────────────
        for tag in soup(_REMOVE_TAGS):
            tag.decompose()

        # Loại bỏ HTML comment
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()

        # ── Thay <img> bằng alt text (nếu có) ────────────────────────────
        for img in soup.find_all("img"):
            alt = (img.get("alt") or "").strip()
            if alt:
                img.replace_with(f"[Image: {alt}]")
            else:
                img.decompose()

        # ── Lấy text, dùng "\n" làm separator ────────────────────────────
        text = soup.get_text(separator="\n")
        text = _BLANK_RE.sub("\n\n", text)

        cleaner = TextCleaner()
        clean = cleaner.clean(text)

        return [
            self._make_text_chunk(content, s, e)
            for content, s, e in split_text(clean)
            if len(content.strip()) >= MIN_CHUNK_CHARS
        ]
