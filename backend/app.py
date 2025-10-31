# ============================================
# ✅ Neelakshi AI Chatbot – Real-time & Smart version
# Combines:
#   - Hindi News (RSS)
#   - Live Cricket (CricAPI)
#   - Live Web via Google Custom Search
#   - Gemini AI summarization
#   - Weather API (Open-Meteo)
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
import re
import html

# Load .env locally; Render uses environment variables
load_dotenv()

# Environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
CRICKET_API_KEY = os.getenv("CRICKET_API_KEY")  # optional: cricapi.com key

if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY missing. Add it in environment variables.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# FastAPI init
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
# Helpers
# -------------------------
def google_search_snippets(query, max_results=3):
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_SEARCH_ENGINE_ID, "q": query, "num": max_results}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if "items" in data:
            return " \n".join([f"{item.get('title','')}: {item.get('snippet','')}" for item in data["items"][:max_results]])
    except Exception:
        return None
    return None

def google_news_hindi_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None

def ask_gemini(prompt):
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
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=6).json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=6
        ).json()
        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]
        return f"🌤️ {location} का तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None

# ------------ Cricket helpers ------------
def normalize_team_name(s: str):
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()

def parse_match_teams(user_text: str):
    """
    Try to extract 'TeamA vs TeamB' or 'TeamA v TeamB' pattern.
    Returns tuple (teamA, teamB) or (None, None).
    """
    text = user_text.replace("vs.", "vs").replace("v.", "v")
    # common separators: vs, v, versus
    m = re.search(r'([A-Za-z ]{2,50})\s+(?:vs|v|versus|vs\.|v\.)\s+([A-Za-z ]{2,50})', text, flags=re.I)
    if m:
        a = m.group(1).strip()
        b = m.group(2).strip()
        return a, b
    return None, None

def get_live_cricket_from_cricapi(query_teamA, query_teamB):
    """
    Use CricAPI (if key provided) to find matches that contain both teams (case-insensitive).
    Returns formatted string or None.
    """
    if not CRICKET_API_KEY:
        return None
    try:
        # get list of matches
        resp = requests.get("https://cricapi.com/api/matches", params={"apikey": CRICKET_API_KEY}, timeout=8)
        data = resp.json()
        matches = data.get("matches") or data.get("data") or []
        teamA_norm = normalize_team_name(query_teamA)
        teamB_norm = normalize_team_name(query_teamB)
        # find the best match
        for m in matches:
            # look in 'team-1', 'team-2', 'team1', 'team2', 'squad', 'title' etc.
            title = " ".join([str(m.get(k, "")) for k in ["team-1", "team-2", "team1", "team2", "squad", "title"]])
            title_norm = normalize_team_name(title)
            if teamA_norm in title_norm and teamB_norm in title_norm:
                # get unique id to fetch score
                uid = m.get("unique_id") or m.get("uniqueId") or m.get("id")
                # get score
                if uid:
                    score_resp = requests.get("https://cricapi.com/api/cricketScore", params={"apikey": CRICKET_API_KEY, "unique_id": uid}, timeout=8)
                    score_data = score_resp.json()
                    # format
                    desc = score_data.get("description") or score_data.get("score") or score_data.get("stat") or ""
                    match = m.get("date") or m.get("dateTimeGMT") or ""
                    venue = m.get("venue") or m.get("place") or ""
                    title_text = m.get("title") or title
                    out = f"🏏 {html.escape(title_text)}\n📍 {venue}\n{desc}"
                    return out
        return None
    except Exception:
        return None

# ----------------------------------------

