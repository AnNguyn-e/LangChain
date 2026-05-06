from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database.database import Base

class RoleEnum(str, enum.Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER, nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    documents = relationship("Document", back_populates="owner")
    chats = relationship("Chat", back_populates="user")
