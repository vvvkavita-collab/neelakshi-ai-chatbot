# backend/app.py
# Neelakshi AI Chatbot
# FastAPI backend combining:
#  - Live Google News (RSS) for "news" queries
#  - Google Custom Search for live/latest web results
#  - Gemini (google-generativeai package) as a summarizer / fallback
#
# Returns JSON { "reply": "..." } so your frontend can show it directly.

import os
import requests
import feedparser
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai   # matches your existing requirements setup

# Load environment variables from .env on local; Render ignores .env and uses Environment variables.
load_dotenv()

# -------------------------
# Config / Keys (must be present in Render environment)
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if not GEMINI_API_KEY:
    # fail early so logs show missing key
    raise Exception("GEMINI_API_KEY not found in environment variables. Add it in Render -> Environment.")

# Configure Gemini (the library you already used before)
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------
# FastAPI init
# -------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for testing; later set your frontend URL instead of "*"
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
    """Return concatenated snippets (or None) for a query using Google Custom Search."""
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
            snippets = []
            for item in data["items"][:max_results]:
                snip = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                # keep small structured snippet
                snippets.append(f"{title}. {snip} (Link: {link})")
            return " \n".join(snippets)
        return None
    except Exception:
        return None

def google_news_hindi_top5():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
        headlines = [entry.title for entry in feed.entries[:5]]
        return headlines if headlines else None
    except Exception:
        return None

def ask_gemini(prompt):
    """Ask the configured google-generativeai (Gemini) and return text or None on failure."""
    try:
        # Use a model name that worked previously in your environment — keep defensive fallback.
        # If your environment supports other model names you can change this.
        model_name_candidates = [
            "models/gemini-2.5-flash",      # newer 2.5 if available
            "models/gemini-2.0-flash",      # fallback
            "models/gemini-1.5-flash",      # older fallback
        ]
        last_err = None
        for model_name in model_name_candidates:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                # older client returned .text; ensure we handle both forms
                if hasattr(response, "text") and response.text:
                    return response.text
                # some responses may return .choices or other shape; convert defensively
                if hasattr(response, "choices") and response.choices:
                    # try to pull first message
                    first = response.choices[0]
                    if hasattr(first, "message") and first.message:
                        return getattr(first.message, "content", str(first.message))
                    return str(first)
                # last attempt: str(response)
                return str(response)
            except Exception as ex:
                last_err = ex
                # try next model_name
                continue
        # if all model attempts failed, raise last error for logs
        raise last_err if last_err is not None else Exception("Unknown Gemini error")
    except Exception:
        return None

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
        return {"reply": "कृपया कुछ टाइप करें । Please type something first."}

    lower = user_text.lower()

    # 1️⃣ Hindi News (same as before)
    if any(k in lower for k in ["news", "खबर", "headline", "समाचार", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            news_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            return {"reply": f"🗞️ आज की टॉप 5 हिंदी खबरें:\n\n{news_text}"}

    # 2️⃣ Detect special "live" topics
    refined_query = user_text
    if any(word in lower for word in ["match", "cricket", "t20", "odi", "ipl", "score", "series"]):
        refined_query += " site:espncricinfo.com OR site:cricbuzz.com"
    elif any(word in lower for word in ["weather", "मौसम"]):
        refined_query += " site:weather.com OR site:accuweather.com OR site:imd.gov.in"
    elif any(word in lower for word in ["election", "vote", "result", "नतीजे", "चुनाव"]):
        refined_query += " site:indiatoday.in OR site:ndtv.com OR site:hindustantimes.com"
    elif any(word in lower for word in ["district", "city", "state", "location", "area", "जिला", "शहर", "राज्य"]):
        refined_query += " site:wikipedia.org OR site:india.gov.in OR site:mapsofindia.com"

    # 3️⃣ Perform refined Google Search
    snippets = google_search_snippets(refined_query)
    if snippets:
        prompt = (
            f"User question: {user_text}\n\n"
            f"Recent web results:\n{snippets}\n\n"
            "Answer with the most recent and accurate information (today’s data if possible). "
            "If you can identify the latest update or place, mention it clearly in Hindi and English both."
        )
        gemini_answer = ask_gemini(prompt)
        if gemini_answer:
            return {"reply": gemini_answer}
        return {"reply": f"Here's what I found:\n{snippets}"}

    # 4️⃣ Fallback – use Gemini directly (general questions)
    prompt = (
        f"User asked: {user_text}\n"
        "Answer clearly and briefly in the user's language."
    )
    gemini_answer = ask_gemini(prompt)
    if gemini_answer:
        return {"reply": gemini_answer}

    return {"reply": "⚠️ Sorry, I couldn't fetch an answer right now. Please try again later."}