# -------------------------
# Routes
# -------------------------
@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        return {"reply": "कृपया कुछ टाइप करें।"}

    lower = user_text.lower()

    # Top Hindi News
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline", "आज की खबर"]):
        headlines = google_news_hindi_top5()
        if headlines:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])}
        return {"reply": "⚠️ फिलहाल खबरें प्राप्त नहीं हो सकीं।"}

    # Weather Queries
    if "weather" in lower or "मौसम" in lower:
        words = lower.replace("weather", "").replace("मौसम", "").strip()
        location = words if words else "Delhi"
        weather_info = get_weather_for(location)
        if weather_info:
            return {"reply": weather_info}
        return {"reply": "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # Cricket / Live / Match related: first try to parse explicit teams
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "series", "score", "vs", "v", "versus"]):
        teamA, teamB = parse_match_teams(user_text)
        # if we detected two teams explicitly, prefer cricket API exact match
        if teamA and teamB:
            # try API first
            api_result = get_live_cricket_from_cricapi(teamA, teamB)
            if api_result:
                return {"reply": api_result}
            # if API not available / no match, use exact-phrase Google search
            exact_phrase = f"\"{teamA} vs {teamB}\" site:espncricinfo.com OR site:cricbuzz.com"
            snippets = google_search_snippets(exact_phrase, max_results=3)
            if snippets:
                # ask Gemini to condense
                prompt = (
                    f"User question: {user_text}\n\n"
                    f"Exact-match web search results:\n{snippets}\n\n"
                    "Provide a short, factual live match answer (score, venue, status). If uncertain, say 'No live match found'."
                )
                gemini_reply = ask_gemini(prompt)
                if gemini_reply:
                    return {"reply": gemini_reply}
                return {"reply": f"Here's what I found matched exact phrase:\n{snippets}"}
            # fallback: broad cricket search
            refined_query = user_text + " site:espncricinfo.com OR site:cricbuzz.com"
        else:
            # no explicit teams parsed; do generic cricket site search
            refined_query = user_text + " site:espncricinfo.com OR site:cricbuzz.com"

        # do google search for refined query
        snippets = google_search_snippets(refined_query)
        if snippets:
            prompt = (
                f"User question: {user_text}\nToday's date: {datetime.now().strftime('%d %B %Y')}\n"
                f"Recent cricket web info:\n{snippets}\n\nAnswer concisely with score/status/venue if possible."
            )
            gemini_reply = ask_gemini(prompt)
            if gemini_reply:
                return {"reply": gemini_reply}
            return {"reply": f"Here's what I found online:\n{snippets}"}

    # Elections
    if any(word in lower for word in ["election", "vote", "result", "नतीजे", "चुनाव"]):
        refined_query = user_text + " site:indiatoday.in OR site:ndtv.com"
        snippets = google_search_snippets(refined_query)
        if snippets:
            prompt = f"User: {user_text}\nWeb results:\n{snippets}\nAnswer briefly."
            gemini_reply = ask_gemini(prompt)
            if gemini_reply:
                return {"reply": gemini_reply}
            return {"reply": snippets}

    # Location / City / State / Official queries
    if any(word in lower for word in ["district", "city", "state", "location", "area", "जिला", "शहर", "राज्य", "collector", "dm"]):
        # attempt to prefer government/wikipedia sites
        refined_query = user_text + " site:india.gov.in OR site:wikipedia.org OR site:gov.in"
        snippets = google_search_snippets(refined_query)
        if snippets:
            prompt = f"User: {user_text}\nWeb results:\n{snippets}\nPlease answer with the most authoritative info (gov sources) and mention source."
            gemini_reply = ask_gemini(prompt)
            if gemini_reply:
                return {"reply": gemini_reply}
            return {"reply": snippets}

    # General online search (fallback)
    refined_query = user_text
    snippets = google_search_snippets(refined_query)
    if snippets:
        prompt = (
            f"User question: {user_text}\nToday's date: {datetime.now().strftime('%d %B %Y')}\n"
            f"Recent online information:\n{snippets}\n\nAnswer in clear Hindi/English as appropriate."
        )
        gemini_reply = ask_gemini(prompt)
        if gemini_reply:
            return {"reply": gemini_reply}
        return {"reply": f"Here's what I found online:\n{snippets}"}

    # Final fallback: Gemini alone
    prompt = f"User asked: {user_text}\nAnswer clearly and helpfully in Hindi/English as per the question."
    gemini_reply = ask_gemini(prompt)
    if gemini_reply:
        return {"reply": gemini_reply}

    return {"reply": "⚠️ मैं इस समय सटीक जानकारी प्राप्त नहीं कर पा रही हूँ। कृपया बाद में प्रयास करें।"}

# For Render / local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))


