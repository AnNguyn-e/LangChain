from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, default="processing")  
    # processing | completed | failed

    chunk_count = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="documents")