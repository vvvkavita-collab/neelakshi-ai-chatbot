# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# Real-Time Google Search + Gemini AI (2025 Live)
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests, os
from dotenv import load_dotenv

# Load env
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
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.message.strip().lower()

    # If question is about current or 2025 data → use Google Search
    if any(word in user_input for word in ["today", "now", "latest", "current", "news", "2025", "आज", "अब", "अभी"]):
        try:
            search_url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}"
            response = requests.get(search_url)
            data = response.json()

            if "items" in data:
                results = []
                for item in data["items"][:3]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    results.append(f"🔹 **{title}**\n{snippet}\n🔗 {link}\n")
                return {"reply": "\n\n".join(results)}
            else:
                return {"reply": "❌ No fresh data found online. Check your Google API or CSE ID."}
        except Exception as e:
            return {"reply": f"⚠️ Google Search Error: {str(e)}"}

    # Otherwise use Gemini
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        result = model.generate_content(request.message)
        return {"reply": result.text}
    except Exception as e:
        return {"reply": f"⚠️ Gemini Error: {str(e)}"}
