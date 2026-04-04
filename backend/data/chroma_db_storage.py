from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from model import embedding_model
import chromadb
embedding= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_db= Chroma.from_documents
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection("documents")