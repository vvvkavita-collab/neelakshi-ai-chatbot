# ============================================
# ✅ Neelakshi AI Chatbot – Final Version (ChatGPT-like)
# Features:
#   - Hindi & English understanding
#   - Live News, Weather, Cricket, & General Queries
#   - Google Search + Gemini AI summarization
#   - Real-time live cricket via RapidAPI (Cricbuzz)
# ============================================

import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------
# Load Environment Variables
# -------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not GEMINI_API_KEY:
    raise Exception("❌ Missing GEMINI_API_KEY in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# -------------------------
# FastAPI Initialization
# -------------------------
app = FastAPI(title="Neelakshi AI Chatbot - Real-time Backend")

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

def google_news_hindi_top5():
    """Fetch top 5 Hindi news headlines"""
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None

def google_search_snippets(query, max_results=3):
    """Search small snippets using Google Custom Search API"""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": max_results,
        }
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if "items" in data:
            return " ".join(
                [f"{item['title']}: {item['snippet']} (Link: {item.get('link','')})" for item in data["items"][:max_results]]
            )
        return None
    except Exception:
        return None

def get_weather(location):
    """Get live weather via Open-Meteo"""
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1").json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()
        temp = w["current_weather"]["temperature"]
        wind = w["current_weather"]["windspeed"]
        return f"🌤️ {location} का वर्तमान तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None

def ask_gemini(prompt):
    """Ask Gemini for smart reasoning"""
    for model_name in ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if hasattr(res, "text") and res.text:
                return res.text.strip()
        except Exception:
            continue
    return None

def get_live_cricket():
    """Fetch live cricket matches using RapidAPI (Cricbuzz)"""
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY or "",
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        }
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        matches = []
        for section in data.get("typeMatches", []):
            for match_series in section.get("seriesMatches", []):
                if "seriesAdWrapper" in match_series:
                    for game in match_series["seriesAdWrapper"].get("matches", []):
                        info = game.get("matchInfo", {})
                        team1 = info.get("team1", {}).get("teamSName", "")
                        team2 = info.get("team2", {}).get("teamSName", "")
                        venue = info.get("venueInfo", {}).get("ground", "Unknown")
                        status = info.get("status", "No status available")
                        if team1 and team2:
                            matches.append(f"🏏 {team1} vs {team2}\n📍 {venue}\n📊 {status}")
        return matches[:5] if matches else None
    except Exception:
        return None

# -------------------------
# Routes
# -------------------------

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running successfully!"}

@app.get("/status")
async def status():
    return {
        "gemini_key": bool(GEMINI_API_KEY),
        "google_search": bool(GOOGLE_SEARCH_API_KEY),
        "rapidapi_key": bool(RAPIDAPI_KEY),
        "status": "active",
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = req.message.strip()
    lower = user_text.lower()

    # ----------------- News -----------------
    if any(w in lower for w in ["news", "खबर", "समाचार", "headline", "आज की खबर"]):
        news = google_news_hindi_top5()
        if news:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(news)])}
        return {"reply": "⚠️ खबरें प्राप्त नहीं हो सकीं।"}

    # ----------------- Weather -----------------
    if "weather" in lower or "मौसम" in lower:
        loc = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        info = get_weather(loc)
        return {"reply": info or "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # ----------------- Cricket -----------------
    if any(w in lower for w in ["cricket", "match", "t20", "odi", "ipl", "series", "score", "fixture", "result"]):
        matches = get_live_cricket()
        if matches:
            return {"reply": "\n\n".join(matches)}

        # No live match → use web search
        refined_query = user_text + " site:espncricinfo.com OR site:cricbuzz.com OR site:bbc.com/sport/cricket"
        snippets = google_search_snippets(refined_query)
        if snippets:
            prompt = f"""
User Question: {user_text}
Date: {datetime.now().strftime('%d %B %Y')}
Latest Web Info:
{snippets}

You are a sports journalist.
👉 Extract match result, teams, venue & winner if available.
👉 Reply clearly, short, factual.
Format:
Hindi: <result in Hindi>
English: <result in English>
"""
            answer = ask_gemini(prompt)
            return {"reply": answer or f"⚠️ कोई स्पष्ट परिणाम नहीं मिला।\n\n🔍 उपलब्ध डेटा:\n{snippets}"}
        return {"reply": "⚠️ कोई लाइव या हालिया मैच डेटा नहीं मिला।"}

    # ----------------- Location / Collector / Govt -----------------
    if any(w in lower for w in ["collector", "district", "city", "state", "राज्य", "जिला", "कलेक्टर", "शहर"]):
        query = (
            user_text
            + " site:rajasthan.gov.in OR site:wikipedia.org OR site:timesofindia.indiatimes.com"
        )
        snippets = google_search_snippets(query)
        if snippets:
            prompt = f"""
User Question: {user_text}
Date: {datetime.now().strftime('%d %B %Y')}
Online Data:
{snippets}

You are a factual assistant.
👉 Extract the current official name clearly.
👉 Output bilingual:
Hindi: <answer in Hindi>
English: <answer in English>
"""
            answer = ask_gemini(prompt)
            return {"reply": answer or f"⚠️ स्पष्ट उत्तर नहीं मिला।\n\n🔍 स्रोत:\n{snippets}"}

    # ----------------- General Search -----------------
    snippets = google_search_snippets(user_text)
    prompt = f"""
User Question: {user_text}
Today's Date: {datetime.now().strftime('%d %B %Y')}
Recent Online Info:
{snippets}

You are ChatGPT-like AI.
Give current, factual answer in Hindi if question is in Hindi, otherwise English.
Be brief and clear.
"""
    answer = ask_gemini(prompt)
    return {"reply": answer or f"⚠️ मैं सटीक उत्तर नहीं ढूंढ सकी।\n\n🔍 उपलब्ध डेटा:\n{snippets}"}


# -------------------------
# Run Locally
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
