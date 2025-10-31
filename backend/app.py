# ============================================
# ✅ Neelakshi AI Chatbot – Real-time & Smart version (v2)
# Adds:
#   - Free live Cricket API (CricAPI)
#   - Verified Collector / State info from gov sites
#   - Hindi News (RSS)
#   - Weather API (Open-Meteo)
#   - Gemini for summarization and reasoning
# ============================================

import os
import requests
import feedparser
from dotenv import load_dotenv
from fastapi import FastAPI
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
CRICAPI_KEY = os.getenv("CRICAPI_KEY")  # 🏏 Add this in Render too!

if not GEMINI_API_KEY:
    raise Exception("❌ GEMINI_API_KEY missing! Add it in Render → Environment Variables.")

genai.configure(api_key=GEMINI_API_KEY)

# -------------------------
# FastAPI app init
# -------------------------
app = FastAPI(title="Neelakshi AI Chatbot – Real-time Smart Version")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "items" in data:
            return " ".join([f"{i['title']}: {i['snippet']}" for i in data["items"][:max_results]])
    except Exception:
        return None
    return None


def google_news_hindi_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None


def get_weather(location):
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


def get_live_cricket():
    """Fetch live cricket match info"""
    if not CRICAPI_KEY:
        return None
    try:
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "data" not in data:
            return None
        for match in data["data"]:
            if match.get("matchType") == "t20" and "India" in str(match.get("teams", [])):
                team1, team2 = match["teams"]
                venue = match.get("venue", "Unknown venue")
                status = match.get("status", "No update")
                return f"🏏 {team1} vs {team2}\n📍 स्थान: {venue}\n📊 स्थिति: {status}"
        return None
    except Exception:
        return None


def ask_gemini(prompt):
    for model_name in ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if hasattr(res, "text") and res.text:
                return res.text
        except Exception:
            continue
    return None


# -------------------------
# Routes
# -------------------------
@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}


@app.post("/chat")
async def chat(req: ChatRequest):
    text = (req.message or "").strip()
    if not text:
        return {"reply": "कृपया कुछ टाइप करें।"}

    lower = text.lower()

    # 🗞️ Hindi News
    if any(k in lower for k in ["news", "खबर", "headline", "समाचार"]):
        news = google_news_hindi_top5()
        if news:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(news)])}
        return {"reply": "⚠️ फिलहाल खबरें प्राप्त नहीं हो सकीं।"}

    # 🌦️ Weather
    if "weather" in lower or "मौसम" in lower:
        loc = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        weather_info = get_weather(loc)
        return {"reply": weather_info or "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # 🏏 Cricket (real-time)
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "score", "series"]):
        live = get_live_cricket()
        if live:
            return {"reply": live}
        else:
            refined = text + " site:espncricinfo.com OR site:cricbuzz.com"
            snippet = google_search_snippets(refined)
            if snippet:
                return {"reply": snippet}
            return {"reply": "⚠️ इस समय कोई लाइव क्रिकेट डेटा नहीं मिला।"}

    # 🧑‍💼 Collector / Admin info
    if "collector" in lower or "जिला अधिकारी" in lower or "district" in lower:
        refined = text + " site:rajasthan.gov.in OR site:india.gov.in OR site:wikipedia.org"
        snippet = google_search_snippets(refined)
        if snippet:
            prompt = (
                f"User asked: {text}\nToday's date: {datetime.now().strftime('%d %B %Y')}\n"
                f"Recent info: {snippet}\n"
                "Find the current official name (latest, 2025) of the District Collector mentioned."
                "Answer in Hindi with English name if possible."
            )
            reply = ask_gemini(prompt)
            if reply:
                return {"reply": reply}
        return {"reply": "⚠️ कलेक्टर की जानकारी अभी अपडेट नहीं है। कृपया सरकारी वेबसाइट देखें।"}

    # 🌐 General queries (Google + Gemini)
    snippet = google_search_snippets(text)
    if snippet:
        prompt = (
            f"User question: {text}\nToday's date: {datetime.now().strftime('%d %B %Y')}\n"
            f"Web data: {snippet}\nProvide a helpful, current factual answer in Hindi/English."
        )
        reply = ask_gemini(prompt)
        return {"reply": reply or snippet}

    # 💬 Fallback
    reply = ask_gemini(f"User asked: {text}\nAnswer briefly in Hindi/English.")
    return {"reply": reply or "⚠️ अभी सटीक जानकारी नहीं मिल सकी। बाद में प्रयास करें।"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
