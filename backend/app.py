# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# ✅ Updated: Now uses Google Search Tool for LIVE, real-time answers (News, Weather, Sports, etc.)
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
# import feedparser # REMOVED: No longer needed, as Gemini will use Google Search for news
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Allow frontend connection (Render static site)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Request model
class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}

@app.post("/chat")
async def chat(request: ChatRequest):
    # 💬 Let Gemini answer and use Google Search for real-time data
    try:
        # 🟢 CHANGE 1: Using gemini-2.5-flash for fast responses with Search grounding
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 🟢 CHANGE 2: Enable Google Search Tool for live web search and real-time answers
        response = model.generate_content(
            request.message,
            tools=[{"googleSearch": {}}] 
        )
        
        # 🟢 CHANGE 3: The old RSS news fetching logic has been entirely removed.

        return {"reply": response.text if hasattr(response, "text") else "⚠️ कोई उत्तर उपलब्ध नहीं है।"}
    
    except Exception as e:
        # This will handle both standard chat errors and now search-related errors
        return {"reply": f"⚠️ आपकी चैट का उत्तर देने में समस्या आई: {str(e)}"}
