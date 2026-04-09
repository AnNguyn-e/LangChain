from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app.schemas import schemas
from app.database.database import get_db
from app.services import auth_service, document_service
from app.model.user_model import User

router = APIRouter(prefix="/documents", tags=["Documents"])


# ─────────────────────────────────────────────
# Upload Document
# ─────────────────────────────────────────────

@router.post("/upload", response_model=schemas.UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tải lên tài liệu và xử lý embedding.
    """
    return document_service.upload_document(file, current_user, db)


# ─────────────────────────────────────────────
# List Documents
# ─────────────────────────────────────────────

@router.get("/", response_model=List[schemas.DocumentResponse])
def get_documents(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tài liệu của người dùng hoặc tất cả nếu là Admin.
    """
    return document_service.get_all_documents(current_user, db)


# ─────────────────────────────────────────────
# Document Stats
# ─────────────────────────────────────────────

@router.get("/stats")
def get_document_stats(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Thống kê tài liệu.
    """
    return document_service.get_stats(current_user, db)


# ─────────────────────────────────────────────
# Delete Document
# ─────────────────────────────────────────────

@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Xóa tài liệu.
    """
    document_service.delete_document(document_id, current_user, db)
    return None