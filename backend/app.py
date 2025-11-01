# app.py
# Neelakshi AI Chatbot - unified real-time backend
# Uses: Google Custom Search, Google News RSS (Hindi), Open-Meteo, RapidAPI (Cricbuzz), Gemini summarization
# Env variables required (set locally in .env or in Render secrets):
#   GEMINI_API_KEY
#   GOOGLE_SEARCH_API_KEY
#   GOOGLE_SEARCH_ENGINE_ID
#   RAPIDAPI_KEY   (optional - required only for live cricket)
# Install requirements in requirements.txt below.

import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# try to import google generative AI client
try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    genai = None
    HAS_GENAI = False

# Load .env (for local testing)
load_dotenv()

# ---------- Environment ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # optional

# configure genai if available and key present
if HAS_GENAI and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        # continue without raising here to keep service alive; ask_gemini will handle
        pass

# ---------- FastAPI ----------
app = FastAPI(title="Neelakshi AI Chatbot - Real-time backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # narrow this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# ---------- Helpers ----------

def google_news_hindi_top5():
    """Return list of top 5 Hindi headlines (Google News RSS)."""
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]] if feed and feed.entries else None
    except Exception:
        return None

def google_search_snippets(query: str, max_results: int = 3):
    """Return a combined snippet string using Google Custom Search (if keys present)."""
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
    """Return simple weather string using Open-Meteo geocoding + current weather."""
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
        return f"🌤️ {location.title()} का वर्तमान तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None

def get_live_cricket_rapidapi():
    """Fetch live matches from Cricbuzz RapidAPI (if RAPIDAPI_KEY provided)."""
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
        # Parse like earlier code: gather first few matches
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
                            matches.append({
                                "teams": f"{team1} vs {team2}",
                                "venue": venue,
                                "status": status
                            })
        return matches[:5] if matches else None
    except Exception:
        return None

def ask_gemini(prompt: str):
    """Ask Gemini models (if available) and return text or None."""
    if not HAS_GENAI or not GEMINI_API_KEY:
        return None
    # try a list of likely supported models; be defensive.
    candidates = ["models/gemini-2.5-flash", "models/gemini-2.1", "models/gemini-2.0-flash", "models/gemini-1.5-flash"]
    last_err = None
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # many SDK shapes: .text, .choices etc.
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            if hasattr(response, "choices") and response.choices:
                first = response.choices[0]
                # try to extract message/content
                if hasattr(first, "message") and getattr(first.message, "content", None):
                    return first.message.content
                return str(first)
            return str(response)
        except Exception as e:
            last_err = e
            continue
    # as last resort return None
    return None

def make_bilingual(hindi_text: str = None, english_text: str = None):
    """Return combined bilingual answer (prefer Hindi then English)."""
    if hindi_text and english_text:
        return f"Hindi: {hindi_text}\n\nEnglish: {english_text}"
    if hindi_text:
        return f"Hindi: {hindi_text}"
    if english_text:
        return f"English: {english_text}"
    return None

# ---------- Routes ----------

@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running."}

@app.get("/status")
async def status():
    return {
        "gemini": bool(HAS_GENAI and GEMINI_API_KEY),
        "google_search": bool(GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID),
        "rapidapi_cricket": bool(RAPIDAPI_KEY),
        "time": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    lower = user_text.lower()

    # 1. News requests (Hindi top 5)
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])}
        return {"reply": "⚠️ फिलहाल खबरें प्राप्त नहीं हो सकीं।"}

    # 2. Weather
    if "weather" in lower or "मौसम" in lower:
        # extract location roughly
        loc = user_text.replace("weather", "").replace("मौसम", "").strip()
        loc = loc if loc else "Delhi"
        w = get_weather(loc)
        if w:
            return {"reply": w}
        return {"reply": "⚠️ मौसम की जानकारी प्राप्त नहीं हो सकी। कृपया स्थान स्पष्ट करें।"}

    # 3. Cricket / live scores / schedule
    if any(w in lower for w in ["cricket", "match", "t20", "odi", "score", "series", "fixture", "ipl"]):
        # Try live RapidAPI first (if configured)
        live = get_live_cricket_rapidapi()
        if live:
            # format succinctly
            formatted = []
            for m in live:
                formatted.append(f"🏏 {m['teams']}\n📍 {m['venue']}\n📊 {m['status']}")
            return {"reply": "\n\n".join(formatted)}

        # Fallback: use Google Search + Gemini to extract result/schedule
        refined = user_text + " site:espncricinfo.com OR site:cricbuzz.com OR site:bbc.com/sport/cricket"
        snippets = google_search_snippets(refined, max_results=4)
        if snippets:
            prompt = (
                f"You are a knowledgeable cricket reporter. Extract the most relevant live/fixture/result info for the user's query.\n\n"
                f"User question: {user_text}\n"
                f"Latest web snippets:\n{snippets}\n\n"
                "Answer briefly. Provide bilingual output: Hindi then English. If multiple matches, list the most relevant ones."
            )
            ans = ask_gemini(prompt)
            if ans:
                return {"reply": ans}
            return {"reply": "🔍 रिजल्ट: " + snippets}
        return {"reply": "⚠️ लाइव या हालिया क्रिकेट जानकारी नहीं मिली।"}

    # 4. Government / collector / district / local authority queries
    if any(w in lower for w in ["collector", "जिला", "कलेक्टर", "district", "collector of", "who is collector", "who is the collector"]):
        # refine search to official/local sites
        # include the user_text and favor government sites
        q = f"{user_text} site:gov.in OR site:nic.in OR site:wikipedia.org"
        snippets = google_search_snippets(q, max_results=4)
        if snippets:
            prompt = (
                f"You are a fact-checker. Extract the current official name (if any) from the snippets below.\n\n"
                f"User: {user_text}\n\n"
                f"Snippets:\n{snippets}\n\n"
                "If you find a clear current name, output EXACTLY in this format:\nHindi: <short answer>\nEnglish: <short answer>\n\nIf you cannot confidently determine, say so clearly in both languages and list the most recent candidate sources."
            )
            ans = ask_gemini(prompt)
            if ans:
                return {"reply": ans}
            return {"reply": "🔍 उपलब्ध स्रोत:\n" + snippets}
        return {"reply": "⚠️ इस विषय पर पर्याप्त सार्वजनिक जानकारी उपलब्ध नहीं है।"}

    # 5. General search -> use Google search snippets then Gemini summarization
    snippets = google_search_snippets(user_text, max_results=4)
    prompt = (
        f"User question: {user_text}\n"
        f"Today's date: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"Recent web information (if any):\n{snippets}\n\n"
        "Answer concisely. If the user asked in Hindi, reply in Hindi (and include English). If in English, reply in English (and include Hindi)."
    )
    gemini_ans = ask_gemini(prompt)
    if gemini_ans:
        return {"reply": gemini_ans}

    # final fallback
    if snippets:
        return {"reply": "🔍 उपलब्ध जानकारी:\n" + snippets}
    return {"reply": "⚠️ मुझे अभी उत्तर उपलब्ध नहीं है — कृपया प्रश्न और अधिक स्पष्ट करें या बाद में पुनः प्रयास करें।"}
