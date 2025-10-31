import os
import requests
import feedparser
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if not GEMINI_API_KEY:
    raise Exception("❌ GEMINI_API_KEY missing in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Neelakshi AI Chatbot – Real-time Backend")

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

def google_search_snippets(query, max_results=3):
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
                [f"{item['title']}: {item['snippet']}" for item in data["items"][:max_results]]
            )
        return None
    except Exception:
        return None

def get_weather(location):
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
    for model_name in ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if hasattr(res, "text") and res.text:
                return res.text
            return str(res)
        except Exception:
            continue
    return None

def get_live_cricket():
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        }
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        matches = []

        for series in data.get("typeMatches", []):
            for match in series.get("seriesMatches", []):
                if "seriesAdWrapper" in match:
                    for game in match["seriesAdWrapper"].get("matches", []):
                        info = game.get("matchInfo", {})
                        teams = info.get("team1", {}).get("teamSName", "") + " vs " + info.get("team2", {}).get("teamSName", "")
                        if info.get("matchDesc"):
                            matches.append({
                                "teams": teams,
                                "venue": info.get("venueInfo", {}).get("ground", "Unknown"),
                                "status": info.get("status", "No status available"),
                            })
        return matches[:3] if matches else None
    except Exception:
        return None

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is active & real-time enabled!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        return {"reply": "कृपया कुछ लिखें।"}

    lower = user_text.lower()

    # Hindi News
    if any(word in lower for word in ["news", "खबर", "headline", "समाचार", "आज की खबर"]):
        headlines = google_news_hindi_top5()
        if headlines:
            return {"reply": "🗞️ आज की टॉप 5 हिंदी खबरें:\n\n" + "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])}
        return {"reply": "⚠️ फिलहाल खबरें लोड नहीं हो सकीं।"}

    # Weather
    if "weather" in lower or "मौसम" in lower:
        city = lower.replace("weather", "").replace("मौसम", "").strip() or "Delhi"
        weather_info = get_weather(city)
        return {"reply": weather_info or "⚠️ मौसम की जानकारी नहीं मिल सकी।"}

    # Cricket
    if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "series", "score"]):
        matches = get_live_cricket()
        if matches:
            formatted = "\n\n".join(
                [f"🏏 {m['teams']}\n📍 मैदान: {m['venue']}\n📊 स्थिति: {m['status']}" for m in matches]
            )
            return {"reply": formatted}
        else:
            return {"reply": "⚠️ इस समय कोई लाइव क्रिकेट डेटा नहीं मिला।"}

    # Location/Government queries
    if any(word in lower for word in ["collector", "district", "state", "city", "राज्य", "जिला", "कलेक्टर", "शहर"]):
        # Optional hardcoded override (only if confident)
        if "जयपुर" in lower and "कलेक्टर" in lower:
            return {"reply": "Hindi: जयपुर के कलेक्टर श्री राजन कुमार सिंह (IAS) हैं।\nEnglish: The Collector of Jaipur is Mr. Rajan Kumar Singh (IAS)."}

        query = user_text + " site:rajasthan.gov.in OR site:wikipedia.org OR site:jaipur.nic.in OR site:timesofindia.indiatimes.com"
        snippets = google_search_snippets(query)
        if snippets:
            prompt = f"""
User asked: {user_text}
Date: {datetime.now().strftime('%d %B %Y')}

Below is the latest online info:
{snippets}

You are a fact-based AI assistant.
👉 If the data mentions a person’s name or post (like Collector, CM, etc.), give a **clear and confident** one-line answer.
👉 If multiple sources exist, pick the **most recent & logical** one.
👉 Output must be in this exact format:

Hindi: <short Hindi answer>  
English: <short English answer>
"""
            answer = ask_gemini(prompt)
            return {"reply": answer or f"⚠️ स्पष्ट उत्तर नहीं मिला।\n\n🔍 उपलब्ध जानकारी:\n{snippets}"}
        else:
            return {"reply": "⚠️ कोई जानकारी प्राप्त नहीं हुई।"}

    # General queries
    snippets = google_search_snippets(user_text)
    prompt = (
        f"User question: {user_text}\n"
        f"Today's date: {datetime.now().strftime('%d %B %Y')}\n"
        f"Recent online info: {snippets}\n\n"
        "Give an accurate, up-to-date answer. Use Hindi if question is Hindi."
    )
    answer = ask_gemini(prompt)
    return {"reply": answer or f"⚠️ इस समय जानकारी उपलब्ध नहीं है।\n\n🔍 उपलब्ध जानकारी:\n{snippets}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
