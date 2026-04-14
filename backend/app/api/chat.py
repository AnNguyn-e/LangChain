from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.model.user_model import User
from app.schemas.schemas import ChatSessionCreate, ChatSessionResponse, ChatMessageResponse, ChatCreateRequest
from app.services.auth_service import get_current_user
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_service.create_chat_session(db=db, user_id=current_user.id, title=request.title)

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_service.get_user_sessions(db=db, user_id=current_user.id)

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_service.get_chat_messages(db=db, session_id=session_id, user_id=current_user.id)

@router.post("/sessions/{session_id}/stream")
async def stream_chat(
    session_id: int,
    request: ChatCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    generator = chat_service.generate_chat_stream(
        db=db, 
        session_id=session_id, 
        user_id=current_user.id, 
        role=current_user.role, 
        query=request.query
    )
    return StreamingResponse(generator, media_type="text/event-stream")
