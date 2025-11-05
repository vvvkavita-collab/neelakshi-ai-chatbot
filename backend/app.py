from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv
import re

# ==============================
#  Load Environment Variables
# ==============================
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==============================
#  Initialize FastAPI App
# ==============================
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend URL for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Helper Functions
# =====================================================

def looks_like_office_query(text: str) -> bool:
    """
    Detects if the user's message is about a government office-holder.
    """
    return bool(re.search(r"(collector|district magistrate|dm of|who is|who was)", text, re.I))


def try_scrape_official_site() -> str | None:
    """
    Tries to scrape the official Jaipur District website for the Collector's name.
    You can set OFFICIAL_COLLECTOR_URL in your environment variables.
    """
    url = os.getenv("OFFICIAL_COLLECTOR_URL", "https://jaipur.rajasthan.gov.in/content/raj/jaipur/en/collector-office.html")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # This is a simple example — adjust CSS selectors as needed.
        possible_texts = soup.get_text(separator="\n")
        match = re.search(r"Collector\s*[:\-]?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", possible_texts)
        if match:
            return match.group(1)
    except Exception:
        return None
    return None


# =====================================================
#  Main Chat Endpoint
# =====================================================

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return {"reply": "Please type something first 😊"}

    try:
        # ✅ Step 1: Handle "Who is Collector" type queries
        if looks_like_office_query(user_message):
            scraped = try_scrape_official_site()
            if scraped:
                return {
                    "reply": (
                        f"✅ According to the official Jaipur District website, "
                        f"the current Collector is **{scraped}**."
                    )
                }

            # If scraping didn’t find anything, provide helpful next steps
            return {
                "reply": (
                    "I don’t have live access to confirm that right now 🕵️‍♀️.\n\n"
                    "To find the current or past Jaipur Collector, please check:\n"
                    "1️⃣ Jaipur District Administration official site\n"
                    "2️⃣ Department of Personnel, Government of Rajasthan\n"
                    "3️⃣ Reputable local news websites (TOI Rajasthan, Hindustan Times Rajasthan)\n\n"
                    "🔎 Tip: You can Google — `site:rajasthan.gov.in Jaipur Collector`"
                )
            }

        # ✅ Step 2: Handle “news” keyword (Hindi or English)
        if "news" in user_message.lower() or "खबर" in user_message.lower():
            url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "xml")
            items = soup.find_all("item")[:5]

            headlines = "\n".join([f"{i+1}. {item.title.text}" for i, item in enumerate(items)])
            return {"reply": f"📰 आज की ताज़ा खबरें ({datetime.now().strftime('%d %B %Y')}):\n\n{headlines}"}

        # ✅ Step 3: Normal chat via Gemini
        current_date = datetime.now().strftime("%d %B %Y")
        system_prompt = (
            "You are Neelakshi AI — a friendly, concise, factual assistant. "
            "Always answer clearly, in simple language. "
            "Avoid unnecessary disclaimers or repetition. "
            "If you don’t know something, say so briefly and suggest where to look."
        )

        user_prompt = f"Date: {current_date}\nUser said: {user_message}"

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            [system_prompt, user_prompt],
            temperature=0.0,
            max_output_tokens=400,
        )

        reply_text = response.text if hasattr(response, "text") else str(response)
        return {"reply": reply_text}

    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}


# =====================================================
#  Test Route (for Render Health Check)
# =====================================================

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}
