from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="processed")
    upload_time = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")
