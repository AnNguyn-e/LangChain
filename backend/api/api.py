import os
import shutil
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize FastAPI app
app = FastAPI(title="Local Document RAG API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
UPLOAD_DIR = "uploads"
CHROMA_DB_DIR = "chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

# Initialize embeddings and vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

# Initialize LM Studio LLM
# Ensure LM Studio is running locally on port 1234
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",  # API key is not required for LM Studio but needed for the client
    temperature=0.7,
)

# -----------------
# Pydantic Models
# -----------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# -----------------
# API Endpoints
# -----------------

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF or TXT file, extract text, and add to Vector DB."""
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Load the document
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
            
        docs = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        # Add metadata source
        for split in splits:
            split.metadata["source"] = file.filename
            
        # Add to vector database
        vectorstore.add_documents(documents=splits)
        
        return {"message": f"Successfully processed and embedded {file.filename}", "chunks": len(splits)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the LLM based on uploaded documents."""
    
    # Create the retriever from the vector store
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Retrieve relevant documents
    docs = retriever.invoke(request.query)
    
    # Extract sources for the response
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
    
    # Format context
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Create prompt template
    template = """You are a helpful assistant for an internal file management system. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer or the context doesn't contain the answer, just say that you don't know, don't try to make up an answer.
Answer in Vietnamese.

Context:
{context}

Question: {question}

Answer:"""
    prompt = PromptTemplate.from_template(template)
    
    # Create the chain
    chain = prompt | llm | StrOutputParser()
    
    answer = chain.invoke({"context": context, "question": request.query})
    
    return ChatResponse(answer=answer, sources=sources)

# -----------------
# Static Files & Frontend Route
# -----------------
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    """Serve the frontend index.html at root."""
    static_file_path = os.path.join("static", "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    return {"message": "Frontend not found at static/index.html. Place your index.html in the static folder."}
