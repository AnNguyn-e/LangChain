from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class DocumentEmbedding(Base):
    """
    Lưu thông tin embedding vector của một chunk.
    Bản thân vector được lưu trong ChromaDB; bảng này lưu metadata/liên kết.
    Quan hệ 1-1 với DocumentChunk; 1-1 với DocumentEmbeddingMetadata.
    """
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(
        Integer,
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # ── Liên kết với vector store ────────────────────────────
    chroma_id = Column(String, unique=True, nullable=True, index=True)
    # ID của vector trong ChromaDB collection

    collection_name = Column(String, nullable=True)    # Tên ChromaDB collection

    # ── Thông tin embedding ──────────────────────────────────
    model_name = Column(String, nullable=True)         # Tên model embedding, e.g. "text-embedding-3-small"
    model_version = Column(String, nullable=True)      # Phiên bản model
    vector_dimension = Column(Integer, nullable=True)  # Số chiều của vector
    embedding_norm = Column(Float, nullable=True)      # L2 norm của vector (dùng để debug)

    status = Column(String, default="pending")
    # pending | completed | failed

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunk = relationship("DocumentChunk", back_populates="embedding")
    embedding_metadata = relationship(
        "DocumentEmbeddingMetadata",
        back_populates="embedding",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DocumentEmbeddingMetadata(Base):
    """
    Metadata bổ sung cho embedding — ngữ cảnh giúp RAG filter/re-rank hiệu quả hơn.
    Quan hệ 1-1 với DocumentEmbedding.
    """
    __tablename__ = "document_embedding_metadata"

    id = Column(Integer, primary_key=True, index=True)
    embedding_id = Column(
        Integer,
        ForeignKey("document_embeddings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # ── Ngữ cảnh tài liệu (denormalized để tăng tốc query/filter) ──
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department = Column(String, nullable=True)         # Copy từ DocumentMetadata để filter nhanh
    category = Column(String, nullable=True)           # Copy từ DocumentMetadata
    language = Column(String, nullable=True)           # Ngôn ngữ của chunk
    confidentiality = Column(String, nullable=True)    # Mức bảo mật: public|internal|confidential

    # ── Chất lượng ──────────────────────────────────────────
    relevance_score = Column(Float, nullable=True)     # Score đánh giá chất lượng chunk (0-1)
    is_noise = Column(String, default="false")         # Chunk có bị coi là nhiễu không

    # ── ChromaDB payload (lưu lại những gì đã push vào chroma) ──
    chroma_payload = Column(Text, nullable=True)       # JSON string của metadata đẩy vào ChromaDB

    # ── Mở rộng ───────────────────────────────────────────────
    extra_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    embedding = relationship("DocumentEmbedding", back_populates="embedding_metadata")
