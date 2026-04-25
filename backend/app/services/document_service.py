import os
import hashlib
from typing import List, Optional
from datetime import datetime

from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.model.user_model import User, RoleEnum
from app.model.document_model import Document
from app.model.tag_model import Tag
from app.schemas import schemas
from app.services.document_processor import run_processing_pipeline

from app.processors import SUPPORTED_EXTENSIONS

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Giới hạn dung lượng file theo từng loại ─────────────────────────────────
# PDF: 50MB
# Office (Word, Excel, PPT): 20MB
# Images, Structured Data (CSV, JSON, HTML): 10MB
# Plain Text, Config: 5MB
FILE_SIZE_LIMITS = {
    # PDF
    "pdf": 50 * 1024 * 1024,
    # Word
    "docx": 20 * 1024 * 1024, "doc": 20 * 1024 * 1024,
    # Spreadsheet
    "xlsx": 20 * 1024 * 1024, "xls": 20 * 1024 * 1024,
    # Presentation
    "pptx": 20 * 1024 * 1024, "ppt": 20 * 1024 * 1024,
    # Images
    "png": 10 * 1024 * 1024, "jpg": 10 * 1024 * 1024, "jpeg": 10 * 1024 * 1024,
    "bmp": 10 * 1024 * 1024, "tiff": 10 * 1024 * 1024, "webp": 10 * 1024 * 1024,
    # Structured / Markup
    "csv": 10 * 1024 * 1024, "tsv": 10 * 1024 * 1024,
    "json": 10 * 1024 * 1024, "jsonl": 10 * 1024 * 1024,
    "html": 10 * 1024 * 1024, "htm": 10 * 1024 * 1024,
    "md": 10 * 1024 * 1024, "markdown": 10 * 1024 * 1024,
}
DEFAULT_SIZE_LIMIT = 5 * 1024 * 1024  # 5MB cho txt, log, yaml...

def get_file_hash(file_content: bytes) -> str:
    """Tính SHA-256 hash của nội dung file."""
    return hashlib.sha256(file_content).hexdigest()

