# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# ============================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Neelakshi AI Chatbot API",
    description="FastAPI backend for Neelakshi AI Chatbot hosted on Render",
    version="1.0.0",
)

# Enable CORS for all origins (to fix network error on other devices)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend URL later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define request schema
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

        # Check for valid text response
        if hasattr(response, "text") and response.text:
            return {"reply": response.text}
        else:
            return {"reply": "⚠️ Sorry, I couldn’t generate a valid reply."}

    except Exception as e:
        print(f"Error: {e}")  # for Render logs
        return {"reply": f"⚠️ Error occurred: {str(e)}"}
