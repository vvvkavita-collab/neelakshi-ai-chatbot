import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pydantic import BaseModel

# ==============================
# ✅ Load Gemini API Key
# ==============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# ==============================
# ✅ CORS Setup (Frontend Access)
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend URL if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# ✅ Models
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
# ✅ Chat Endpoint (Web-Enabled)
# ==============================
@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat endpoint with Gemini + Web Search enabled
    """
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]

    # ✅ Use experimental Gemini model with Google Search enabled
    model = genai.GenerativeModel(
        "models/gemini-2.0-pro-exp-02-05",
        tools=[{"google_search": {}}]
    )

    try:
        response = model.generate_content(chat_format)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"[Error: {str(e)}]"}


# ==============================
# ✅ Chat Stream Endpoint (Optional)
# ==============================
@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming chat endpoint (token by token)
    """
    chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]

    model = genai.GenerativeModel(
        "models/gemini-2.0-pro-exp-02-05",
        tools=[{"google_search": {}}]
    )

    def generate():
        try:
            for chunk in model.generate_content(chat_format, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")
