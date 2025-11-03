import os
import requests
import feedparser
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Gemini/OpenAI (replace as required)
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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

def get_weather(location):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1", timeout=5).json()
        if "results" not in geo or not geo["results"]: return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=5).json()
        cw = w.get("current_weather", {})
        temp = cw.get("temperature", "?")
        wind = cw.get("windspeed", "?")
        return f"{location.title()} temperature: {temp}°C, wind: {wind} km/h."
    except Exception as e:
        return None

def get_cricbuzz_news():
    try:
        rss = feedparser.parse("https://www.cricbuzz.com/rss/news")
        news = [entry.title for entry in rss.entries[:5]]
        return "\n".join(news)
    except:
        return None

def get_state_cm(state: str):
    wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/List_of_chief_ministers_of_{state.title().replace(' ', '_')}"
    try:
        r = requests.get(wiki_url, timeout=6)
        data = r.json()
        if 'extract' in data:
            return data['extract']
    except:
        return None

def get_jaipur_collector():
    url = "https://jaipur.rajasthan.gov.in/content/raj/jaipur/en/about-jaipur/district-collector.html"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        info = soup.find("div", {"class": "profiletitle"})
        if info:
            return info.text.strip()
    except Exception as e:
        return None

def get_google_news(query="india"):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(url)
        news = [entry.title for entry in feed.entries[:5]]
        return "\n".join(news)
    except:
        return None

def get_bollywood_news():
    rss_url = "https://www.bollywoodhungama.com/rss/news.xml"
    try:
        feed = feedparser.parse(rss_url)
        news = [entry.title for entry in feed.entries[:5]]
        return "\n".join(news)
    except:
        return None

def get_wikipedia_summary(topic):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        r = requests.get(url)
        data = r.json()
        if "extract" in data:
            return data["extract"]
    except:
        return None

def ask_llm(messages):
    try:
        chat_format = []
        for m in messages:
            if hasattr(m, "role"):
                chat_format.append({"role": m.role, "parts": [m.content]})
            elif isinstance(m, dict):
                chat_format.append({"role": m["role"], "parts": [m["content"]]})
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(chat_format)
        return response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        return f"Error: {e}"

@app.post("/chat")
def chat(req: ChatRequest):
    user_msg = req.messages[-1].content.lower()

    if "weather" in user_msg:
        loc = user_msg.replace("weather", "").strip() or "Delhi"
        out = get_weather(loc)
        if out:
            return {"reply": out}

    if "cricket" in user_msg:
        out = get_cricbuzz_news()
        if out:
            return {"reply": out}

    if "bollywood" in user_msg or "entertainment" in user_msg:
        out = get_bollywood_news()
        if out:
            return {"reply": out}

    if "collector" in user_msg and "jaipur" in user_msg:
        out = get_jaipur_collector()
        if out:
            return {"reply": out}

    # CM/Chief Minister dynamic
    if "chief minister" in user_msg or "cm" in user_msg:
        for state in ["rajasthan", "up", "uttar pradesh", "mp", "madhya pradesh", "maharashtra", "delhi"]:
            if state in user_msg:
                out = get_state_cm(state)
                if out:
                    return {"reply": out}

    # Wikipedia fallback for any topic
    if "wiki" in user_msg or "who" in user_msg or "where" in user_msg:
        keys = user_msg.replace("who is", "").replace("what is", "").replace("where is", "").strip()
        ans = get_wikipedia_summary(keys)
        if ans:
            return {"reply": ans}

    # NEWS on anything (city/state/country)
    if "news" in user_msg:
        query = user_msg.replace("news", "").strip() or "india"
        out = get_google_news(query)
        if out:
            return {"reply": out}

    # Fallback: LLM answer
    ans = ask_llm(req.messages)
    return {"reply": ans}
