# backend/app.py
"""
Neelakshi AI Chatbot - Real-time backend
Features:
 - Top-5 Hindi news via Google News RSS
 - Live web results via Google Custom Search (Programmable Search)
 - Optional live cricket via RapidAPI Cricbuzz (if RAPIDAPI_KEY provided)
 - Weather via Open-Meteo
 - Reasoning / Natural-language answers via Google Gemini (google-generativeai SDK)
 - Single endpoint: POST /chat  ->  JSON { "message": "..." }  -> { "reply": "..." }
"""

import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Try to import google.generativeai the standard way
try:
    import google.generativeai as genai
except Exception:
    genai = None  # We'll handle missing / misconfigured Gemini gracefully

# Load environment variables from .env during local dev (Render uses Environment)
load_dotenv()

# Environment / keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").strip()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()  # optional for cricket
# Note: If you do NOT have RAPIDAPI_KEY, cricket will attempt to use web search.

# Configure Gemini if available
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        # ignore configure failure, handled later
        pass

# FastAPI init
app = FastAPI(title="Neelakshi AI Chatbot - Real-time Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production replace * with your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str

# ---------------- HELPER FUNCTIONS ----------------

def google_news_hindi_top5():
    """Return list of top-5 Hindi headlines (Google News RSS)"""
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        headlines = [entry.title for entry in feed.entries[:5]]
        return headlines if headlines else None
    except Exception:
        return None

def google_search_snippets(query: str, max_results: int = 3):
    """Call Google Custom Search (Programmable Search) and return small snippet text.
    Requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID.
    """
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
            parts = []
            for it in data["items"][:max_results]:
                title = it.get("title", "")
                snip = it.get("snippet", "")
                link = it.get("link", "")
                parts.append(f"{title}: {snip} (Link: {link})")
            return "\n\n".join(parts)
        return None
    except Exception:
        return None

def get_weather_for(location: str):
    """Return simple current weather from Open-Meteo for a location string."""
    try:
        if not location:
            return None
        geo_resp = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(location)}&count=1", timeout=6)
        geo = geo_resp.json()
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
    """Ask Gemini (if configured). Returns text or None.
    Tries multiple model names and handles missing SDK/key gracefully.
    """
    if genai is None or not GEMINI_API_KEY:
        return None
    if model_candidates is None:
        model_candidates = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-1.5-flash",
        ]
    last_err = None
    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            # The generate_content call returns an object with .text in many setups
            response = model.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text
            # Some SDK shapes may differ — fallback to string
            return str(response)
        except Exception as e:
            last_err = e
            continue
    # all failed
    return None

def get_live_cricket_rapidapi(limit=3):
    """Get live matches using a RapidAPI Cricbuzz endpoint (if RAPIDAPI_KEY provided)"""
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
        # RapidAPI cricbuzz structure can be nested; we try to extract basic info
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
    """Fallback: search web for live cricket (espncricinfo / cricbuzz). Returns formatted list or None."""
    # Build a targeted search
    query = f"{user_query} site:espncricinfo.com OR site:cricbuzz.com"
    snippets = google_search_snippets(query, max_results=5)
    if not snippets:
        return None
    # Make a simple attempt to format lines from snippet text (not perfect)
    lines = []
    for line in snippets.split("\n\n")[:limit]:
        # keep it short
        lines.append(line.strip())
    return [{"teams": line, "venue": "", "status": ""} for line in lines] if lines else None

# ---------------- ROUTES ----------------

@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is live — POST /chat with JSON {message}."}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Please provide a message in JSON: { \"message\": \"...\" }")

    lower = user_text.lower()

    # 1) News
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            news_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            return {"reply": f"🗞️ आज की टॉप 5 हिंदी खबरें:\n\n{news_text}"}
        # fallback
        return {"reply": "⚠️ खबरें लोड करने में समस्या आई — कृपया कुछ समय बाद पुनः प्रयास करें।"}

    # 2) Weather
    if "weather" in lower or "मौसम" in lower:
        loc = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        w = get_weather_for(loc)
        return {"reply": w or "⚠️ मौसम डेटा उपलब्ध नहीं। कृपया किसी अन्य स्थान के साथ पुनः प्रयास करें।"}

    # 3) Cricket / Live sports
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "series", "score", "live"]):
        # prefer rapidapi if key present
        matches = get_live_cricket_rapidapi()
        if not matches:
            # fallback to search
            matches = get_live_cricket_search(user_text)
        if matches:
            formatted = []
            for m in matches:
                teams = m.get("teams", "").strip()
                venue = m.get("venue", "")
                status = m.get("status", "")
                block = f"🏏 {teams}\n"
                if venue:
                    block += f"📍 मैदान: {venue}\n"
                if status:
                    block += f"📊 स्थिति: {status}\n"
                formatted.append(block.strip())
            return {"reply": "\n\n".join(formatted)}
        else:
            return {"reply": "⚠️ इस समय लाइव क्रिकेट डेटा उपलब्ध नहीं मिला। आप ESPNcricinfo या Cricbuzz पर विवरण देख सकते हैं."}

    # 4) Location / official / collector / district queries — try targeted sites then Gemini
    if any(word in lower for word in ["collector", "district", "जिला", "कलेक्टर", "collector", "district collector", "mayor", "mp", "mla"]):
        # Build targeted search
        target_sites = "site:gov.in OR site:rajasthan.gov.in OR site:.nic.in OR site:wikipedia.org OR site:timesofindia.indiatimes.com"
        query = f"{user_text} {target_sites}"
        snippets = google_search_snippets(query, max_results=4)
        if snippets:
            prompt = (
                f"User question: {user_text}\n"
                f"Search snippets:\n{snippets}\n\n"
                "Provide a concise factual answer. If there are multiple sources, pick the most recent authoritative source. "
                "Return answer as two short lines: first in Hindi, second in English."
            )
            ai = ask_gemini(prompt)
            if ai:
                return {"reply": ai}
            # fallback to returning snippets
            return {"reply": f"🔍 उपलब्ध जानकारी:\n\n{snippets}"}
        else:
            return {"reply": "⚠️ इस विषय पर ऑनलाइन प्रमाणित जानकारी अभी नहीं मिली।"}

    # 5) General queries: use web search + Gemini summarizer
    snippets = google_search_snippets(user_text, max_results=4)
    # Build master prompt containing date and snippets
    prompt = (
        f"You are Neelakshi AI — a friendly assistant. Today's date: {datetime.now().strftime('%d %B %Y')}.\n\n"
        f"User asked: {user_text}\n\n"
    )
    if snippets:
        prompt += f"Recent web results:\n{snippets}\n\n"
    prompt += (
        "Answer clearly and concisely. If user asked in Hindi, answer in Hindi; otherwise answer in English. "
        "If question requires latest facts (dates, match times, officials), prioritize web snippets. "
        "Keep answer short (max 6 sentences)."
    )

    ai_text = ask_gemini(prompt)
    if ai_text:
        return {"reply": ai_text}

    # Last-resort: return search snippets if Gemini not available or failed
    if snippets:
        return {"reply": f"Here's what I found online:\n\n{snippets}"}

    return {"reply": "⚠️ जानकारी उपलब्ध नहीं। कृपया प्रश्न को थोड़ा अलग शब्दों में पूछें।"}

# Run with: uvicorn app:app --host 0.0.0.0 --port 10000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
