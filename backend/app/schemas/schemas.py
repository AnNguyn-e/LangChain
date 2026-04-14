import re
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.model.user_model import RoleEnum

# ─────────────────────────────────────────────
# User Schemas
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username phải có ít nhất 3 ký tự")
        if len(v) > 50:
            raise ValueError("Username không được vượt quá 50 ký tự")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username chỉ được chứa chữ cái, số và dấu gạch dưới (_)")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự")
        if len(v) > 128:
            raise ValueError("Mật khẩu không được vượt quá 128 ký tự")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError("Email không hợp lệ")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username phải có ít nhất 3 ký tự")
        if len(v) > 50:
            raise ValueError("Username không được vượt quá 50 ký tự")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username chỉ được chứa chữ cái, số và dấu gạch dưới (_)")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự")
        if len(v) > 128:
            raise ValueError("Mật khẩu không được vượt quá 128 ký tự")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError("Email không hợp lệ")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: RoleEnum

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Token Schemas
# ─────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshToken(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str
# ─────────────────────────────────────────────
# Tag Schemas
# ─────────────────────────────────────────────

class TagBase(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Document Metadata Schemas
# ─────────────────────────────────────────────

class DocumentMetadataResponse(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    keywords: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    summary: Optional[str] = None
    page_count: Optional[int] = None
    source_url: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Document Schemas
# ─────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Schema trả về thông tin tài liệu (dùng cho GET list)."""
    id: int
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    tags: List[TagResponse] = []
    doc_metadata: Optional[DocumentMetadataResponse] = None

    class Config:
        from_attributes = True


class UploadDocumentResponse(BaseModel):
    """Schema trả về sau khi upload + embed document thành công."""
    id: int
    filename: str
    status: str
    chunk_count: int
    created_at: datetime
    message: str

    class Config:
        from_attributes = True

class BulkUploadResponse(BaseModel):
    results: List[UploadDocumentResponse]
    errors: List[dict] # {filename: str, error: str}


# ─────────────────────────────────────────────
# Chat Schemas
# ─────────────────────────────────────────────

class ChatCreateRequest(BaseModel):
    query: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    question: str
    answer: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    # We optionally include chats
    chats: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
