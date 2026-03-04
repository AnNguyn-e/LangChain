from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()  # file .env cần có GOOGLE_API_KEY=AIza...
llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
messages =[
    SystemMessage(content="is that you"),
    HumanMessage(content="yes, it is me"),
   
]
resuilt =llm.invoke( messages=messages)
print(resuilt.content)