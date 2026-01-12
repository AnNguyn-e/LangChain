from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    openai_api_base="http://192.168.171.1:1234/v1",
    openai_api_key="lm-studio",
    model="qwen3-8b",
    temperature=0.7
)

res = llm.invoke("Giải thích Gradient Descent cho người mới học")
print(res.content)
