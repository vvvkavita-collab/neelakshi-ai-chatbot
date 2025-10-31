# ============================================
# ✅ Neelakshi AI Chatbot – Real-time & Smart version
# Combines:
#   - Hindi News (RSS)
#   - Live web via Google Custom Search (auto source tuning)
#   - Gemini AI summarization & translation
#   - Weather API & simple live info enhancer
# ============================================

import os
import requests
import feedparser
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from datetime import datetime

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if not GEMINI_API_KEY:
    raise Exception("❌ GEMINI_API_KEY missing! Add it in Render → Environment Variables.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------
# FastAPI init
# -------------------------
app = FastAPI(title="Neelakshi AI Chatbot - Real-time Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str


# -------------------------
# Helper Functions
# -------------------------
def google_search_snippets(query, max_results=3):
    """Fetch small snippets using Google Custom Search API"""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_SEARCH_ENGINE_ID, "q": query, "num": max_results}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if "items" in data:
            return " ".join([f"{item['title']}: {item['snippet']}" for item in data["items"][:max_results]])
    except Exception:
        return None
    return None


def google_news_hindi_top5():
    """Fetch Top 5 Hindi headlines"""
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None


def ask_gemini(prompt):
    """Ask Gemini 2.x models safely"""
    model_candidates = [
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash",
    ]
    for name in model_candidates:
        try:
            model = genai.GenerativeModel(name)
            res = model.generate_content(prompt)
            if hasattr(res, "text") and res.text:
                return res.text
            return str(res)
        except Exception:
            continue
    return None


def get_weather_for(location: str):
    """Get live weather via Open-Meteo API"""
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1").json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()
        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]
        return f"🌤️ {location} का तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None


# -------------------------
# Routes
# -------------------------
@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}


@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        return {"reply": "कृपया कुछ टाइप करें।"}

    lower = user_text.lower()

    # 1️⃣ Top Hindi News
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की खबर"]):
        headlines = google_news_hindi_top5()
        if headlines:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])}
        return {"reply": "⚠️ फिलहाल खबरें प्राप्त नहीं हो सकीं।"}

    # 2️⃣ Weather Queries
    if "weather" in lower or "मौसम" in lower:
        words = lower.replace("weather", "").replace("मौसम", "").strip()
        location = words if words else "Delhi"
        weather_info = get_weather_for(location)
        if weather_info:
            return {"reply": weather_info}
        return {"reply": "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # 3️⃣ Cricket / Live / Match related
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "series", "score"]):
        refined_query = user_text + " site:espncricinfo.com OR site:cricbuzz.com"
    # 4️⃣ Elections
    elif any(word in lower for word in ["election", "vote", "result", "नतीजे", "चुनाव"]):
        refined_query = user_text + " site:indiatoday.in OR site:ndtv.com"
    # 5️⃣ Location / City / State
    elif any(word in lower for word in ["district", "city", "state", "location", "area", "जिला", "शहर", "राज्य"]):
        refined_query = user_text + " site:wikipedia.org OR site:india.gov.in OR site:mapsofindia.com"
    else:
        refined_query = user_text

    # 6️⃣ Search online (Google Custom Search)
    snippets = google_search_snippets(refined_query)
    if snippets:
        prompt = (
            f"User question: {user_text}\n"
            f"Today's date: {datetime.now().strftime('%d %B %Y')}\n\n"
            f"Recent online information:\n{snippets}\n\n"
            "Give a current, fact-based and location-aware answer in Hindi if question is Hindi, otherwise English."
        )
        gemini_reply = ask_gemini(prompt)
        if gemini_reply:
            return {"reply": gemini_reply}
        return {"reply": f"Here's what I found online:\n{snippets}"}

    # 7️⃣ Fallback (Gemini reasoning)
    prompt = f"User asked: {user_text}\nAnswer clearly and helpfully in Hindi/English as per question."
    gemini_reply = ask_gemini(prompt)
    if gemini_reply:
        return {"reply": gemini_reply}

    return {"reply": "⚠️ मैं इस समय सटीक जानकारी प्राप्त नहीं कर पा रही हूँ। कृपया बाद में प्रयास करें।"}


# -------------------------
# For Render
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
