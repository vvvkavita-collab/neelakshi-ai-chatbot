from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from datetime import datetime
from google.generativeai import configure, GenerativeModel
import news_service

# ✅ Configure Gemini
configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = GenerativeModel("gemini-pro")
news_service_obj = news_service.NewsService()

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "✅ Neelakshi AI Backend Running Successfully!"}

def get_weather(city):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1").json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
        temp = w["current_weather"]["temperature"]
        wind = w["current_weather"]["windspeed"]
        return f"🌤️ {city} का तापमान {temp}°C है और हवा की गति {wind} km/h है।"
    except:
        return None

def build_gemini_prompt(user_msg, snippets=None):
    prompt = (
        f"Today's date: {datetime.now().strftime('%d %B %Y')}\n"
        f"You are Neelakshi AI — a smart assistant that answers any question clearly and helpfully.\n\n"
        f"User asked: {user_msg}\n\n"
    )
    if snippets:
        prompt += f"Recent web results:\n{snippets}\n\n"
    prompt += (
        "Please give a complete answer. If it's a how-to question, use numbered steps. "
        "If it's a factual query, give a short summary. "
        "If the user asked in Hindi, reply in Hindi. If in English, reply in English. "
        "Keep it clear, helpful, and no longer than 6 sentences."
    )
    return prompt

@app.post("/chat")
async def chat(req: ChatRequest):
    user_msg = req.message.strip()
    ai_reply = ""

    try:
        lower = user_msg.lower()

        # 🔹 News
        if any(word in lower for word in ["news", "खबर", "jaipur", "udaipur", "delhi", "mumbai", "rajasthan", "kota"]):
            news_list = news_service_obj.get_news(user_msg)
            ai_reply = "\n".join(news_list)
            return {"reply": ai_reply}

        # 🔹 Weather
        if "weather" in lower or "मौसम" in lower:
            city = lower.replace("weather", "").replace("मौसम", "").strip() or "Jaipur"
            weather = get_weather(city)
            ai_reply = weather or f"⚠️ {city} के मौसम की जानकारी नहीं मिल सकी।"
            return {"reply": ai_reply}

        # 🔹 Cricket (fallback via Gemini)
        if any(word in lower for word in ["cricket", "match", "t20", "odi", "ipl", "score", "series"]):
            prompt = build_gemini_prompt(user_msg)
            response = model.generate_content(prompt)
            ai_reply = response.text
            return {"reply": ai_reply}

        # 🔹 Location / Collector / MP / MLA
        if any(word in lower for word in ["collector", "district", "जिला", "कलेक्टर", "mayor", "mp", "mla"]):
            prompt = build_gemini_prompt(user_msg)
            response = model.generate_content(prompt)
            ai_reply = response.text
            return {"reply": ai_reply}

        # 🔹 General queries
        prompt = build_gemini_prompt(user_msg)
        response = model.generate_content(prompt)
        ai_reply = response.text

    except Exception as e:
        print("Error in /chat:", e)
        ai_reply = (
            "⚠️ Sorry, I am unable to fetch live response right now.\n"
            "Example: The current Collector of Jaipur is Dr. Jitendra Kumar Soni (IAS 2010 batch)."
        )

    return {"reply": ai_reply}
