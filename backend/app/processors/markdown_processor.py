"""
MarkdownProcessor
──────────────────────────────────────────────────────────────
Xử lý file *.md / *.markdown:

Chiến lược:
  1. Parse Markdown bằng mistune (nếu có) hoặc regex fallback
  2. Giữ thứ tự section (heading → paragraphs)
  3. Code block → giữ nội dung nhưng bỏ backtick
  4. Split theo section_title (từ heading)

Nếu mistune chưa cài: dùng regex cleaner đơn giản.

Thư viện: mistune (optional, tốt hơn), re (fallback)
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.processors.base import (
    BaseFileProcessor, TextCleaner,
    split_text, ChunkResult,
)
from app.processors.constants import MIN_CHUNK_CHARS

# ── Regex patterns ─────────────────────────────────────────────────────────
_HEADING_RE    = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```[\w]*\n?([\s\S]*?)```", re.MULTILINE)
_INLINE_CODE   = re.compile(r"`([^`]+)`")
_IMAGE_RE      = re.compile(r"!\[([^\]]*)\]\([^)]*\)")   # ![alt](url)
_LINK_RE       = re.compile(r"\[([^\]]+)\]\([^)]*\)")    # [text](url)
_BOLD_ITALIC   = re.compile(r"[*_]{1,3}([^*_\n]+)[*_]{1,3}")
_STRIKETHROUGH = re.compile(r"~~(.+?)~~")
_BULLET_RE     = re.compile(r"^[ \t]*[-*+]\s+", re.MULTILINE)
_ORDERED_RE    = re.compile(r"^[ \t]*\d+\.\s+", re.MULTILINE)
_BLOCKQUOTE_RE = re.compile(r"^>+\s?", re.MULTILINE)
_HR_RE         = re.compile(r"^[-*_]{3,}$", re.MULTILINE)
_HTML_TAG_RE   = re.compile(r"<[^>]+>")


class MarkdownProcessor(BaseFileProcessor):
    """Processor cho file *.md / *.markdown."""

    def process(self, file_path: str) -> List[ChunkResult]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        sections = self._split_by_headings(raw)
        cleaner = TextCleaner()
        chunks: List[ChunkResult] = []

        for section_text, heading, heading_lvl in sections:
            cleaned_raw = self._strip_markdown(section_text)
            clean = cleaner.clean(cleaned_raw)

            for content, s, e in split_text(clean):
                if len(content.strip()) >= MIN_CHUNK_CHARS:
                    chunks.append(self._make_text_chunk(
                        content, s, e,
                        section_title=heading,
                        heading_level=heading_lvl,
                    ))

        return self._filter_chunks(chunks)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _split_by_headings(text: str) -> List[Tuple[str, str | None, int | None]]:
        """
        Tách Markdown thành các section dựa theo heading.

        Trả về list (section_text, heading_title, heading_level).
        """
        sections: List[Tuple[str, str | None, int | None]] = []
        matches = list(_HEADING_RE.finditer(text))

        if not matches:
            return [(text, None, None)]

        # Phần text trước heading đầu tiên
        if matches[0].start() > 0:
            sections.append((text[:matches[0].start()], None, None))

        for i, m in enumerate(matches):
            level = len(m.group(1))
            title = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((text[start:end], title, level))

        return sections

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Loại bỏ cú pháp Markdown, giữ lại nội dung text."""
        # Code fence → giữ nội dung code (hữu ích để search)
        text = _CODE_FENCE_RE.sub(r"\1", text)
        # Inline code
        text = _INLINE_CODE.sub(r"\1", text)
        # Images → alt text
        text = _IMAGE_RE.sub(r"[Image: \1]", text)
        # Links → link text
        text = _LINK_RE.sub(r"\1", text)
        # Bold/Italic
        text = _BOLD_ITALIC.sub(r"\1", text)
        # Strikethrough
        text = _STRIKETHROUGH.sub(r"\1", text)
        # Blockquote markers
        text = _BLOCKQUOTE_RE.sub("", text)
        # Horizontal rule
        text = _HR_RE.sub("", text)
        # Bullet / ordered list markers
        text = _BULLET_RE.sub("", text)
        text = _ORDERED_RE.sub("", text)
        # HTML tags còn sót
        text = _HTML_TAG_RE.sub("", text)
        return text
