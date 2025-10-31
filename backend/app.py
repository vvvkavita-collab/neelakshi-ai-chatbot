# backend/app.py
# Neelakshi AI Chatbot — Real-time version
# - CricAPI for live cricket (if CRICAPI_KEY present)
# - Google Custom Search for live web results
# - Gemini for summarization and friendly replies
# - Feedparser for Hindi news

import os
import requests
import feedparser
from dotenv import load_dotenv
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Gemini client import (google-generativeai)
# Make sure google-generativeai is installed in your environment.
import google.generativeai as genai

load_dotenv()  # local development; Render uses environment variables

# -------------------------
# Environment / Keys
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
CRICAPI_KEY = os.getenv("CRICAPI_KEY")  # optional but recommended for live cricket

# Require Gemini for AI summarization (we can still respond without it, but it's best)
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY missing — set it in Render / .env")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------
# FastAPI init & CORS
# -------------------------
app = FastAPI(title="Neelakshi AI Chatbot - Real-time Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production: restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# -------------------------
# Helper: Google Custom Search snippets
# -------------------------
def google_search_snippets(query: str, max_results: int = 3) -> str | None:
    """Return compact combined snippets from Google Custom Search (or None)."""
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
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if not data or "items" not in data:
            return None
        parts = []
        for item in data["items"][:max_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            parts.append(f"{title}. {snippet} (Link: {link})")
        return "\n".join(parts)
    except Exception:
        return None

# -------------------------
# Helper: Google News (Hindi) top 5
# -------------------------
def google_news_hindi_top5() -> list | None:
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]] if feed.entries else None
    except Exception:
        return None

# -------------------------
# Helper: Gemini summarizer (tries safe model list)
# -------------------------
def ask_gemini(prompt: str) -> str | None:
    """Ask Gemini and return text, or None on failure."""
    model_names = [
        "models/gemini-2.5-flash",  # try better models first (if available)
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash",
    ]
    last_exc = None
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            resp = model.generate_content(prompt)
            # prefer .text
            if hasattr(resp, "text") and resp.text:
                return resp.text
            # fallback to string
            return str(resp)
        except Exception as e:
            last_exc = e
            continue
    # log last_exc to server logs for debugging
    if last_exc:
        print("Gemini error:", repr(last_exc))
    return None

# -------------------------
# Helper: CricAPI live match & score
# Uses cricapi.com endpoints (common free provider). Requires CRICAPI_KEY.
# Endpoints (legacy cricapi):
#   /api/matches?apikey=KEY
#   /api/cricketScore?apikey=KEY&unique_id=ID
# If your provider uses different endpoints, update these functions accordingly.
# -------------------------
def cricapi_get_matches() -> dict | None:
    if not CRICAPI_KEY:
        return None
    try:
        url = "https://cricapi.com/api/matches"
        params = {"apikey": CRICAPI_KEY}
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        return data
    except Exception:
        return None

def cricapi_get_score(unique_id: str) -> dict | None:
    if not CRICAPI_KEY or not unique_id:
        return None
    try:
        url = "https://cricapi.com/api/cricketScore"
        params = {"apikey": CRICAPI_KEY, "unique_id": unique_id}
        r = requests.get(url, params=params, timeout=8)
        return r.json()
    except Exception:
        return None

def find_live_cricket_info(query: str) -> str | None:
    """Try to locate a live match related to query, return formatted string or None."""
    matches_data = cricapi_get_matches()
    if not matches_data or "matches" not in matches_data:
        return None

    # normalize query
    q_lower = query.lower()
    # look for matches where team names appear in query or match title
    for m in matches_data["matches"]:
        # typical fields: 'team-1', 'team-2', 'squad', 'unique_id', 'matchStarted', 'type', 'date'
        t1 = (m.get("team-1") or "").lower()
        t2 = (m.get("team-2") or "").lower()
        title = (m.get("type") or "") + " " + (m.get("date") or "")
        # If query mentions either team or both
        if (t1 and t1 in q_lower) or (t2 and t2 in q_lower) or (t1 and t2 and (t1 in q_lower or t2 in q_lower)):
            unique_id = m.get("unique_id")
            # If matchStarted true, try for live score
            if m.get("matchStarted") and unique_id:
                score = cricapi_get_score(unique_id)
                if score:
                    # returns fields like 'score', 'stat', 'team-1', etc. Format as user-friendly.
                    score_text = score.get("score") or score.get("stat") or str(score)
                    # Build location/time from matches data
                    venue = m.get("venue") or m.get("date") or ""
                    status = m.get("matchStarted")
                    out = f"🏏 {m.get('team-1')} vs {m.get('team-2')}\n"
                    if venue: out += f"📍 {venue}\n"
                    out += f"🟢 Live: {score_text}\n"
                    return out
            else:
                # upcoming or scheduled
                date = m.get("date") or ""
                typ = m.get("type") or ""
                venue = m.get("venue") or ""
                return f"📅 Scheduled: {m.get('team-1')} vs {m.get('team-2')}\nType: {typ}\nDate/Time: {date}\nVenue: {venue}\n(Match not started or no live score available yet.)"
    return None

