# app/model/__init__.py
# Re-export tất cả models để có thể import gọn: from app.model import User, Document, ...

from app.model.user_model import User, RoleEnum
from app.model.document_model import Document
from app.model.chats_model import Chat
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