def upload_document(
    file: UploadFile,
    current_user: User,
    db: Session,
    background_tasks: BackgroundTasks,
) -> schemas.UploadDocumentResponse:
    """
    Upload tài liệu: validate → lưu disk → tạo DB record → trả về ngay.
    Quá trình xử lý (chunk + embed) chạy ngầm trong background.
    """
    # 1. Kiểm tra định dạng
    filename = file.filename or "unknown"
    ext_with_dot = os.path.splitext(filename)[1].lower()
    ext = ext_with_dot.lstrip(".")
    
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng '.{ext}' không được hỗ trợ. Các định dạng cho phép: {supported}"
        )

    # 2. Đọc nội dung, kiểm tra kích thước theo loại, tính hash
    try:
        content = file.file.read()
        file_size = len(content)
        
        # Lấy giới hạn dung lượng tương ứng
        limit = FILE_SIZE_LIMITS.get(ext, DEFAULT_SIZE_LIMIT)
        if file_size > limit:
            limit_mb = limit / (1024 * 1024)
            raise HTTPException(
                status_code=400, 
                detail=f"File '{filename}' ({file_size / 1024 / 1024:.1f}MB) vượt quá giới hạn cho phép ({limit_mb:.0f}MB) cho loại file này."
            )
        file_hash = get_file_hash(content)

        existing = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Tài liệu '{filename}' đã tồn tại trong hệ thống (trùng nội dung)."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {e}")
    finally:
        file.file.seek(0)

    # 3. Lưu file xuống disk (tên = hash + ext để tránh trùng)
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}{ext}")
    try:
        with open(file_path, "wb") as buf:
            buf.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu tệp: {e}")

    # 4. Tạo bản ghi Document với status='processing'
    new_doc = Document(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        file_type=ext.lstrip(".").upper(),
        file_hash=file_hash,
        user_id=current_user.id,
        status="processing",
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 5. Đặt lịch chạy pipeline ngầm
    background_tasks.add_task(
        run_processing_pipeline,
        document_id=new_doc.id,
        file_path=file_path,
        user_id=current_user.id,
    )

    return schemas.UploadDocumentResponse(
        id=new_doc.id,
        filename=new_doc.filename,
        status=new_doc.status,   # "processing"
        chunk_count=0,
        created_at=new_doc.created_at,
        message="Tài liệu đã được nhận. Đang xử lý trong nền..."
    )


def get_document_by_id(document_id: int, current_user: User, db: Session) -> Document:
    """Lấy thông tin một document theo id, có kiểm tra quyền."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    if doc.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Không có quyền xem tài liệu này")
    return doc

def get_all_documents(
    current_user: User,
    db: Session,
    search: Optional[str] = None,
    tag_id: Optional[int] = None
) -> List[Document]:
    """Lấy danh sách tài liệu có filter."""
    query = db.query(Document)
    
    if current_user.role != RoleEnum.ADMIN:
        query = query.filter(Document.user_id == current_user.id)
        
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))
        
    if tag_id:
        query = query.join(Document.tags).filter(Tag.id == tag_id)
        
    return query.order_by(Document.created_at.desc()).all()

def delete_document(document_id: int, current_user: User, db: Session):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    
    if doc.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Không có quyền xóa")

    # Xóa file vật lý
    if doc.file_path and os.path.exists(doc.file_path):
        # Kiểm tra xem có doc nào khác dùng chung file_path (hash) không
        other_using = db.query(Document).filter(Document.file_path == doc.file_path, Document.id != doc.id).count()
        if other_using == 0:
            os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return True

def update_document(
    document_id: int, 
    doc_in: schemas.DocumentUpdate, 
    current_user: User, 
    db: Session
) -> Document:
    """Cập nhật thông tin tài liệu và metadata."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    
    if doc.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa tài liệu này")

    # 1. Cập nhật thông tin cơ bản của Document
    if doc_in.filename is not None:
        doc.filename = doc_in.filename

    # 2. Cập nhật Metadata
    if doc_in.doc_metadata:
        from app.model.document_metadata_model import DocumentMetadata
        
        meta = doc.doc_metadata
        if not meta:
            # Tạo mới nếu chưa có
            meta = DocumentMetadata(document_id=doc.id)
            db.add(meta)
        
        update_data = doc_in.doc_metadata.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(meta, field, value)
        
        meta.updated_at = datetime.utcnow()

    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def bulk_delete_documents(
    doc_ids: List[int], 
    current_user: User, 
    db: Session
) -> dict:
    """Xóa hàng loạt tài liệu."""
    results = {"deleted": [], "errors": []}
    
    for doc_id in doc_ids:
        try:
            delete_document(doc_id, current_user, db)
            results["deleted"].append(doc_id)
        except Exception as e:
            results["errors"].append({"id": doc_id, "error": str(e)})
            
    return results


def get_document_file_info(
    document_id: int, 
    current_user: User, 
    db: Session
) -> tuple[str, str]:
    """Lấy đường dẫn file và filename nguyên thủy để download."""
    doc = get_document_by_id(document_id, current_user, db)
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File vật lý không tồn tại trên server")
    
    return doc.file_path, doc.filename

# ─────────────────────────────────────────────
# Tag Logic
# ─────────────────────────────────────────────

def create_tag(tag_in: schemas.TagCreate, db: Session) -> Tag:
    existing = db.query(Tag).filter(Tag.name == tag_in.name).first()
    if existing:
        return existing
    new_tag = Tag(name=tag_in.name, color=tag_in.color)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

def get_tags(db: Session) -> List[Tag]:
    return db.query(Tag).all()

def get_documents_by_tag(tag_id: int, current_user: User, db: Session) -> List[Document]:
    """Lấy danh sách các tài liệu thuộc một tag cụ thể, có kiểm tra quyền."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")
        
    query = db.query(Document).join(Document.tags).filter(Tag.id == tag_id)
    
    if current_user.role != RoleEnum.ADMIN:
        query = query.filter(Document.user_id == current_user.id)
        
    return query.order_by(Document.created_at.desc()).all()

def assign_tag_to_document(doc_id: int, tag_id: int, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not doc or not tag:
        raise HTTPException(status_code=404, detail="Doc hoặc Tag không tồn tại")

    if tag not in doc.tags:
        doc.tags.append(tag)
        db.commit()
    return doc


def remove_tag_from_document(doc_id: int, tag_id: int, current_user: User, db: Session):
    """Gỡ một tag khỏi document. Chỉ chủ sở hữu hoặc Admin mới có quyền."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    if doc.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa tài liệu này")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")

    if tag in doc.tags:
        doc.tags.remove(tag)
        db.commit()

    return {"message": f"Đã gỡ tag '{tag.name}' khỏi tài liệu"}


def delete_tag(tag_id: int, db: Session):
    """Xóa tag khỏi hệ thống. Tag sẽ tự động được gỡ khỏi tất cả document."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Không tìm thấy tag")

    db.delete(tag)
    db.commit()
    return {"message": f"Đã xóa tag '{tag.name}' khỏi hệ thống"}