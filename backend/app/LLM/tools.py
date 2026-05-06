from typing import Dict, Any, List

def search_documents(query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm tài liệu.
    Đây là tool placeholder để LLM gọi khi cần thiết.
    """
    return [{"title": "Demo", "content": "This is a demo content based on query: " + query}]

# Định nghĩa các tool theo chuẩn OpenAI / LangChain
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Tìm kiếm thông tin trong cơ sở dữ liệu nội bộ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm."
                    },
                    "filters": {
                        "type": "object",
                        "description": "Bộ lọc nâng cao (tùy chọn)."
                    }
                },
                "required": ["query"]
            }
        }
    }
]
