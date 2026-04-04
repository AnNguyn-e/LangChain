from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models import RoleEnum

# User Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum

    class Config:
        orm_mode = True
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    upload_time: datetime

    class Config:
        orm_mode = True
        from_attributes = True

# Chat Schemas
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
