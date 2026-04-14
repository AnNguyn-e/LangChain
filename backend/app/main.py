from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.api import auth, documents
from app.database.database import Base, engine
from app.model import (
    user_model,
    document_model,
    document_metadata_model,
    document_chunk_model,
    document_embedding_model,
    tag_model,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (bền bỉ nhất cho dev/ngrok)
    allow_credentials=False, # Tắt vì chúng ta dùng Bearer Token (không dùng Cookie)
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, documents, chat

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
