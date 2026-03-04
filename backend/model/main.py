from langchain_openai import ChatOpenAI
# Khởi tạo model từ LM Studio
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1", # Địa chỉ server của LM Studio
    api_key="lm-studio",                 # LM Studio không check key, bạn điền gì cũng được
    model="ignored"                      # Model đã được load sẵn trong LM Studio nên không cần định nghĩa lại
)

# Chạy thử
response = llm.invoke("helo")
print(response.contentiii)