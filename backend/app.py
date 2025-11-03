import os
import requests
import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

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

def get_current_collector(city):
    # Try Wikipedia
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{city}_district"
        r = requests.get(url, timeout=8)
        data = r.json()
        for key in ["collector", "district magistrate", "district magistrate of " + city.lower()]:
            if key in data.get("extract", "").lower():
                return data.get("extract")
    except Exception:
        pass
    # Try Rajasthan Govt official site (scraped)
    try:
        url = "https://jaipur.rajasthan.gov.in/content/raj/jaipur/en/about-jaipur/district-collector.html"
        r = requests.get(url, timeout=8)
        if "District Collector" in r.text:
            start = r.text.find("District Collector")
            snippet = r.text[start:start + 250]
            return snippet.strip()
    except Exception:
        pass
    return None

def get_cm(state):
    # Wikipedia API for the state CM
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/List_of_chief_ministers_of_{state.title()}_(_India_)"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("extract"):
            return data["extract"]
    except Exception:
        pass
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
        return f"{location.title()} ka aaj ka temperature: {temp}°C, wind: {wind} km/h."
    except Exception:
        return None

def google_news_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
        return [entry.title for entry in feed.entries[:5]] if feed and feed.entries else None
    except Exception:
        return None

def ask_gemini(messages):
    if not (HAS_GENAI and GEMINI_API_KEY): return None
    chat_format = []
    for m in messages:
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
        return f"Gemini error: {e}"

@app.post("/chat")
def chat(req: ChatRequest):
    user_msg = req.messages[-1].content.lower().strip()

    # Weather
    if "weather" in user_msg or "मौसम" in user_msg:
        loc = user_msg.replace("weather", "").replace("मौसम", "").strip()
        loc = loc if loc else "Delhi"
        data = get_weather(loc)
        if data:
            req.messages.append({"role": "model", "content": data})
            ans = ask_gemini(req.messages)
            return {"reply": ans or data}

    # CM query
    if "cm" in user_msg or "chief minister" in user_msg:
        for state in ["rajasthan", "up", "uttar pradesh", "mp", "madhya pradesh", "maharashtra", "delhi", "haryana"]:
            if state in user_msg:
                info = get_cm(state)
                if info:
                    req.messages.append({"role": "model", "content": info})
                    ans = ask_gemini(req.messages)
                    return {"reply": ans or info}
    # Collector query
    if "collector" in user_msg or "जिला" in user_msg:
        city = "jaipur"
        for token in user_msg.split():
            if token not in ["what", "who", "is", "the", "of", "collector"]:
                city = token
                break
        info = get_current_collector(city.title())
        if info:
            req.messages.append({"role": "model", "content": info})
            ans = ask_gemini(req.messages)
            return {"reply": ans or info}

    # News
    if "news" in user_msg or "खबर" in user_msg or "समाचार" in user_msg:
        headlines = google_news_top5()
        if headlines:
            news = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            req.messages.append({"role": "model", "content": news})
            ans = ask_gemini(req.messages)
            return {"reply": ans or news}

    # General search
    ans = ask_gemini(req.messages)
    return {"reply": ans or "Sorry, up-to-date data is not available for your question."}
