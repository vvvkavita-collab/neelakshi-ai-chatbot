import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except Exception:
    genai = None

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").strip()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()

if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

app = FastAPI(title="Neelakshi AI Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def google_news_hindi_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None

def google_search_snippets(query: str, max_results: int = 3):
    if not (GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID):
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": max_results
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if "items" in data:
            return "\n\n".join([
                f"{item.get('title')}: {item.get('snippet')} (Link: {item.get('link')})"
                for item in data["items"][:max_results]
            ])
        return None
    except Exception:
        return None

def get_weather_for(location: str):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=6).json()
        if "results" not in geo or not geo["results"]:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=6).json()
        cw = w.get("current_weather")
        if not cw:
            return None
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        return f"🌤️ {location} का वर्तमान तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None

def ask_gemini(prompt: str, model_candidates=None):
    if genai is None or not GEMINI_API_KEY:
        return None
    if model_candidates is None:
        model_candidates = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-1.5-flash",
            "gemini-pro"
        ]
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text
            return str(response)
        except Exception:
            continue
    return None

def get_live_cricket_rapidapi(limit=3):
    if not RAPIDAPI_KEY:
        return None
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        matches = []
        for group in data.get("typeMatches", []):
            for series in group.get("seriesMatches", []):
                wrapper = series.get("seriesAdWrapper")
                if not wrapper:
                    continue
                for game in wrapper.get("matches", []):
                    info = game.get("matchInfo", {}) or {}
                    team1 = info.get("team1", {}).get("teamSName", "")
                    team2 = info.get("team2", {}).get("teamSName", "")
                    venue = info.get("venueInfo", {}).get("ground", "") or info.get("venue", "")
                    status = info.get("status", "") or info.get("matchDesc", "")
                    if team1 or team2:
                        matches.append({
                            "teams": f"{team1} vs {team2}".strip(),
                            "venue": venue or "Unknown",
                            "status": status or "No status available"
                        })
        return matches[:limit] if matches else None
    except Exception:
        return None

def get_live_cricket_search(user_query, limit=3):
    query = f"{user_query} site:espncricinfo.com OR site:cricbuzz.com"
    snippets = google_search_snippets(query, max_results=5)
    if not snippets:
        return None
    lines = [line.strip() for line in snippets.split("\n\n")[:limit]]
    return [{"teams": line, "venue": "", "status": ""} for line in lines] if lines else None

@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is live — POST /chat with JSON {message}."}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Please provide a message in JSON: { \"message\": \"...\" }")

    lower = user_text.lower()

    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            news_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            return {"reply": f"🗞️ आज की टॉप 5 हिंदी खबरें:\n\n{news_text}"}
        return {"reply": "⚠️ खबरें लोड करने में समस्या आई — कृपया कुछ समय बाद पुनः प्रयास करें।"}

    if "weather" in lower or "मौसम" in lower:
        loc = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        w = get_weather_for(loc)
        return {"reply": w or f"⚠️ {loc} के मौसम की जानकारी नहीं मिल सकी।"}

    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "series", "score", "live"]):
        matches = get_live_cricket_rapidapi()
        if not matches:
            matches = get_live_cricket_search(user_text)
        if matches:
            formatted = []
            for m in matches:
                block = f"🏏 {m.get('teams', '')}"
                if m.get("venue"):
                    block += f"\n📍 मैदान: {m['venue']}"
                if m.get("status"):
                    block += f"\n📊 स्थिति: {m['status']}"
                formatted.append(block.strip())
            return {"reply": "\n\n".join(formatted)}
        return {"reply": "⚠️ इस समय लाइव क्रिकेट डेटा उपलब्ध नहीं मिला।"}

    if any(word in lower for word in ["collector", "district", "जिला", "कलेक्टर", "mayor", "mp", "mla"]):
        query = f"{user_text} site:gov.in OR site:rajasthan.gov.in OR site:.nic.in OR site:wikipedia.org OR site:timesofindia.indiatimes.com"
        snippets = google_search_snippets(query, max_results=4)
        if snippets:
            prompt = (
                f"User question: {user_text}\n"
                f"Search snippets:\n{snippets}\n\n"
                "Provide a concise factual answer. If there are multiple sources, pick the most recent authoritative source. "
                "Return answer as two short lines: first in Hindi, second in English."
            )
