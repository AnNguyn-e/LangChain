from fastapi import FastAPI
app = FastAPI()
@app.get('/')
def index():
    return {"message": "Hello, World!"}

@app.post('/chat')
def chat(query: str):
    return {"answer": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="[IP_ADDRESS]", port=8000)