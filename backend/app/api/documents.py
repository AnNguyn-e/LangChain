from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services import document_service
from app.schemas import schemas
from app.services.auth_service import get_current_user
from app.model.user_model import User

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload-multiple", response_model=schemas.BulkUploadResponse)
def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tải lên nhiều tài liệu cùng lúc."""
    results = []
    errors = []
    
    for file in files:
        # Re-seek file just in case
        file.file.seek(0)
        try:
            res = document_service.upload_document(file, current_user, db)
            results.append(res)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
            
    return {"results": results, "errors": errors}

@router.get("/", response_model=List[schemas.DocumentResponse])
def list_documents(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên file"),
    tag_id: Optional[int] = Query(None, description="Lọc theo tag"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách tài liệu với bộ lọc."""
    return document_service.get_all_documents(current_user, db, search, tag_id)

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa tài liệu."""
    document_service.delete_document(document_id, current_user, db)
    return {"message": "Xóa thành công"}

# ─────────────────────────────────────────────
# Tag Endpoints
# ─────────────────────────────────────────────

@router.get("/tags", response_model=List[schemas.TagResponse])
def list_tags(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả các thẻ."""
    return document_service.get_tags(db)

@router.post("/tags", response_model=schemas.TagResponse)
def create_tag(
    tag_in: schemas.TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo thẻ mới."""
    return document_service.create_tag(tag_in, db)

@router.post("/{document_id}/tags/{tag_id}")
def assign_tag(
    document_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Gắn thẻ cho tài liệu."""
    return document_service.assign_tag_to_document(document_id, tag_id, db)