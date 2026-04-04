import os
import shutil
from typing import List, Dict

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas
from database import engine, get_db
import auth
from langchain_ops import process_and_embed_document, get_answer

# Creates DB tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Internal Document Management System")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------
# Authentication
# ----------------

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    
    # First user gets ADMIN role
    is_first_user = db.query(models.User).count() == 0
    role = models.RoleEnum.ADMIN if is_first_user else models.RoleEnum.USER
    
    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ----------------
# Documents
# ----------------

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    allowed_extensions = (".pdf", ".txt", ".csv", ".xlsx", ".xls", ".doc", ".docx", ".png", ".jpg", ".jpeg")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Unsupported file format")
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Save to SQLite
    new_doc = models.Document(
        filename=file.filename,
        user_id=current_user.id,
        status="processing"
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    try:
        # Process and save to ChromaDB
        num_chunks = process_and_embed_document(file_path, current_user.id)
        
        # Update status
        new_doc.status = "completed"
        db.commit()
        
        return {
            "message": f"Successfully uploaded and indexed", 
            "filename": file.filename,
            "chunks": num_chunks
        }
    except Exception as e:
        new_doc.status = f"failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/documents", response_model=List[schemas.DocumentResponse])
def get_documents(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role == models.RoleEnum.ADMIN:
        docs = db.query(models.Document).all()
    else:
        docs = db.query(models.Document).filter(models.Document.user_id == current_user.id).all()
    return docs

@app.get("/documents/stats")
def get_stats(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    stats = {}
    if current_user.role == models.RoleEnum.ADMIN:
        stats["total_documents"] = db.query(models.Document).count()
        stats["total_users"] = db.query(models.User).count()
        docs_by_user = db.query(models.Document.user_id, func.count(models.Document.id)).group_by(models.Document.user_id).all()
        stats["documents_by_user"] = [{"user_id": uid, "count": count} for uid, count in docs_by_user]
    else:
        stats["your_documents"] = db.query(models.Document).filter(models.Document.user_id == current_user.id).count()
    return stats

# ----------------
# Chat
# ----------------

@app.post("/chat", response_model=schemas.ChatResponse)
def chat(
    request: schemas.ChatRequest, 
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        is_admin = current_user.role == models.RoleEnum.ADMIN
        answer, sources = get_answer(request.query, user_id=current_user.id, is_admin=is_admin)
        return schemas.ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
