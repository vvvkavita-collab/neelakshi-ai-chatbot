import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Gemini LLM
try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

# Astrology package for predictions (pip install flatlib)
try:
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib.const import SIDEREAL
    HAS_ASTRO = True
except Exception:
    HAS_ASTRO = False

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

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

def wikipedia_lookup(query):
    try:
        resp = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_"), timeout=5)
        data = resp.json()
        if data.get("extract"):
            return data["extract"]
        return None
    except Exception:
        return None

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

def astro_prediction(name, dob, tob, pob):
    """Example astrology function using flatlib (needs improvement for advanced astrology!)"""
    try:
        # dob (YYYY-MM-DD), tob (HH:MM), pob (city)
        dt = Datetime(dob + ' ' + tob, 'UTC')
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={pob}&count=1").json()
        if "results" in geo and geo["results"]:
            city = geo["results"][0]
            pos = GeoPos(city["latitude"], city["longitude"])
            chart = Chart(dt, pos, hsys='P', IDs=SIDEREAL)
            sunSign = chart.get("SUN").sign
            return f"{name}, aapki janm rashi {sunSign} hai. (Detailed astrology needs more custom code.)"
        return "Location not found for astrology."
    except Exception as e:
        return f"Astro error: {e}"

def ask_gemini(messages):
    if not (HAS_GENAI and GEMINI_API_KEY):
        return None
    chat_format = []
    for m in messages:
        # Support both Pydantic obj and dict
        if hasattr(m, "role") and hasattr(m, "content"):
            chat_format.append({"role": m.role, "parts": [m.content]})
        elif isinstance(m, dict) and "role" in m and "content" in m:
            chat_format.append({"role": m["role"], "parts": [m["content"]]})
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
            req.messages.append({"role": "model", "content": w})
            ans = ask_gemini(req.messages)
            return {"reply": ans or w}

    # Cricket
    if any(x in user_msg for x in ["cricket", "t20", "odi", "ipl", "match", "score"]):
        live = get_live_cricket_rapidapi()
        if live:
            cricket_info = "\n\n".join(live)
            req.messages.append({"role": "model", "content": cricket_info})
            ans = ask_gemini(req.messages)
            return {"reply": ans or cricket_info}

    # News
    if "news" in user_msg or "खबर" in user_msg or "समाचार" in user_msg:
        headlines = google_news_top5()
        if headlines:
            news = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            req.messages.append({"role": "model", "content": news})
            ans = ask_gemini(req.messages)
            return {"reply": ans or news}

    # Astrology
    if any(x in user_msg for x in ["kundli", "janam", "birth chart", "future", "astrology", "prediction", "rashi", "zodiac"]):
        # Example: extract dob, tob, pob from history
        dob, tob, pob, name = None, None, None, "User"
        for m in req.messages:
            text = m.content.lower()
            if "dob" in text or "date" in text:
                # Try to extract like "dob: 1990-01-01" (very basic)
                for part in text.split():
                    if part.count('-') == 2:
                        dob = part
            if "time" in text or "tob" in text:
                # Look for "time: 09:00"
                for part in text.split():
                    if ':' in part:
                        tob = part
            if "jaipur" in text or "delhi" in text or "pob" in text:
                pob = "jaipur" if "jaipur" in text else "delhi"
        if ALL_VARS := (dob and tob and pob):
            astro = astro_prediction(name, dob, tob, pob)
            req.messages.append({"role": "model", "content": astro})
            ans = ask_gemini(req.messages)
            return {"reply": ans or astro}
        # Else, answer by Gemini intelligence only ("past, present, future")
        ans = ask_gemini(req.messages)
        return {"reply": ans or "Please provide DOB, time, and place for detailed
