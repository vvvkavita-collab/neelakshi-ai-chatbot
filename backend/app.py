from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv
import re
import spacy

# ==============================
#  Load Environment Variables
# ==============================
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load SpaCy for location detection
nlp = spacy.load("en_core_web_sm")

# ==============================
#  Initialize FastAPI App
# ==============================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ✅ Helper Functions
# =====================================================

def extract_location(text: str):
    """ Identify city/state name from Hindi/English user message """
    doc = nlp(text)
    # English location detection
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            return ent.text

    # Hindi fallback dictionary
    hindi_locations = {
        "जयपुर": "Jaipur", "राजस्थान": "Rajasthan",
        "कोटा": "Kota", "उदयपुर": "Udaipur",
        "जोधपुर": "Jodhpur", "अजमेर": "Ajmer",
        "बीकानेर": "Bikaner", "अलवर": "Alwar",
        "सीकर": "Sikar", "भरतपुर": "Bharatpur"
    }

    for hi, en in hindi_locations.items():
        if hi in text:
            return en
    
    return None


def get_news_by_location(loc=None):
    """ Fetch Hindi news - local or national """
    if loc:
        url = f"https://news.google.com/rss/search?q={loc}&hl=hi&gl=IN&ceid=IN:hi"
    else:
        url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "xml")
    return soup.find_all("item")[:5]


def format_news_response(user_text):
    """ Final news reply for user """
    date_str = datetime.now().strftime("%d %B %Y")
    loc = extract_location(user_text)

    articles = get_news_by_location(loc)

    if not articles:
        return "❌ उस जगह से संबंधित खबर नहीं मिली। कृपया किसी और स्थान का नाम पूछें।"

    if loc:
        response = f"📰 {loc} की ताज़ा खबरें ({date_str}):\n\n"
    else:
        response = f"📰 आज की ताज़ा खबरें ({date_str}):\n\n"

    for i, item in enumerate(articles, start=1):
        response += f"{i}. {item.title.text}\n"

    return response


def looks_like_office_query(text: str) -> bool:
    return bool(re.search(r"(collector|district magistrate|dm of|who is|who was)", text, re.I))


def try_scrape_official_site() -> str | None:
    url = os.getenv("OFFICIAL_COLLECTOR_URL", "https://jaipur.rajasthan.gov.in/content/raj/jaipur/en/collector-office.html")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        possible_texts = soup.get_text(separator="\n")
        match = re.search(r"Collector\s*[:\-]?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", possible_texts)
        if match:
            return match.group(1)
    except Exception:
        return None
    return None


# =====================================================
# ✅ Main Chat Endpoint
# =====================================================

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return {"reply": "Please type something first 😊"}

    try:
        # ✅ Collector / DM queries
        if looks_like_office_query(user_message):
            scraped = try_scrape_official_site()
            if scraped:
                return {"reply": f"✅ Jaipur Collector: **{scraped}**"}
            return {"reply": "⚠️ Live data unavailable. कृपया Jaipur Govt वेबसाइट देखें ✅"}

        # ✅ Location-based News
        if "news" in user_message.lower() or "खबर" in user_message.lower():
            return {"reply": format_news_response(user_message)}

        # ✅ AI Chat (Gemini)
        current_date = datetime.now().strftime("%d %B %Y")
        system_prompt = (
            "You are Neelakshi AI — a friendly, concise, factual assistant. "
            "Always answer clearly in simple language."
        )

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            [system_prompt, f"Date: {current_date}\nUser: {user_message}"],
            temperature=0.0,
        )

        return {"reply": response.text}

    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}


@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}
