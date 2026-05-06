from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.model.user_model import User
from app.model.document_model import Document
from app.model.chats_model import Chat
from app.model.chats_session import ChatSession

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"]
)

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Lấy số liệu thống kê cơ bản cho Dashboard"""
    total_users = db.query(func.count(User.id)).scalar()
    total_documents = db.query(func.count(Document.id)).filter(Document.is_deleted == False).scalar()
    total_chats = db.query(func.count(Chat.id)).scalar()
    
    # Calculate total storage used by documents (in bytes)
    total_storage_bytes = db.query(func.sum(Document.file_size)).filter(Document.is_deleted == False).scalar() or 0
    
    # Convert bytes to MB
    total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
    
    # Get recent document uploads
    recent_documents = db.query(Document).filter(
        Document.is_deleted == False
    ).order_by(Document.created_at.desc()).limit(5).all()
    
    recent_docs_list = [{
        "id": doc.id,
        "filename": doc.filename,
        "created_at": doc.created_at,
        "status": doc.status
    } for doc in recent_documents]

    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_chats": total_chats,
            "total_storage_mb": total_storage_mb,
            "recent_documents": recent_docs_list
        }
    }
