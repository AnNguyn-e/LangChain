"""
Document Processing Pipeline
─────────────────────────────
Luồng xử lý:
  File → Load → Clean → Chunk (text + OCR riêng biệt)
       → Persist Chunks vào SQL
       → Batch Embed → Persist Embeddings vào SQL + ChromaDB
"""

from __future__ import annotations

import io
import json
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.model.document_chunk_model import DocumentChunk, DocumentChunkMetadata
from app.model.document_embedding_model import DocumentEmbedding, DocumentEmbeddingMetadata
from app.model.document_model import Document

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
CHUNK_SIZE        = 1000   # characters
CHUNK_OVERLAP     = 150
MIN_CHUNK_CHARS   = 30     # chunks shorter than this are discarded (noise)
OCR_MIN_CONF      = 0.40   # OCR confidence threshold; below = noise
IMAGE_MAX_DIM     = 2048   # max width/height for OCR preprocessing (pixels)
IMAGE_OCR_DPI     = 300    # target DPI when rasterising PDF pages to image
EMBED_BATCH_SIZE  = 32     # number of chunks per embedding batch
MAX_WORKERS       = 4      # parallel threads for page processing

CHROMA_DB_DIR       = "chroma_db"
EMBED_MODEL_NAME    = "all-MiniLM-L6-v2"
EMBED_COLLECTION    = "documents"

