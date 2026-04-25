from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services import document_service
from app.schemas import schemas
from app.services.auth_service import get_current_user
from app.model.user_model import User

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=schemas.UploadDocumentResponse)
def upload_single_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tải lên một tài liệu duy nhất."""
    return document_service.upload_document(file, current_user, db, background_tasks)


@router.post("/upload-multiple", response_model=schemas.BulkUploadResponse)
def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tải lên nhiều tài liệu cùng lúc. Xử lý (chunk + embed) chạy ngầm."""
    results = []
    errors  = []

    for file in files:
        file.file.seek(0)
        try:
            res = document_service.upload_document(file, current_user, db, background_tasks)
            results.append(res)
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    return {"results": results, "errors": errors}


@router.get("/{document_id}/status", response_model=schemas.DocumentResponse, summary="Kiểm tra trạng thái xử lý")
def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin và trạng thái xử lý của một tài liệu."""
    return document_service.get_document_by_id(document_id, current_user, db)

@router.get("", response_model=List[schemas.DocumentResponse])
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

@router.patch("/{document_id}", response_model=schemas.DocumentResponse)
def update_document(
    document_id: int,
    doc_in: schemas.DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin và metadata của tài liệu."""
    return document_service.update_document(document_id, doc_in, current_user, db)

@router.post("/bulk-delete")
def bulk_delete_documents(
    request: schemas.BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa hàng loạt tài liệu theo danh sách IDs."""
    return document_service.bulk_delete_documents(request.ids, current_user, db)

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tải file tài liệu gốc."""
    file_path, filename = document_service.get_document_file_info(document_id, current_user, db)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

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

@router.get("/tags/{tag_id}/documents", response_model=List[schemas.DocumentResponse], summary="Lấy danh sách tài liệu theo tag")
def get_documents_by_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách tất cả các tài liệu được gắn với một tag xác định."""
    return document_service.get_documents_by_tag(tag_id, current_user, db)

@router.post("/{document_id}/tags/{tag_id}", summary="Gắn tag vào tài liệu")
def assign_tag(
    document_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Gắn thẻ cho tài liệu."""
    return document_service.assign_tag_to_document(document_id, tag_id, db)


@router.delete("/{document_id}/tags/{tag_id}", summary="Gỡ tag khỏi tài liệu")
def remove_tag(
    document_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Gỡ một tag ra khỏi tài liệu. Chỉ chủ sở hữu hoặc Admin mới có quyền."""
    return document_service.remove_tag_from_document(document_id, tag_id, current_user, db)


@router.delete("/tags/{tag_id}", summary="Xóa tag khỏi hệ thống")
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa tag khỏi hệ thống (chỉ Admin). Tag sẽ tự động được gỡ khỏi tất cả document."""
    from app.model.user_model import RoleEnum
    if current_user.role != RoleEnum.ADMIN:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có thể xóa tag")
    return document_service.delete_tag(tag_id, db)