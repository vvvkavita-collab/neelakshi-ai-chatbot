from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

# Add your own: ENV loading and generative model config here
import os

# LLM model config (Gemini or OpenAI)
import google.generativeai as genai  # or import openai

# ========== BEGIN CODE ==========

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
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

def get_live_collector(city="jaipur"):
    try:
        url = "https://jaipur.rajasthan.gov.in/content/raj/jaipur/en/about-jaipur/district-collector.html"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        titles = soup.find_all("div", {"class": "profiletitle"})
        names = [t.text.strip() for t in titles if "District Collector" in t.text or "Shri" in t.text]
        if names:
            return f"Current District Collector of Jaipur: {names[0]}"
    except Exception:
        pass
    return None

def get_wiki_summary(topic):
    """Quick, latest Wikipedia API summary."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("extract"):
            return data["extract"]
    except Exception:
        pass
    return None

def get_weather(location):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=6).json()
        if "results" not in geo or not geo["results"]: return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=6).json()
        cw = w.get("current_weather", {})
        temp = cw.get("temperature", "?")
        wind = cw.get("windspeed", "?")
        return f"{location.title()} temperature: {temp}°C, wind: {wind} km/h."
    except Exception:
        return None

def ask_llm(messages):
    # Gemini implementation
    try:
        chat_format = []
        for m in messages:
            if hasattr(m, "role"):
                chat_format.append({"role": m.role, "parts": [m.content]})
            elif isinstance(m, dict):
                chat_format.append({"role": m["role"], "parts": [m["content"]]})
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(chat_format)
        return getattr(response, "text", str(response))
    except Exception as e:
        return f"Error: {e}"

@app.post("/chat")
def chat(req: ChatRequest):
    user_msg = req.messages[-1].content.lower()

    # Layer 1: Collector
    if "collector" in user_msg and "jaipur" in user_msg:
        live = get_live_collector("jaipur")
        if live:
            req.messages.append({"role": "model", "content": live})
            return {"reply": live}
        # Wikipedia fallback
        wiki = get_wiki_summary("Jaipur_district")
        if wiki:
            req.messages.append({"role": "model", "content": wiki})
            return {"reply": wiki}

    # Layer 2: Weather
    if "weather" in user_msg or "मौसम" in user_msg:
        loc = "jaipur" if "jaipur" in user_msg else "delhi"
        report = get_weather(loc)
        if report:
            req.messages.append({"role": "model", "content": report})
            return {"reply": report}

    # Layer 3: General LLM with chat context for everything else
    ans = ask_llm(req.messages)
    return {"reply": ans}

# ========== END CODE ==========
