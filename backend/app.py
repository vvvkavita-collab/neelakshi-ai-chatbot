import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Gemini (Google AI)
try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")   # Optional (cricket only)

if HAS_GENAI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

def google_news_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
        return [entry.title for entry in feed.entries[:5]] if feed and feed.entries else None
    except Exception:
        return None

def google_search_snippets(query: str, max_results: int = 3):
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": max_results
        }
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if "items" in data:
            parts = []
            for item in data["items"][:max_results]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                parts.append(f"{title}. {snippet} (Source: {link})")
            return "\n\n".join(parts)
        return None
    except Exception:
        return None

def get_weather(location: str):
    try:
        if not location:
            return None
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=6).json()
        if "results" not in geo or not geo["results"]:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=6).json()
        cw = w.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        return f"🌤️ {location.title()} ka aaj ka temperature: {temp}°C, wind: {wind} km/h."
    except Exception:
        return None

def get_live_cricket_rapidapi():
    if not RAPIDAPI_KEY:
        return None
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        matches = []
        for section in data.get("typeMatches", []):
            for seriesBlock in section.get("seriesMatches", []):
                if "seriesAdWrapper" in seriesBlock:
                    for game in seriesBlock["seriesAdWrapper"].get("matches", []):
                        info = game.get("matchInfo", {})
                        team1 = info.get("team1", {}).get("teamSName", "")
                        team2 = info.get("team2", {}).get("teamSName", "")
                        venue = info.get("venueInfo", {}).get("ground", "Unknown")
                        status = info.get("status", "Status not available")
                        if team1 and team2:
                            matches.append(f"{team1} vs {team2} at {venue}\nStatus: {status}")
        return matches[:5] if matches else None
    except Exception:
        return None

def ask_gemini(messages):
    if not (HAS_GENAI and GEMINI_API_KEY):
        return None
    chat_format = [{"role": m.role, "parts": [m.content]} for m in messages]
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(chat_format)
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        return str(response)
    except Exception as e:
        return f"❌ Gemini error: {e}"

@app.post("/chat")
def chat(req: ChatRequest):
    user_msg = req.messages[-1].content.lower()

    # Weather
    if "weather" in user_msg or "मौसम" in user_msg:
        loc = user_msg.replace("weather", "").replace("मौसम", "").strip()
        loc = loc if loc else "Delhi"
        w = get_weather(loc)
        if w:
            reply = w + "\n\n(Weather via Open-Meteo live)"
            req.messages.append({"role": "model", "content": reply})
            ans = ask_gemini(req.messages)
            return {"reply": ans or reply}

    # Cricket
    if any(x in user_msg for x in ["cricket", "t20", "odi", "ipl", "match", "score"]):
        live = get_live_cricket_rapidapi()
        if live:
            reply = "\n\n".join(live)
            req.messages.append({"role": "model", "content": reply})
            ans = ask_gemini(req.messages)
            return {"reply": ans or reply}

    # News
    if "news" in user_msg or "खबर" in user_msg or "समाचार" in user_msg:
        headlines = google_news_top5()
        if headlines:
            news = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            req.messages.append({"role": "model", "content": news})
            ans = ask_gemini(req.messages)
            return {"reply": ans or news}

    # Collector/District/Authority queries
    if any(w in user_msg for w in ["collector", "जिला", "कलेक्टर", "district"]):
        q = user_msg + " site:gov.in OR site:nic.in OR site:wikipedia.org"
        snippets = google_search_snippets(q)
        if snippets:
            req.messages.append({"role": "model", "content": snippets})
            ans = ask_gemini(req.messages)
            return {"reply": ans or snippets}

    # General search
    snippets = google_search_snippets(user_msg)
    if snippets:
        req.messages.append({"role": "model", "content": snippets})
        ans = ask_gemini(req.messages)
        return {"reply": ans or snippets}

    # Last fallback: pure LLM answer (training data)
    ans = ask_gemini(req.messages)
    return {"reply": ans or "⚠️ Sorry, abhi is prashn par sahi data nahi mila."}
