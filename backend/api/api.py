from importlib_resources import contents
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from fastapi import FastAPI, File, UploadFile
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from sympy import content
from data.database import Sessionlocal, UploadFile_PDF
from vector_store import vector_db
from file_loader import split_text
from rag import ask_question
# Khởi tạo FastAPI app
app = FastAPI()
# Khởi tạo model từ LM Studio
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1", # Địa chỉ server của LM Studio
    api_key="lm-studio",                 # LM Studio không check key, bạn điền gì cũng được
    model="ignored"                      # Model đã được load sẵn trong LM Studio nên không cần định nghĩa lại
)
embedding = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large", encode_kwargs={"normalize_embeddings": True})

@app("/generate_embedding/")
async def generate_embedding(text: str):
   print(embedding.embed_query(text)) 
app = FastAPI()

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8")
    # Chia văn bản thành các đoạn nhỏ
    chunk = split_text(text)
    # Tạo embedding và lưu vào vector store
@app.get("'")
async def root():
    return {"message": "API is running"}
@app.post("")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    # Lưu file vào cơ sở dữ liệu
    db = Sessionlocal()
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    # Lưu file vào cơ sở dữ liệu
    db = Sessionlocal()
    pdf_file = UploadFile_PDF(filename=file.filename, content=contents)
    db.add(pdf_file)
    db.commit()
    return {"filename": file.filename, "size": len(contents)}
