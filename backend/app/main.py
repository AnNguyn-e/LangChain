from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents
from app.database.database import Base, engine
from app.model import user_model, document_model, tag_model

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
