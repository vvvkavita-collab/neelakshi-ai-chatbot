import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Gemini (Google AI) import
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# ENV for Gemini API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if HAS_GENAI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

@app.post("/chat")
def chat(req: ChatRequest):
    # Gemini API call
    if not (HAS_GENAI and GEMINI_API_KEY):
        return {"reply": "❌ Gemini API key not configured."}
    try:
        # Prepare messages history for Gemini chat format
        chat_format = [{"role": m.role, "parts": [m.content]} for m in req.messages]
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(chat_format)
        # Response handling as plain text
        if hasattr(response, "text") and response.text:
            return {"reply": response.text.strip()}
        return {"reply": str(response)}
    except Exception as e:
        return {"reply": f"❌ Gemini error: {str(e)}"}
