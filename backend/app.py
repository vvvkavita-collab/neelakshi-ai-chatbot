import os
import google.generativeai as genai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from dotenv import load_dotenv
from pydantic import BaseModel

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

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
    """Serve a simple frontend"""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    """Stream Gemini responses token by token"""
    chat_format = [
        {"role": m.role, "parts": [m.content]} if hasattr(m, "role") else {"role": m["role"], "parts": [m["content"]]}
        for m in req.messages
    ]
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    def generate():
        try:
            for chunk in model.generate_content(chat_format, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")
