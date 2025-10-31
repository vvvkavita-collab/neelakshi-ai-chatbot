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

    # 1) If user requested news -> return live Hindi news (fast, working)
    if any(k in lower for k in ["news", "खबर", "headline", "समाचार", "आज की"]):
        headlines = google_news_hindi_top5()
        if headlines:
            news_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            return {"reply": f"🗞️ आज की टॉप 5 हिंदी खबरें:\n\n{news_text}"}
        # fallback message
        # if google news fails, continue to try search/gemini below

    # 2) Try Google Custom Search for live web results (best for 'current' questions, location specifics)
    snippets = google_search_snippets(user_text)
    if snippets:
        # Ask Gemini to summarize the snippets (if Gemini available), else return snippets directly
        prompt = (
            f"User question: {user_text}\n\n"
            f"Recent web excerpts (from Google Custom Search):\n{snippets}\n\n"
            "Please give a short, accurate answer based on the above, and include sources (links). "
            "If user asked for location/district/state details, prioritize local facts from the search results."
        )
        gemini_answer = ask_gemini(prompt)
        if gemini_answer:
            return {"reply": gemini_answer}
        # Gemini failed -> return cleaned snippets as fallback
        return {"reply": f"Here are the latest search snippets I found:\n\n{snippets}"}

    # 3) No live results -> fallback to direct Gemini answer (Gemini's internal knowledge, may be older)
    prompt = (
        f"User question: {user_text}\n\n"
        "Answer clearly and helpfully. If you don't know, say you don't know."
    )
    gemini_answer = ask_gemini(prompt)
    if gemini_answer:
        return {"reply": gemini_answer}

    # 4) Everything failed
    return {"reply": "⚠️ Sorry, I couldn't fetch an answer right now. Please try again in a bit."}
