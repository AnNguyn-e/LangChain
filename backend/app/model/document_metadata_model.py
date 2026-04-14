from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class DocumentMetadata(Base):
    """
    Metadata mô tả của Document — do người dùng/hệ thống nhập hoặc trích xuất từ file.
    Quan hệ 1-1 với Document.
    """
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # ── Thông tin người dùng nhập ──────────────────────────────
    department = Column(String, nullable=True)        # Phòng ban sở hữu tài liệu
    uploaded_by_name = Column(String, nullable=True)  # Tên người upload (display)
    description = Column(Text, nullable=True)         # Mô tả ngắn do người dùng nhập
    category = Column(String, nullable=True)          # Phân loại: Báo cáo, Hợp đồng, ...
    version = Column(String, nullable=True)           # Phiên bản tài liệu, e.g. "v1.2"
    confidentiality = Column(String, default="internal")
    # public | internal | confidential | secret

    # ── Thông tin trích xuất từ file (PDF, DOCX, ...) ──────────
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    creator = Column(String, nullable=True)    # Phần mềm tạo file
    producer = Column(String, nullable=True)   # PDF producer
    keywords = Column(String, nullable=True)
    language = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)

    # ── Thông tin AI sinh ra ───────────────────────────────────
    summary = Column(Text, nullable=True)      # Tóm tắt do LLM sinh ra
    source_url = Column(String, nullable=True) # URL nguồn gốc nếu có

    # ── Mở rộng ───────────────────────────────────────────────
    extra_data = Column(Text, nullable=True)   # JSON string cho trường mở rộng

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="doc_metadata")