# -------------------------
# API Routes
# -------------------------
@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend running ✅"}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        return {"reply": "कृपया कुछ टाइप करें।"}

    lower = user_text.lower()

    # 1) Top Hindi news quick path
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            reply = "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            return {"reply": reply}
        # fallback continue to web search if no feed
        # (we don't return here, proceed to search below)

    # 2) Cricket-specific path: try CricAPI first if query looks crickety
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "score", "series", "vs", "v/s"]):
        # try cricapi quick lookup
        cric_result = find_live_cricket_info(user_text)
        if cric_result:
            return {"reply": cric_result}
        # if cricapi didn't return anything, fall through to web search+gemini

    # 3) Weather quick path (use open-meteo geocoding)
    if "weather" in lower or "मौसम" in lower:
        # extract location phrase simply
        words = lower.replace("weather", "").replace("मौसम", "").strip()
        location = words if words else "Delhi"
        try:
            geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=6).json()
            if "results" in geo and geo["results"]:
                lat = geo["results"][0]["latitude"]
                lon = geo["results"][0]["longitude"]
                weather = requests.get(
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
                    timeout=6
                ).json()
                cw = weather.get("current_weather", {})
                temp = cw.get("temperature")
                wind = cw.get("windspeed")
                if temp is not None:
                    return {"reply": f"🌤️ {location.title()} का तापमान {temp}°C और हवा की गति {wind} km/h है।"}
        except Exception:
            pass
        # fallback to web search below if above failed

    # 4) General live search: refine by topic to prefer authoritative sources
    refined_query = user_text
    if any(word in lower for word in ["cricket", "score", "t20", "odi", "ipl"]):
        refined_query += " site:espncricinfo.com OR site:cricbuzz.com"
    elif any(word in lower for word in ["district", "collector", "dm", "district collector", "जिला", "कलेक्टर", "collector"]):
        refined_query += " site:india.gov.in OR site:wikipedia.org OR site:rajasthan.gov.in"
    elif any(word in lower for word in ["weather", "मौसम"]):
        refined_query += " site:open-meteo.com OR site:weather.com OR site:accuweather.com"

    snippets = google_search_snippets(refined_query, max_results=3)
    if snippets:
        # craft a prompt instructing Gemini to summarize and include sources and date
        prompt = (
            f"User question: {user_text}\n"
            f"Today's date: {datetime.utcnow().strftime('%d %B %Y (UTC)')}\n\n"
            f"Recent web search results (from Google custom search):\n{snippets}\n\n"
            "Using the above, write a clear, current, fact-based answer. "
            "If the web results are not recent or are ambiguous, say so. "
            "Answer in Hindi if the question looks Hindi, otherwise in English. "
            "Also include the most relevant source link(s) at the end."
        )
        gemini_answer = ask_gemini(prompt)
        if gemini_answer:
            return {"reply": gemini_answer}
        # fallback to sending raw snippets if Gemini not available
        return {"reply": "Here's what I found online:\n\n" + snippets}

    # 5) Final fallback: direct Gemini reasoning (no web)
    prompt = f"User asked: {user_text}\nAnswer concisely and clearly."
    gemini_answer = ask_gemini(prompt)
    if gemini_answer:
        return {"reply": gemini_answer}

    return {"reply": "⚠️ मैं इस समय सटीक जानकारी प्राप्त नहीं कर पा रहा/रही हूँ। कृपया बाद में आज़माएँ।"}

# -------------------------
# Run on local / Render uses uvicorn automatically
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
