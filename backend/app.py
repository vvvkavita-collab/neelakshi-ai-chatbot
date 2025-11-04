import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel

# ==============================
# ✅ Load Gemini API Key
# ==============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# ==============================
# ✅ Allow Frontend Access
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; restrict later to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# ✅ Data Models
# ==============================
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

# ==============================
# ✅ Root Endpoint
# ==============================
@app.get("/")
async def index():
    return {"status": "Backend is running fine ✅"}

# ==============================
# ✅ Normal Chat Endpoint
# ==============================
@app.post("/chat")
async def chat(req: ChatRequest):
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(chat_format)
        return {"reply": response.text}
    except Exception as e:
        return JSONResponse(content={"reply": f"⚠️ Error: {e}"}, status_code=500)

# ==============================
# ✅ Streaming Chat Endpoint
# ==============================
@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]
    model = genai.GenerativeModel("gemini-1.5-flash")

    def generate():
        try:
            for chunk in model.generate_content(chat_format, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")
