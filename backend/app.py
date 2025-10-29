# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# ============================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Allow frontend (Render static site)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can replace "*" with your frontend Render URL for safety
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Request schema
class ChatRequest(BaseModel):
    message: str

# Root health check
@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(request.message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
