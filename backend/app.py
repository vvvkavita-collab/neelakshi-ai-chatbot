import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------
# Load environment
# ----------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not GEMINI_API_KEY:
    raise Exception("❌ GEMINI_API_KEY missing in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# ----------------------------
# FastAPI app setup
# ----------------------------
app = FastAPI(title="Neelakshi AI Chatbot – Smart & Real-time")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# ----------------------------
# Helper functions
# ----------------------------
def google_news_hindi_top5(region=None):
    """Fetch top Hindi or regional news"""
    try:
        if region:
            region_query = f"https://news.google.com/rss/search?q={region}+समाचार&hl=hi&gl=IN&ceid=IN:hi"
            feed = feedparser.parse(region_query)
        else:
            feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        return [entry.title for entry in feed.entries[:5]]
    except Exception:
        return None

def google_search_snippets(query, max_results=3):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_SEARCH_ENGINE_ID, "q": query, "num": max_results}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        if "items" in data:
            return " ".join([f"{i['title']}: {i['snippet']}" for i in data["items"][:max_results]])
        return None
    except Exception:
        return None

def ask_gemini(prompt):
    """Ask Gemini and return bilingual response if possible"""
    for model_name in ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if hasattr(res, "text") and res.text:
                return res.text.strip()
            return str(res)
        except Exception:
            continue
    return None

def get_weather(location):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1").json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
        temp = w["current_weather"]["temperature"]
        wind = w["current_weather"]["windspeed"]
        return f"🌤️ {location} का तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except Exception:
        return None

def get_live_cricket():
    """Fetch live Team India matches"""
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        }
        res = requests.get(url, headers=headers, timeout=10).json()
        matches = []
        for t in res.get("typeMatches", []):
            for sm in t.get("seriesMatches", []):
                if "seriesAdWrapper" in sm:
                    for m in sm["seriesAdWrapper"].get("matches", []):
                        info = m.get("matchInfo", {})
                        t1 = info.get("team1", {}).get("teamSName", "")
                        t2 = info.get("team2", {}).get("teamSName", "")
                        if "India" in (t1 + t2):
                            matches.append({
                                "teams": f"{t1} vs {t2}",
                                "venue": info.get("venueInfo", {}).get("ground", "Unknown"),
                                "status": info.get("status", "No update yet"),
                            })
        return matches if matches else None
    except Exception:
        return None

def get_upcoming_schedule():
    """Fetch upcoming T20/ODI schedule from Cricbuzz"""
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/upcoming"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        }
        data = requests.get(url, headers=headers, timeout=10).json()
        schedule = []
        for t in data.get("typeMatches", []):
            for sm in t.get("seriesMatches", []):
                if "seriesAdWrapper" in sm:
                    for m in sm["seriesAdWrapper"].get("matches", []):
                        info = m.get("matchInfo", {})
                        t1 = info.get("team1", {}).get("teamSName", "")
                        t2 = info.get("team2", {}).get("teamSName", "")
                        match_format = info.get("matchFormat", "")
                        date = datetime.fromtimestamp(info.get("startDate", 0)/1000.0).strftime("%d %b %Y")
                        if "India" in (t1 + t2):
                            schedule.append(f"🏏 {t1} vs {t2} ({match_format}) - 📅 {date}")
        return schedule[:5] if schedule else None
    except Exception:
        return None

# ----------------------------
# Routes
# ----------------------------
@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend active & smart!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    text = (req.message or "").strip()
    if not text:
        return {"reply": "कृपया कुछ लिखें।"}
    lower = text.lower()

    # 📰 News
    if any(k in lower for k in ["news", "खबर", "समाचार", "headline"]):
        if "rajasthan" in lower or "राजस्थान" in lower:
            headlines = google_news_hindi_top5("राजस्थान")
        else:
            headlines = google_news_hindi_top5()
        if headlines:
            return {"reply": "🗞️ आज की टॉप 5 खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i,h in enumerate(headlines)])}
        return {"reply": "⚠️ फिलहाल खबरें प्राप्त नहीं हो सकीं।"}

    # 🌤️ Weather
    if "weather" in lower or "मौसम" in lower:
        city = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        info = get_weather(city)
        return {"reply": info or "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # 🏏 Cricket
    if "schedule" in lower or "fixture" in lower:
        schedule = get_upcoming_schedule()
        if schedule:
            return {"reply": "📅 आगामी भारत टीम मैच:\n\n" + "\n".join(schedule)}
        return {"reply": "⚠️ कोई आगामी मैच डेटा नहीं मिला।"}

    if any(k in lower for k in ["cricket", "match", "t20", "odi", "ipl", "score", "series"]):
        matches = get_live_cricket()
        if matches:
            formatted = "\n\n".join([f"🏏 {m['teams']}\n📍 मैदान: {m['venue']}\n📊 स्थिति: {m['status']}" for m in matches])
            return {"reply": formatted}
        return {"reply": "⚠️ इस समय कोई लाइव क्रिकेट डेटा उपलब्ध नहीं है।"}

    # 🏛️ Government Info
    if any(w in lower for w in ["collector", "district", "कलेक्टर", "जिला"]):
        if "jaipur" in lower or "जयपुर" in lower:
            return {"reply": "Hindi: जयपुर के जिला कलेक्टर श्री जितेन्द्र कुमार सोनी (IAS) हैं।\nEnglish: The District Collector of Jaipur is Mr. Jitendra Kumar Soni (IAS)."}
        query = text + " site:gov.in OR site:wikipedia.org OR site:timesofindia.indiatimes.com"
        snippets = google_search_snippets(query)
        if snippets:
            prompt = f"User asked: {text}\nToday's date: {datetime.now().strftime('%d %B %Y')}\nWeb info: {snippets}\nGive a short bilingual answer: Hindi + English."
            ans = ask_gemini(prompt)
            return {"reply": ans or f"🔍 उपलब्ध जानकारी:\n{snippets}"}
        return {"reply": "⚠️ कोई सटीक सरकारी जानकारी नहीं मिली।"}

    # 💡 General Queries
    snippets = google_search_snippets(text)
    prompt = f"User: {text}\nDate: {datetime.now().strftime('%d %B %Y')}\nInfo: {snippets}\nProvide a clear, short, fact-based bilingual (Hindi + English) answer."
    ans = ask_gemini(prompt)
    return {"reply": ans or f"⚠️ इस समय जानकारी नहीं मिल सकी।\n\n🔍 उपलब्ध जानकारी:\n{snippets}"}

# ----------------------------
# Render hosting
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
