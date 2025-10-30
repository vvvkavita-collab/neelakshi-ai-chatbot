# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# Real-Time Google Search + Gemini AI
# ============================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os, requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend running fine!"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.message.strip()

    # Detect if question needs live info
    live_keywords = ["today", "now", "latest", "current", "news", "2025", "अभी", "आज", "अब", "ताज़ा"]
    if any(k in user_input.lower() for k in live_keywords):
        try:
            search_url = (
                f"https://www.googleapis.com/customsearch/v1?"
                f"q={user_input}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}"
            )
            res = requests.get(search_url)
            data = res.json()

            if "items" in data:
                top_results = []
                for item in data["items"][:3]:
                    top_results.append(f"📰 **{item['title']}**\n{item['snippet']}\n🔗 {item['link']}\n")

                joined = "\n".join(top_results)
                return {"reply": f"Here are the latest results I found:\n\n{joined}"}
            else:
                return {"reply": "No fresh info found online right now."}
        except Exception as e:
            return {"reply": f"⚠️ Google Search Error: {str(e)}"}

    # Fallback to Gemini
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(user_input)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Gemini Error: {str(e)}"}
