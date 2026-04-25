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
from app.processors.constants import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBED_BATCH_SIZE, CHROMA_DB_DIR, 
    EMBED_MODEL_NAME, EMBED_COLLECTION
)

os.makedirs(CHROMA_DB_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data Model
# ─────────────────────────────────────────────────────────────────────────────
from app.processors.base import ChunkResult, TextCleaner, ImageOptimizer, run_ocr


# ─────────────────────────────────────────────────────────────────────────────
# 4. Document Processor  (entry point — delegate to processors package)
# ─────────────────────────────────────────────────────────────────────────────
class DocumentProcessor:
    """
    Thin dispatcher: nhận file_path → gọi processor phù hợp từ
    app.processors (PDFProcessor, DOCXProcessor, ...).

    Toàn bộ logic xử lý từng định dạng đã được chuyển sang
    app/processors/<format>_processor.py để dễ bảo trì và mở rộng.
    """

    def process(self, file_path: str) -> List[ChunkResult]:
        from app.processors import get_processor  # noqa: PLC0415
        processor = get_processor(file_path)
        return processor.process(file_path)


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
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        from app.processors.constants import LM_STUDIO_BASE_URL
        
        self._embed_fn = OpenAIEmbeddings(
            base_url=LM_STUDIO_BASE_URL,
            api_key="lm-studio",
            check_embedding_ctx_length=False
        )
        self._vectorstore = Chroma(
            collection_name=EMBED_COLLECTION,
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self._embed_fn,
        )
        self._model_name   = EMBED_MODEL_NAME
        self._vector_dim   = 0  # Dynamic based on LMStudio model

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
