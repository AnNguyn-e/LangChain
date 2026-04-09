import os
import shutil
from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.model.user_model import User, RoleEnum
from app.model.document_model import Document
from app.schemas import schemas
from app.LLM.langchain_ops import process_and_embed_document

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def upload_document(
    file: UploadFile,
    current_user: User,
    db: Session
) -> schemas.UploadDocumentResponse:
    """
    Xử lý upload tài liệu: lưu disk, tạo record DB, và thực hiện embedding.
    """
    allowed_extensions = (
        ".pdf", ".txt", ".csv",
        ".xlsx", ".xls",
        ".doc", ".docx",
        ".png", ".jpg", ".jpeg"
    )
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Định dạng tệp không được hỗ trợ")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Lưu file xuống disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu tệp: {str(e)}")

    # Tạo bản ghi document trong SQLite với trạng thái "processing"
    new_doc = Document(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user.id,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    try:
        # Xử lý: load → clean → chunk → embed vào ChromaDB
        num_chunks = process_and_embed_document(file_path, current_user.id)

        # Cập nhật trạng thái và số chunk
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
            message=f"Upload và index thành công ({num_chunks} chunks)"
        )

    except Exception as e:
        # Cập nhật trạng thái thất bại và lưu lỗi
        new_doc.status = "failed"
        new_doc.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Xử lý tài liệu thất bại: {str(e)}"
        )


def get_all_documents(
    current_user: User,
    db: Session
) -> List[Document]:
    """
    Lấy danh sách tài liệu dựa trên quyền hạn của người dùng.
    """
    if current_user.role == RoleEnum.ADMIN:
        return db.query(Document).all()
    else:
        return db.query(Document).filter(Document.user_id == current_user.id).all()


def get_stats(
    current_user: User,
    db: Session
):
    """
    Thống kê tài liệu: Admin thấy toàn bộ, User thấy cá nhân.
    """
    if current_user.role == RoleEnum.ADMIN:
        total_docs = db.query(Document).count()
        total_users = db.query(User).count()
        docs_by_user = (
            db.query(Document.user_id, func.count(Document.id))
            .group_by(Document.user_id)
            .all()
        )
        return {
            "total_documents": total_docs,
            "total_users": total_users,
            "documents_by_user": [
                {"user_id": uid, "count": count}
                for uid, count in docs_by_user
            ]
        }
    else:
        my_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
        return {"your_documents": my_docs}


def delete_document(
    document_id: int,
    current_user: User,
    db: Session
):
    """
    Xóa tài liệu và tệp vật lý.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    if doc.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa tài liệu này")

    # Xóa file vật lý nếu tồn tại
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            # Vẫn tiếp tục xóa DB record nhưng log lỗi hoặc thông báo
            print(f"Lỗi khi xóa file vật lý: {e}")

    db.delete(doc)
    db.commit()
    return True