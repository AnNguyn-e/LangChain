"""
TextCleaner
──────────────────────────────────────────────────────────────
Làm sạch văn bản trích xuất từ nhiều loại tài liệu:
  1. Chuẩn hoá Unicode ligature (fi, fl, ff, ...)
  2. Loại ký tự điều khiển (giữ lại \\n, \\t)
  3. Nối lại từ bị hyphen cuối dòng (PDF raster artifact)
  4. Xoá khoảng trắng đầu/cuối mỗi dòng
  5. Rút gọn dòng trống thừa (tối đa 2 liên tiếp)
"""

import re
import unicodedata


class TextCleaner:
    """Tiện ích làm sạch văn bản — thread-safe (classmethod only)."""

    # ── Unicode ligature map ──────────────────────────────────────
    _LIGATURES: dict[str, str] = {
        "\ufb00": "ff",  "\ufb01": "fi",  "\ufb02": "fl",
        "\ufb03": "ffi", "\ufb04": "ffl", "\ufb05": "ft",
        "\ufb06": "st",
    }

    # ── Compiled regex ────────────────────────────────────────────
    # Ký tự điều khiển (trừ \n=0x0a, \t=0x09, \r=0x0d)
    _CTRL_RE  = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    # Dòng trống thừa → tối đa 2
    _BLANK_RE = re.compile(r"\n{3,}")
    # Khoảng trắng cuối dòng
    _TRAIL_RE = re.compile(r"[ \t]+$", re.MULTILINE)
    # Khoảng trắng đầu dòng (indent thừa)
    _LEAD_RE  = re.compile(r"^[ \t]+", re.MULTILINE)
    # Hyphenation cuối dòng: "exam-\nple" → "example"
    _HYPH_RE  = re.compile(r"(\w)-\n(\w)")
    # Nhiều space liên tiếp trên cùng dòng → 1 space
    _MULTI_SP = re.compile(r"[^\S\n]{2,}")
    # Ký tự soft-hyphen (U+00AD) — invisible nhưng gây lỗi search
    _SOFT_H   = re.compile(r"\u00ad")

    @classmethod
    def clean(cls, text: str) -> str:
        """Làm sạch và chuẩn hoá văn bản."""
        if not text:
            return ""

        # 1. Chuẩn hoá Unicode dạng NFC (tránh ký tự composed/decomposed lẫn lộn)
        text = unicodedata.normalize("NFC", text)

        # 2. Sửa ligature PDF
        for lig, rep in cls._LIGATURES.items():
            text = text.replace(lig, rep)

        # 3. Xoá soft-hyphen ẩn
        text = cls._SOFT_H.sub("", text)

        # 4. Loại ký tự điều khiển
        text = cls._CTRL_RE.sub("", text)

        # 5. Nối từ bị hyphen cuối dòng
        text = cls._HYPH_RE.sub(r"\1\2", text)

        # 6. Thu gọn nhiều khoảng trắng trên cùng dòng
        text = cls._MULTI_SP.sub(" ", text)

        # 7. Xoá khoảng trắng đầu/cuối dòng
        text = cls._TRAIL_RE.sub("", text)
        text = cls._LEAD_RE.sub("", text)

        # 8. Rút gọn dòng trống liên tiếp
        text = cls._BLANK_RE.sub("\n\n", text)

        return text.strip()

    @classmethod
    def clean_table_cell(cls, value: str) -> str:
        """Làm sạch nhẹ hơn cho ô trong bảng (giữ khoảng trắng đơn)."""
        if not value:
            return ""
        value = unicodedata.normalize("NFC", value)
        value = cls._CTRL_RE.sub("", value)
        value = cls._SOFT_H.sub("", value)
        return value.strip()