os.makedirs(CHROMA_DB_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data Model
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. Text Cleaner
# ─────────────────────────────────────────────────────────────────────────────
class TextCleaner:
    """Làm sạch văn bản: loại ký tự rác, sửa ligature, chuẩn hóa whitespace."""

    _LIGATURES = {
        "\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff",
        "\ufb03": "ffi", "\ufb04": "ffl", "\ufb05": "ft", "\ufb06": "st",
    }

    # Ký tự điều khiển (trừ \n \t)
    _CTRL_RE   = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    # Nhiều dòng trống liên tiếp → tối đa 2
    _BLANK_RE  = re.compile(r"\n{3,}")
    # Khoảng trắng đầu/cuối dòng
    _TRAIL_RE  = re.compile(r"[ \t]+$", re.MULTILINE)
    # Dấu gạch nối cuối dòng (hyphenation) → nối lại
    _HYPH_RE   = re.compile(r"(\w)-\n(\w)")

    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ""
        # 1. Sửa ligature
        for lig, rep in cls._LIGATURES.items():
            text = text.replace(lig, rep)
        # 2. Loại ký tự điều khiển
        text = cls._CTRL_RE.sub("", text)
        # 3. Nối lại từ bị hyphen cuối dòng
        text = cls._HYPH_RE.sub(r"\1\2", text)
        # 4. Xóa khoảng trắng cuối dòng
        text = cls._TRAIL_RE.sub("", text)
        # 5. Rút gọn dòng trống thừa
        text = cls._BLANK_RE.sub("\n\n", text)
        return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Image Optimizer (trước OCR)
# ─────────────────────────────────────────────────────────────────────────────
class ImageOptimizer:
    """
    Tối ưu ảnh trước khi đưa vào OCR:
      Resize → Grayscale → Denoise → Otsu Binarization
    Giảm pixel thừa giúp RapidOCR nhanh hơn 2-3x và chính xác hơn.
    """

    @staticmethod
    def optimize(img: Image.Image) -> Image.Image:
        # 1. Resize: giới hạn chiều dài/rộng tối đa
        w, h = img.size
        if max(w, h) > IMAGE_MAX_DIM:
            scale = IMAGE_MAX_DIM / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # 2. Về grayscale
        img = img.convert("L")

        # 3. Nhẹ nhàng khử nhiễu
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # 4. Otsu Binarization qua numpy
        arr = np.array(img, dtype=np.uint8)
        # histogram
        hist, bins = np.histogram(arr.flatten(), 256, [0, 256])
        total = arr.size
        sum_total = np.dot(np.arange(256), hist)
        sum_b, w_b, max_var, threshold = 0.0, 0, 0.0, 128
        for t in range(256):
            w_b += hist[t]
            if w_b == 0:
                continue
            w_f = total - w_b
            if w_f == 0:
                break
            sum_b += t * hist[t]
            mean_b = sum_b / w_b
            mean_f = (sum_total - sum_b) / w_f
            var = w_b * w_f * (mean_b - mean_f) ** 2
            if var > max_var:
                max_var, threshold = var, t
        binarized = (arr > threshold).astype(np.uint8) * 255
        return Image.fromarray(binarized)

    @staticmethod
    def pil_to_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 3. OCR Helper
# ─────────────────────────────────────────────────────────────────────────────
def _run_ocr(img: Image.Image) -> Tuple[str, float]:
    """
    Chạy RapidOCR trên PIL Image đã tối ưu.
    Trả về (text, mean_confidence).
    """
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    optimized = ImageOptimizer.optimize(img)
    img_bytes = ImageOptimizer.pil_to_bytes(optimized)
    result, _ = ocr(img_bytes)
    if not result:
        return "", 0.0
    texts  = [item[1] for item in result]
    scores = [float(item[2]) if len(item) > 2 else 1.0 for item in result]
    return "\n".join(texts), (sum(scores) / len(scores) if scores else 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Text Splitter
# ─────────────────────────────────────────────────────────────────────────────
def _split_text(text: str) -> List[Tuple[str, int, int]]:
    """
    Tách text thành chunks theo RecursiveCharacterTextSplitter (tự implement nhẹ).
    Trả về list of (chunk_text, start_char, end_char).
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks_with_index = splitter.create_documents([text])
    results = []
    cursor = 0
    for c in chunks_with_index:
        start = text.find(c.page_content, cursor)
        if start == -1:
            start = cursor
        end = start + len(c.page_content)
        results.append((c.page_content, start, end))
        cursor = max(cursor, end - CHUNK_OVERLAP)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 5. Page Processor  (chạy parallel)
# ─────────────────────────────────────────────────────────────────────────────
def _process_pdf_page(page, page_num: int) -> List[ChunkResult]:
    """
    Xử lý một trang PDF:
      - Extract text → clean → split thành text chunks
      - Extract embedded images → OCR → tạo OCR chunks
    """
    results: List[ChunkResult] = []
    cleaner = TextCleaner()

    # --- Text ---
    raw_text = page.extract_text() or ""
    clean = cleaner.clean(raw_text)
    if len(clean) >= MIN_CHUNK_CHARS:
        for chunk_text, s, e in _split_text(clean):
            if len(chunk_text.strip()) >= MIN_CHUNK_CHARS:
                results.append(ChunkResult(
                    content=chunk_text,
                    content_type="text",
                    page_number=page_num,
                    start_char=s,
                    end_char=e,
                ))

    # --- Embedded images → OCR ---
    if hasattr(page, "images"):
        for img_idx, img_obj in enumerate(page.images):
            try:
                img_data = img_obj.get("data", None) or img_obj.get("stream", b"")
                if not img_data:
                    continue
                pil_img = Image.open(io.BytesIO(img_data))
                ocr_text, conf = _run_ocr(pil_img)
                ocr_clean = cleaner.clean(ocr_text)
                if len(ocr_clean.strip()) < MIN_CHUNK_CHARS or conf < OCR_MIN_CONF:
                    continue
                results.append(ChunkResult(
                    content=ocr_clean,
                    content_type="ocr",
                    page_number=page_num,
                    image_index=img_idx,
                    ocr_confidence=round(conf, 4),
                    ocr_engine="rapidocr",
                ))
            except Exception:
                pass

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 6. Document Processor (entry point)
# ─────────────────────────────────────────────────────────────────────────────
class DocumentProcessor:
    """Phân loại file và chạy pipeline xử lý phù hợp."""

    def process(self, file_path: str) -> List[ChunkResult]:
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        dispatch = {
            "pdf":  self._process_pdf,
            "docx": self._process_docx,
            "doc":  self._process_docx,
            "txt":  self._process_txt,
            "html": self._process_html,
            "htm":  self._process_html,
            "csv":  self._process_csv,
            "xlsx": self._process_excel,
            "xls":  self._process_excel,
            "pptx": self._process_pptx,
            "ppt":  self._process_pptx,
            "md":   self._process_markdown,
            "json": self._process_json,
            "png":  self._process_image,
            "jpg":  self._process_image,
            "jpeg": self._process_image,
            "bmp":  self._process_image,
            "tiff": self._process_image,
            "webp": self._process_image,
        }
        handler = dispatch.get(ext, self._process_txt)  # fallback: txt
        return handler(file_path)

    # ── PDF ──────────────────────────────────────────────────
    def _process_pdf(self, file_path: str) -> List[ChunkResult]:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages  = reader.pages

        all_chunks: List[ChunkResult] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {
                ex.submit(_process_pdf_page, page, i): i
                for i, page in enumerate(pages)
            }
            page_results = {}
            for fut in as_completed(futures):
                page_num = futures[fut]
                try:
                    page_results[page_num] = fut.result()
                except Exception:
                    page_results[page_num] = []

        # Ghép lại theo thứ tự trang
        for i in sorted(page_results):
            all_chunks.extend(page_results[i])

        return all_chunks

    # ── DOCX ─────────────────────────────────────────────────
    def _process_docx(self, file_path: str) -> List[ChunkResult]:
        import docx as python_docx  # python-docx package
        doc = python_docx.Document(file_path)
        cleaner = TextCleaner()

        full_text = "\n\n".join(
            p.text for p in doc.paragraphs if p.text.strip()
        )
        clean = cleaner.clean(full_text)
        chunks: List[ChunkResult] = []
        for chunk_text, s, e in _split_text(clean):
            if len(chunk_text.strip()) >= MIN_CHUNK_CHARS:
                chunks.append(ChunkResult(
                    content=chunk_text,
                    content_type="text",
                    start_char=s,
                    end_char=e,
                ))

        # Embedded images trong DOCX
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                try:
                    img_bytes = rel.target_part.blob
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    ocr_text, conf = _run_ocr(pil_img)
                    ocr_clean = cleaner.clean(ocr_text)
                    if len(ocr_clean.strip()) >= MIN_CHUNK_CHARS and conf >= OCR_MIN_CONF:
                        chunks.append(ChunkResult(
                            content=ocr_clean,
                            content_type="ocr",
                            ocr_confidence=round(conf, 4),
                            ocr_engine="rapidocr",
                        ))
                except Exception:
                    pass

        return chunks

    # ── TXT ──────────────────────────────────────────────────
    def _process_txt(self, file_path: str) -> List[ChunkResult]:
        cleaner = TextCleaner()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        clean = cleaner.clean(raw)
        return [
            ChunkResult(content=t, content_type="text", start_char=s, end_char=e)
            for t, s, e in _split_text(clean)
            if len(t.strip()) >= MIN_CHUNK_CHARS
        ]

    # ── Image ─────────────────────────────────────────────────
    def _process_image(self, file_path: str) -> List[ChunkResult]:
        cleaner = TextCleaner()
        pil_img = Image.open(file_path)
        ocr_text, conf = _run_ocr(pil_img)
        clean = cleaner.clean(ocr_text)
        if len(clean.strip()) < MIN_CHUNK_CHARS or conf < OCR_MIN_CONF:
            return []
        return [ChunkResult(
            content=clean,
            content_type="ocr",
            page_number=0,
            image_index=0,
            ocr_confidence=round(conf, 4),
            ocr_engine="rapidocr",
        )]

    # ── HTML ──────────────────────────────────────────────────
    def _process_html(self, file_path: str) -> List[ChunkResult]:
        """
        Parse HTML → xóa tag → lấy text thuần.
        Dùng BeautifulSoup (đã có trong langchain-community deps).
        """
        from bs4 import BeautifulSoup
        cleaner = TextCleaner()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        soup = BeautifulSoup(raw, "html.parser")
        # Loại bỏ script, style, head
        for tag in soup(["script", "style", "head", "meta", "link"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        clean = cleaner.clean(text)
        return [
            ChunkResult(content=t, content_type="text", start_char=s, end_char=e)
            for t, s, e in _split_text(clean)
            if len(t.strip()) >= MIN_CHUNK_CHARS
        ]

    # ── CSV ───────────────────────────────────────────────────
    def _process_csv(self, file_path: str) -> List[ChunkResult]:
        """
        Đọc CSV bằng pandas.
        Mỗi hàng được chuyển thành dạng text: "col1: val1 | col2: val2 | ..."
        Nhóm CSV_ROWS_PER_CHUNK hàng thành 1 chunk.
        """
        import pandas as pd
        CSV_ROWS_PER_CHUNK = 20
        try:
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, dtype=str, encoding="latin-1")

        df = df.fillna("").astype(str)
        cols = list(df.columns)
        rows_text = [
            " | ".join(f"{col}: {row[col]}" for col in cols)
            for _, row in df.iterrows()
        ]

        chunks: List[ChunkResult] = []
        for i in range(0, len(rows_text), CSV_ROWS_PER_CHUNK):
            batch = rows_text[i: i + CSV_ROWS_PER_CHUNK]
            content = "\n".join(batch)
            if len(content.strip()) >= MIN_CHUNK_CHARS:
                chunks.append(ChunkResult(
                    content=content,
                    content_type="table",
                    is_table=True,
                    section_title=f"Rows {i + 1}–{i + len(batch)}",
                ))
        return chunks

    # ── Excel ─────────────────────────────────────────────────
    def _process_excel(self, file_path: str) -> List[ChunkResult]:
        """
        Đọc tất cả sheets trong Excel.
        Mỗi sheet xử lý như CSV (nhóm hàng thành chunks, content_type=table).
        """
        import pandas as pd
        EXCEL_ROWS_PER_CHUNK = 20
        ext = os.path.splitext(file_path)[1].lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"
        xls = pd.ExcelFile(file_path, engine=engine)

        chunks: List[ChunkResult] = []
        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name, dtype=str).fillna("").astype(str)
            cols = list(df.columns)
            rows_text = [
                " | ".join(f"{col}: {row[col]}" for col in cols)
                for _, row in df.iterrows()
            ]
            for i in range(0, len(rows_text), EXCEL_ROWS_PER_CHUNK):
                batch = rows_text[i: i + EXCEL_ROWS_PER_CHUNK]
                content = "\n".join(batch)
                if len(content.strip()) >= MIN_CHUNK_CHARS:
                    chunks.append(ChunkResult(
                        content=content,
                        content_type="table",
                        is_table=True,
                        section_title=f"{sheet_name} | Rows {i + 1}–{i + len(batch)}",
                    ))
        return chunks

    # ── PowerPoint ────────────────────────────────────────────
    def _process_pptx(self, file_path: str) -> List[ChunkResult]:
        """
        Đọc từng slide trong PPTX:
          - Extract text từ TextFrame
          - Extract ảnh nhúng → OCR
        """
        from pptx import Presentation
        from pptx.util import Pt
        cleaner = TextCleaner()
        prs = Presentation(file_path)
        chunks: List[ChunkResult] = []

        for slide_num, slide in enumerate(prs.slides, start=1):
            slide_texts = []
            for shape in slide.shapes:
                # Text
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        line = " ".join(run.text for run in para.runs).strip()
                        if line:
                            slide_texts.append(line)
                # Embedded image → OCR
                if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                    try:
                        img_bytes = shape.image.blob
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        ocr_text, conf = _run_ocr(pil_img)
                        ocr_clean = cleaner.clean(ocr_text)
                        if len(ocr_clean.strip()) >= MIN_CHUNK_CHARS and conf >= OCR_MIN_CONF:
                            chunks.append(ChunkResult(
                                content=ocr_clean,
                                content_type="ocr",
                                page_number=slide_num,
                                ocr_confidence=round(conf, 4),
                                ocr_engine="rapidocr",
                                section_title=f"Slide {slide_num} (image)",
                            ))
                    except Exception:
                        pass

            if slide_texts:
                combined = cleaner.clean("\n".join(slide_texts))
                for t, s, e in _split_text(combined):
                    if len(t.strip()) >= MIN_CHUNK_CHARS:
                        chunks.append(ChunkResult(
                            content=t,
                            content_type="text",
                            page_number=slide_num,
                            start_char=s,
                            end_char=e,
                            section_title=f"Slide {slide_num}",
                        ))
        return chunks

    # ── Markdown ──────────────────────────────────────────────
    def _process_markdown(self, file_path: str) -> List[ChunkResult]:
        """
        Parse Markdown → loại bỏ cú pháp Markdown → text thuần.
        Dùng regex nhẹ, không cần convert sang HTML.
        """
        cleaner = TextCleaner()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        # Xóa code blocks
        raw = re.sub(r"```[\s\S]*?```", "", raw)
        raw = re.sub(r"`[^`]+`", "", raw)
        # Xóa links/images: ![alt](url) và [text](url)
        raw = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw)
        raw = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("]")[0][1:], raw)
        # Xóa heading ký hiệu # nhưng giữ text
        raw = re.sub(r"^#{1,6}\s*", "", raw, flags=re.MULTILINE)
        # Xóa bold/italic
        raw = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", raw)
        # Xóa bullet points
        raw = re.sub(r"^[\-*+]\s+", "", raw, flags=re.MULTILINE)
        clean = cleaner.clean(raw)
        return [
            ChunkResult(content=t, content_type="text", start_char=s, end_char=e)
            for t, s, e in _split_text(clean)
            if len(t.strip()) >= MIN_CHUNK_CHARS
        ]

    # ── JSON ──────────────────────────────────────────────────
    def _process_json(self, file_path: str) -> List[ChunkResult]:
        """
        Đọc JSON → flatten thành text có cấu trúc dạng "key: value".
        Với list of objects (records), xử lý như CSV.
        """
        import json as _json
        cleaner = TextCleaner()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                data = _json.load(f)
            except Exception:
                # Nếu không parse được, xử lý như TXT
                f.seek(0)
                return self._process_txt(file_path)

        def _flatten(obj, prefix="") -> str:
            lines = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = f"{prefix}.{k}" if prefix else k
                    lines.append(_flatten(v, key))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    lines.append(_flatten(item, f"{prefix}[{i}]"))
            else:
                lines.append(f"{prefix}: {obj}")
            return "\n".join(lines)

        text = _flatten(data)
        clean = cleaner.clean(text)
        return [
            ChunkResult(content=t, content_type="text", start_char=s, end_char=e)
            for t, s, e in _split_text(clean)
            if len(t.strip()) >= MIN_CHUNK_CHARS
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Chunk Persister
# ─────────────────────────────────────────────────────────────────────────────
class ChunkPersister:
    """Lưu danh sách ChunkResult vào SQL (document_chunks + document_chunk_metadata)."""

    @staticmethod
    def save(chunks: List[ChunkResult], document_id: int, db: Session) -> List[DocumentChunk]:
        db_chunks: List[DocumentChunk] = []
        for idx, c in enumerate(chunks):
            chunk_obj = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=c.content,
                token_count=len(c.content.split()),
            )
            db.add(chunk_obj)
            db.flush()  # lấy chunk_obj.id ngay

            meta = DocumentChunkMetadata(
                chunk_id=chunk_obj.id,
                page_number=c.page_number,
                page_number_end=c.page_number_end,
                start_char=c.start_char,
                end_char=c.end_char,
                section_title=c.section_title,
                heading_level=c.heading_level,
                is_table=str(c.is_table).lower(),
                is_header_footer=str(c.is_header_footer).lower(),
                chunk_strategy=c.chunk_strategy,
                chunk_size=c.chunk_size,
                chunk_overlap=c.chunk_overlap,
                content_type=c.content_type,
                image_index=c.image_index,
                ocr_confidence=c.ocr_confidence,
                ocr_engine=c.ocr_engine,
            )
            db.add(meta)
            db_chunks.append(chunk_obj)

        db.commit()
        for ch in db_chunks:
            db.refresh(ch)
        return db_chunks


# ─────────────────────────────────────────────────────────────────────────────
# 8. Chunk Embedder (Batch)
# ─────────────────────────────────────────────────────────────────────────────
class ChunkEmbedder:
    """
    Embed chunks theo batch và lưu vào:
      - ChromaDB (vector search)
      - document_embeddings + document_embedding_metadata (SQL)
    """

    def __init__(self):
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        self._embed_fn = HuggingFaceEmbeddings(model_name=EMBED_MODEL_NAME)
        self._vectorstore = Chroma(
            collection_name=EMBED_COLLECTION,
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self._embed_fn,
        )
        self._model_name   = EMBED_MODEL_NAME
        self._vector_dim   = 384  # all-MiniLM-L6-v2

    def embed_all(
        self,
        db_chunks: List[DocumentChunk],
        document_id: int,
        user_id: int,
        doc_metadata: Optional[dict],
        db: Session,
    ) -> int:
        """
        Embed tất cả chunks theo batch, lưu vào Chroma + SQL.
        Trả về số chunks được embed thành công.
        """
        if not db_chunks:
            return 0

        doc_meta = doc_metadata or {}
        success  = 0

        # Chia batch
        batches = [
            db_chunks[i : i + EMBED_BATCH_SIZE]
            for i in range(0, len(db_chunks), EMBED_BATCH_SIZE)
        ]

        for batch in batches:
            texts      = [c.content for c in batch]
            chroma_ids = [str(uuid.uuid4()) for _ in batch]
            metadatas  = [
                {
                    "document_id": document_id,
                    "user_id":     user_id,
                    "chunk_index": c.chunk_index,
                    "content_type": (c.chunk_metadata.content_type if c.chunk_metadata else "text"),
                    "department":  doc_meta.get("department", ""),
                    "category":    doc_meta.get("category", ""),
                    "language":    doc_meta.get("language", ""),
                    "confidentiality": doc_meta.get("confidentiality", "internal"),
                }
                for c in batch
            ]

            try:
                self._vectorstore.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=chroma_ids,
                )
            except Exception as e:
                # Nếu batch lỗi, đánh dấu failed và tiếp tục
                for ch in batch:
                    emb = DocumentEmbedding(
                        chunk_id=ch.id,
                        collection_name=EMBED_COLLECTION,
                        model_name=self._model_name,
                        vector_dimension=self._vector_dim,
                        status="failed",
                        error_message=str(e),
                    )
                    db.add(emb)
                db.commit()
                continue

            # Lưu SQL cho từng chunk trong batch
            for ch, cid, meta in zip(batch, chroma_ids, metadatas):
                emb = DocumentEmbedding(
                    chunk_id=ch.id,
                    chroma_id=cid,
                    collection_name=EMBED_COLLECTION,
                    model_name=self._model_name,
                    vector_dimension=self._vector_dim,
                    status="completed",
                )
                db.add(emb)
                db.flush()

                emb_meta = DocumentEmbeddingMetadata(
                    embedding_id=emb.id,
                    document_id=document_id,
                    user_id=user_id,
                    department=meta.get("department"),
                    category=meta.get("category"),
                    language=meta.get("language"),
                    confidentiality=meta.get("confidentiality"),
                    chroma_payload=json.dumps(meta, ensure_ascii=False),
                )
                db.add(emb_meta)
                success += 1

            db.commit()

        return success


# ─────────────────────────────────────────────────────────────────────────────
# 9. Master Pipeline (chạy trong background task)
# ─────────────────────────────────────────────────────────────────────────────
def run_processing_pipeline(document_id: int, file_path: str, user_id: int):
    """
    Hàm entry point cho BackgroundTask.
    Tạo DB session riêng (vì chạy ngoài request context).
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # 1. Load + Clean + Chunk
        processor = DocumentProcessor()
        chunks    = processor.process(file_path)

        if not chunks:
            doc.status        = "failed"
            doc.error_message = "Không trích xuất được nội dung từ tài liệu"
            db.commit()
            return

        # 2. Lưu chunks vào SQL
        persister  = ChunkPersister()
        db_chunks  = persister.save(chunks, document_id, db)

        # 3. Lấy doc_metadata để denormalize vào embedding
        doc_meta_obj = doc.doc_metadata
        doc_meta_dict = {}
        if doc_meta_obj:
            doc_meta_dict = {
                "department":    doc_meta_obj.department,
                "category":      doc_meta_obj.category,
                "language":      doc_meta_obj.language,
                "confidentiality": doc_meta_obj.confidentiality,
            }

        # 4. Embed + lưu vào Chroma & SQL
        embedder     = ChunkEmbedder()
        success_cnt  = embedder.embed_all(db_chunks, document_id, user_id, doc_meta_dict, db)

        # 5. Cập nhật trạng thái document
        doc.status      = "completed"
        doc.chunk_count = len(db_chunks)
        db.commit()

    except Exception as e:
        db.rollback()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status        = "failed"
                doc.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
