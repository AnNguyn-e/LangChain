from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class DocumentChunk(Base):
    """
    Lưu từng đoạn văn bản (chunk) sau khi tài liệu được phân đoạn.
    Quan hệ nhiều-1 với Document; 1-1 với DocumentChunkMetadata.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index = Column(Integer, nullable=False)   # Thứ tự chunk trong tài liệu (0-based)
    content = Column(Text, nullable=False)           # Nội dung văn bản của chunk
    token_count = Column(Integer, nullable=True)     # Số token ước tính

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    chunk_metadata = relationship(
        "DocumentChunkMetadata",
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan"
    )
    embedding = relationship(
        "DocumentEmbedding",
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DocumentChunkMetadata(Base):
    """
    Metadata mô tả vị trí & ngữ cảnh của một chunk trong tài liệu gốc.
    Quan hệ 1-1 với DocumentChunk.
    """
    __tablename__ = "document_chunk_metadata"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(
        Integer,
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # ── Vị trí trong tài liệu ────────────────────────────────
    page_number = Column(Integer, nullable=True)       # Trang bắt đầu của chunk
    page_number_end = Column(Integer, nullable=True)   # Trang kết thúc (nếu chunk kéo dài)
    start_char = Column(Integer, nullable=True)        # Vị trí ký tự bắt đầu trong tài liệu gốc
    end_char = Column(Integer, nullable=True)          # Vị trí ký tự kết thúc

    # ── Cấu trúc ─────────────────────────────────────────────
    section_title = Column(String, nullable=True)      # Tiêu đề mục/phần chứa chunk
    heading_level = Column(Integer, nullable=True)     # Cấp heading (1, 2, 3...)
    is_table = Column(String, default="false")         # Chunk có phải bảng biểu không
    is_header_footer = Column(String, default="false") # Có phải header/footer không

    # ── Chunking strategy info ────────────────────────────────
    chunk_strategy = Column(String, nullable=True)     # "recursive", "sentence", "fixed", ...
    chunk_size = Column(Integer, nullable=True)        # Kích thước chunk (chars hoặc tokens)
    chunk_overlap = Column(Integer, nullable=True)     # Số ký tự/token chồng lấp

    # ── Loại nội dung ─────────────────────────────────────────
    content_type = Column(String, default="text")      # "text" | "ocr" | "table"
    image_index = Column(Integer, nullable=True)       # Thứ tự ảnh trong trang (chỉ khi content_type="ocr")
    ocr_confidence = Column(Float, nullable=True)      # Độ tin cậy OCR (0.0–1.0)
    ocr_engine = Column(String, nullable=True)         # Engine OCR dùng, e.g. "rapidocr"

    # ── Mở rộng ──────────────────────────────────────────────
    extra_data = Column(Text, nullable=True)           # JSON string cho trường mở rộng

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chunk = relationship("DocumentChunk", back_populates="chunk_metadata")