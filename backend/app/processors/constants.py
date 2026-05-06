"""
app/processors/constants.py
──────────────────────────────────────────────────────────────
Các hằng số dùng chung cho quá trình xử lý tài liệu.
"""

# Chunking
CHUNK_SIZE        = 1000   # chars
CHUNK_OVERLAP     = 200
MIN_CHUNK_CHARS   = 30     # chunks ngắn hơn sẽ bị loại bỏ

# OCR
OCR_MIN_CONF      = 0.40   # độ tự tin tối thiểu của OCR
IMAGE_MAX_DIM     = 2048   # kích thước ảnh tối đa (pixels)
IMAGE_OCR_DPI     = 300    # DPI mục tiêu khi trích xuất trang PDF

# Pipeline
EMBED_BATCH_SIZE  = 16     # số lượng chunks mỗi batch embedding (tối ưu cho local model)
MAX_WORKERS       = 4      # số luồng xử lý song song (trang PDF, v.v.)
CHROMA_DB_DIR     = "chroma_db"
EMBED_MODEL_NAME  = "nomic-embed-text:latest" # Model name from LM Studio (nomic, etc.)
EMBED_COLLECTION  = "document_chunks"

# Local AI (LM Studio / Ollama via OpenAI spec)
LM_STUDIO_BASE_URL = " http://192.168.171.1:1234"
