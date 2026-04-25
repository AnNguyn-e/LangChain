import os
import re
from typing import List, Dict, Any

from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    CSVLoader, 
    UnstructuredExcelLoader, 
    Docx2txtLoader
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.processors.constants import LM_STUDIO_BASE_URL, EMBED_COLLECTION

# Constants
CHROMA_DB_DIR = "chroma_db"
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Initialize embeddings and vector store via Local LM Studio
embeddings = OpenAIEmbeddings(
    base_url=LM_STUDIO_BASE_URL,
    api_key="lm-studio",
    check_embedding_ctx_length=False
)
vectorstore = Chroma(
    collection_name=EMBED_COLLECTION,
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embeddings
)

# Initialize LM Studio LLM for Chat Generation
llm = ChatOpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key="lm-studio",
    temperature=0.7,
)

def clean_text(text: str) -> str:
    """Xóa khoảng trắng thừa và ký tự không cần thiết."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def load_image_with_rapidocr(file_path: str) -> List[Document]:
    """Sử dụng RapidOCR để bóc tách chữ từ ảnh độc lập."""
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    result, _ = ocr(file_path)
    text = ""
    if result:
        text = "\\n".join([item[1] for item in result])
    return [Document(page_content=text, metadata={"source": file_path})]

def process_and_embed_document(file_path: str, user_id: int):
    """Load, clean, chunk and embed document into ChromaDB."""
    ext = file_path.lower().split('.')[-1]
    
    if ext == "pdf":
        loader = PyPDFLoader(file_path, extract_images=True)
        docs = loader.load()
    elif ext == "csv":
        loader = CSVLoader(file_path)
        docs = loader.load()
    elif ext in ["xlsx", "xls"]:
        loader = UnstructuredExcelLoader(file_path, mode="elements")
        docs = loader.load()
    elif ext in ["docx", "doc"]:
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
    elif ext in ["png", "jpg", "jpeg"]:
        docs = load_image_with_rapidocr(file_path)
    else:
        # Default txt or other
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        
    # Process/Clean content
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
        
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\\n\\n", "\\n", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    
    # Add metadata source
    filename = os.path.basename(file_path)
    for split in splits:
        split.metadata["source"] = filename
        split.metadata["user_id"] = user_id
        
    # Add to vector database
    vectorstore.add_documents(documents=splits)
    return len(splits)

def get_answer(query: str, user_id: int = None, is_admin: bool = False):
    """Retrieve internal data and generate answer."""
    # Build filter
    filter_dict = {}
    if not is_admin and user_id is not None:
        filter_dict["user_id"] = user_id
        
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            "fetch_k": 10,
            "lambda_mult": 0.7,
            "filter": filter_dict if filter_dict else None
        }
    )
    
    # Retrieve relevant documents
    docs = retriever.invoke(query)
    
    # Extract sources for the response
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
    
    # Format context
    context = "\\n\\n".join([doc.page_content for doc in docs])
    
    if not docs:
         return "Tôi không tìm thấy thông tin nào liên quan đến câu hỏi trong các tài liệu hiện có.", sources

    # Create prompt template
    template = """Bạn là trợ lý AI hữu ích hỗ trợ nhân viên nội bộ công ty quản lý tài liệu.
Sử dụng các thông tin ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi, thông tin này được lấy từ dữ liệu nội bộ.
Nếu thông tin không liên quan gì, hãy báo rằng bạn không có câu trả lời.
KHÔNG được bịa đặt thông tin. Luôn trả lời bằng tiếng Việt một cách rõ ràng.

Ngữ cảnh:
{context}

Câu hỏi: {question}

Trả lời:"""
    prompt = PromptTemplate.from_template(template)
    
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": query})
    
    return answer, sources

import json

def get_answer_stream(query: str, user_id: int = None, is_admin: bool = False):
    """Retrieve internal data and generate answer via stream."""
    filter_dict = {}
    if not is_admin and user_id is not None:
        filter_dict["user_id"] = user_id
        
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            "fetch_k": 10,
            "lambda_mult": 0.7,
            "filter": filter_dict if filter_dict else None
        }
    )
    
    docs = retriever.invoke(query)
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
    context = "\n\n".join([doc.page_content for doc in docs])
    
    if not docs:
         msg = "Tôi không tìm thấy thông tin nào liên quan đến câu hỏi trong các tài liệu hiện có."
         yield f"data: {json.dumps({'content': msg})}\n\n"
         yield f"data: {json.dumps({'sources': sources})}\n\n"
         yield "data: [DONE]\n\n"
         return

    template = """Bạn là trợ lý AI hữu ích hỗ trợ nhân viên nội bộ công ty quản lý tài liệu.
Sử dụng các thông tin ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi, thông tin này được lấy từ dữ liệu nội bộ.
Nếu thông tin không liên quan gì, hãy báo rằng bạn không có câu trả lời.
KHÔNG được bịa đặt thông tin. Luôn trả lời bằng tiếng Việt một cách rõ ràng.

Ngữ cảnh:
{context}

Câu hỏi: {question}

Trả lời:"""
    prompt = PromptTemplate.from_template(template)
    
    chain = prompt | llm | StrOutputParser()
    
    for chunk in chain.stream({"context": context, "question": query}):
        yield f"data: {json.dumps({'content': chunk})}\n\n"
        
    # Send the final sources at the end
    yield f"data: {json.dumps({'sources': sources})}\n\n"
    yield "data: [DONE]\n\n"
