"""
ImageOptimizer  +  OCR helper
──────────────────────────────────────────────────────────────
Pipeline tối ưu ảnh trước OCR:
  Resize → Grayscale → Median Denoise → Otsu Binarization

OCR sử dụng RapidOCR (rapidocr-onnxruntime) — singleton per thread.
"""

from __future__ import annotations

import io
import threading
from typing import Tuple

import numpy as np
from PIL import Image, ImageFilter

# ── Constants (override từ config nếu cần) ───────────────────────────────────
IMAGE_MAX_DIM: int = 2048   # pixels – chiều dài/rộng tối đa trước OCR
OCR_MIN_CONF: float = 0.40  # ngưỡng confidence tối thiểu


# ── Singleton OCR engine (thread-local để tránh GIL conflict) ────────────────
_tls = threading.local()


def _get_ocr_engine():
    """Trả về RapidOCR instance theo thread (lazy init)."""
    if not getattr(_tls, "ocr", None):
        from rapidocr_onnxruntime import RapidOCR  # noqa: PLC0415
        _tls.ocr = RapidOCR()
    return _tls.ocr


# ── ImageOptimizer ────────────────────────────────────────────────────────────
class ImageOptimizer:
    """
    Tối ưu ảnh PIL trước khi đưa vào OCR.

    Các bước:
      1. Resize   – giới hạn kích thước tối đa (IMAGE_MAX_DIM)
      2. Grayscale – chuyển về L mode
      3. Denoise  – Median Filter 3×3
      4. Otsu     – binarize tăng tương phản text

    Kết quả: ảnh PNG bytes sẵn cho RapidOCR.
    """

    @staticmethod
    def optimize(img: Image.Image) -> Image.Image:
        """Trả về PIL Image đã qua resize + grayscale + denoise + binarize."""

        # ── 1. Resize ────────────────────────────────────────────
        w, h = img.size
        if max(w, h) > IMAGE_MAX_DIM:
            scale = IMAGE_MAX_DIM / max(w, h)
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.LANCZOS,
            )

        # ── 2. Chuyển về grayscale ───────────────────────────────
        img = img.convert("L")

        # ── 3. Khử nhiễu nhẹ ────────────────────────────────────
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # ── 4. Otsu Binarization ──────────────────────────────────
        arr = np.array(img, dtype=np.uint8)
        hist, _ = np.histogram(arr.flatten(), bins=256, range=(0, 256))
        total = arr.size
        sum_total = float(np.dot(np.arange(256, dtype=np.float64), hist))

        sum_b, w_b, max_var, threshold = 0.0, 0, 0.0, 128
        for t in range(256):
            w_b += int(hist[t])
            if w_b == 0:
                continue
            w_f = total - w_b
            if w_f == 0:
                break
            sum_b += t * int(hist[t])
            mean_b = sum_b / w_b
            mean_f = (sum_total - sum_b) / w_f
            var = w_b * w_f * (mean_b - mean_f) ** 2
            if var > max_var:
                max_var, threshold = var, t

        binarized = (arr > threshold).astype(np.uint8) * 255
        return Image.fromarray(binarized)

    @staticmethod
    def pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
        """Chuyển PIL Image → bytes ở định dạng cho trước."""
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    @classmethod
    def prepare_for_ocr(cls, img: Image.Image) -> bytes:
        """Shortcut: optimize rồi chuyển sang bytes PNG."""
        return cls.pil_to_bytes(cls.optimize(img))


# ── Public OCR helper ─────────────────────────────────────────────────────────
def run_ocr(img: Image.Image) -> Tuple[str, float]:
    """
    Chạy RapidOCR trên một PIL Image.

    Trả về:
        text (str)       – văn bản nhận diện được
        confidence (float) – mean confidence score (0.0–1.0)
                            0.0 nếu không nhận diện được gì.
    """
    try:
        ocr = _get_ocr_engine()
        img_bytes = ImageOptimizer.prepare_for_ocr(img)
        result, _ = ocr(img_bytes)

        if not result:
            return "", 0.0

        texts  = [row[1] for row in result]
        scores = [float(row[2]) if len(row) > 2 else 1.0 for row in result]
        mean_conf = sum(scores) / len(scores) if scores else 0.0

        return "\n".join(texts), round(mean_conf, 4)

    except Exception:
        return "", 0.0
