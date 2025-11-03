import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from dotenv import load_dotenv
from pydantic import BaseModel

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@app.get("/")
async def index():
    return {"status": "Backend is running fine ✅"}

@app.post("/chat")
async def chat(req: ChatRequest):
    """Non-streaming chat endpoint"""
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    try:
        response = model.generate_content(chat_format)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"[Error: {str(e)}]"}

@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    """Streaming chat endpoint"""
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    def generate():
        try:
            for chunk in model.generate_content(chat_format, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")
