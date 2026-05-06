from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, AsyncGenerator
import json

from app.model.chats_session import ChatSession
from app.model.chats_model import Chat
from app.model.user_model import RoleEnum
from app.LLM.langchain_ops import get_answer_stream

def create_chat_session(db: Session, user_id: int, title: str) -> ChatSession:
    new_session = ChatSession(user_id=user_id, title=title)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_user_sessions(db: Session, user_id: int) -> List[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()

def get_chat_messages(db: Session, session_id: int, user_id: int) -> List[Chat]:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = db.query(Chat).filter(Chat.session_id == session_id).order_by(Chat.created_at.asc()).all()
    return messages

async def generate_chat_stream(db: Session, session_id: int, user_id: int, role: RoleEnum, query: str) -> AsyncGenerator[str, None]:
    # Verify session
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    is_admin = (role == RoleEnum.ADMIN)
    
    # Retrieve past messages
    past_messages = db.query(Chat).filter(Chat.session_id == session_id).order_by(Chat.created_at.asc()).all()
    
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    chat_history = []
    
    # Add summary as system message if it exists
    if session.summary:
        chat_history.append(SystemMessage(content=f"Tóm tắt các cuộc hội thoại trước: {session.summary}"))
        
    # Build history (sliding window of last 6 messages, 3 pairs)
    recent_messages = past_messages[-6:]
    for msg in recent_messages:
        chat_history.append(HumanMessage(content=msg.question))
        chat_history.append(AIMessage(content=msg.answer))
        
    # Summarize if history gets too long (e.g., > 10 messages)
    if len(past_messages) > 10:
        # We should summarize the old messages in a background task ideally, but for simplicity here:
        from app.LLM.langchain_ops import summarize_chat_history
        new_summary = summarize_chat_history(chat_history)
        session.summary = new_summary
        db.commit()
    
    # Create an active generator from LangChain
    answer_generator = get_answer_stream(query, user_id, is_admin, chat_history=chat_history)
    
    full_answer = ""
    sources = []
    try:
        for item in answer_generator:
            if item.startswith("data: ") and not item.startswith("data: [DONE]"):
                json_str = item[len("data: "):].strip()
                if json_str:
                    try:
                        obj = json.loads(json_str)
                        if "content" in obj:
                            full_answer += obj["content"]
                        if "sources" in obj:
                            sources = obj["sources"]
                    except json.JSONDecodeError:
                        pass
            yield item
    finally:
        # Save the record after streaming completes
        new_chat = Chat(
            user_id=user_id,
            session_id=session_id,
            question=query,
            answer=full_answer,
            sources=json.dumps(sources) if sources else None
        )
        db_session_sync = db.object_session(session) if db.object_session(session) else db
        db_session_sync.add(new_chat)
        db_session_sync.commit()
