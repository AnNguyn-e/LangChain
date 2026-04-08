from fastapi import FastAPI
from app.api import auth, documents, chat

app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")