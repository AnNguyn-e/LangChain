"""
Text Splitter
──────────────────────────────────────────────────────────────
Chia văn bản thành chunks bằng RecursiveCharacterTextSplitter
và trả về cả vị trí (start_char, end_char) của mỗi chunk
trong văn bản gốc — cần thiết để lưu metadata.
"""

from __future__ import annotations

from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.processors.constants import CHUNK_SIZE, CHUNK_OVERLAP


# Separator ưu tiên theo ngữ nghĩa (đoạn > dòng > câu > từ > ký tự)
_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]


def split_text(text: str) -> List[Tuple[str, int, int]]:
    """
    Tách ``text`` thành danh sách (chunk_text, start_char, end_char).

    Args:
        text: Văn bản đã làm sạch.

    Returns:
        List các tuple (nội_dung_chunk, vị_trí_bắt_đầu, vị_trí_kết_thúc).
        Danh sách rỗng nếu text trống.
    """
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

    docs = splitter.create_documents([text])
    results: List[Tuple[str, int, int]] = []
    cursor = 0

    for doc in docs:
        content = doc.page_content
        start = text.find(content, cursor)
        if start == -1:
            # Fallback: tìm lại từ đầu (trường hợp chunk overlap phức tạp)
            start = text.find(content)
        if start == -1:
            start = cursor
        end = start + len(content)
        results.append((content, start, end))
        # Lùi cursor đúng CHUNK_OVERLAP để chunk tiếp theo overlap chính xác
        cursor = max(cursor, end - CHUNK_OVERLAP)

    return results


def split_text_by_sections(
    sections: List[Tuple[str, str | None]],
) -> List[Tuple[str, int, int, str | None]]:
    """
    Tách từng section (text, title) và trả về
    (chunk_text, start_char, end_char, section_title).

    Dành cho tài liệu có cấu trúc rõ (DOCX, Markdown có heading).
    """
    results = []
    for text, title in sections:
        for chunk, s, e in split_text(text):
            results.append((chunk, s, e, title))
    return results
