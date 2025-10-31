# ============================================
# Neelakshi AI Chatbot - FastAPI + Gemini + Live Google Search + Hindi News
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import os
import feedparser
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# API Keys
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Request Schema
class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot Backend is Running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_msg = request.message.lower()

    # 📰 If user asks for news (Hindi)
    if "news" in user_msg or "खबर" in user_msg or "headline" in user_msg:
        try:
            feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
            headlines = [entry.title for entry in feed.entries[:5]]
            if not headlines:
                return {"reply": "⚠️ फिलहाल कोई खबरें प्राप्त नहीं हुईं। कृपया कुछ समय बाद पुनः प्रयास करें।"}
            news_text = "\n".join([f"{i+1}. {headline}" for i, headline in enumerate(headlines)])
            return {"reply": f"🗞️ आज की टॉप 5 हिंदी खबरें:\n\n{news_text}"}
        except Exception as e:
            return {"reply": f"⚠️ खबरें लोड करने में समस्या आई: {str(e)}"}

    # 🌍 Otherwise fetch live info from Google Search
    try:
        query = request.message.strip()
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={query}"
        )
        search_response = requests.get(search_url)
        search_data = search_response.json()

        if "items" in search_data:
            snippets = " ".join([item["snippet"] for item in search_data["items"][:3]])
        else:
            snippets = "No recent web results found."

        # 💬 Combine live search + Gemini summary
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        prompt = f"""
        The user asked: {query}
        Based on recent web results: {snippets}
        Answer clearly and accurately for the year 2025.
        If question is about a city, district, or state — give location-specific answer.
        """
        response = model.generate_content(prompt)

        return {"reply": response.text if hasattr(response, "text") else "⚠️ कोई उत्तर उपलब्ध नहीं है।"}

    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
