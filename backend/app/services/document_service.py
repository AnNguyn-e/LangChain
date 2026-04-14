import os
import shutil
import hashlib
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.model.user_model import User, RoleEnum
from app.model.document_model import Document
from app.model.tag_model import Tag
from app.schemas import schemas
from app.LLM.langchain_ops import process_and_embed_document

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024 # 50MB

def get_file_hash(file_content: bytes) -> str:
    """Tính SHA-256 hash của nội dung file."""
    return hashlib.sha256(file_content).hexdigest()

def upload_document(
    file: UploadFile,
    current_user: User,
    db: Session
) -> schemas.UploadDocumentResponse:
    """
    Xử lý upload tài liệu: check size, check hash (trùng lặp), lưu disk, tạo record DB, và embedding.
    """
    # 1. Kiểm tra định dạng
    allowed_extensions = (".pdf", ".txt", ".docx")
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Định dạng {ext} không được hỗ trợ. Chỉ nhận PDF, TXT, DOCX.")

    # 2. Đọc nội dung để kiểm tra kích thước và tính hash
    try:
        content = file.file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {filename} vượt quá giới hạn 50MB")
        
        file_hash = get_file_hash(content)
        
        # 3. Kiểm tra trùng lặp (Deduplication)
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing_doc:
            raise HTTPException(status_code=400, detail=f"Tài liệu '{filename}' đã tồn tại trong hệ thống (trùng nội dung).")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {str(e)}")
    finally:
        file.file.seek(0) # Reset pointer

    # 4. Lưu file xuống disk
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}{ext}") # Lưu theo hash để tránh trùng tên
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu tệp: {str(e)}")

    # 5. Tạo bản ghi document
    new_doc = Document(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        file_type=ext.replace('.', '').upper(),
        file_hash=file_hash,
        user_id=current_user.id,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    try:
        # 6. Xử lý embedding (chạy đồng bộ cho đơn giản, hoặc async nhiệm vụ sau)
        num_chunks = process_and_embed_document(file_path, current_user.id)

        new_doc.status = "completed"
        new_doc.chunk_count = num_chunks
        db.commit()
        db.refresh(new_doc)

        return schemas.UploadDocumentResponse(
            id=new_doc.id,
            filename=new_doc.filename,
            status=new_doc.status,
            chunk_count=num_chunks,
            created_at=new_doc.created_at,
            message="Xử lý thành công"
        )

    except Exception as e:
        new_doc.status = "failed"
        new_doc.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Xử lý AI thất bại: {str(e)}"
        )

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

def assign_tag_to_document(doc_id: int, tag_id: int, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not doc or not tag:
        raise HTTPException(status_code=404, detail="Doc hoặc Tag không tồn tại")
    
    if tag not in doc.tags:
        doc.tags.append(tag)
        db.commit()
    return doc