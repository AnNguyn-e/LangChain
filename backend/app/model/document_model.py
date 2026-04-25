from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base
from app.model.tag_model import document_tags


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)   # Bytes
    file_type = Column(String, nullable=True)
    file_hash = Column(String, index=True, nullable=True)  

    user_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, default="processing")
    # processing | completed | failed

    chunk_count = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="documents")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")
    doc_metadata = relationship(
        "DocumentMetadata",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan"
    )
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )