# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# with Google Search + Gemini
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Allow frontend (Render static site)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Google Search config
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Chat request schema
class ChatRequest(BaseModel):
    message: str

# Function: get search results
def get_google_results(query):
    try:
        url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?key={GOOGLE_SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
        )
        response = requests.get(url)
        data = response.json()

        results = []
        for item in data.get("items", []):
            results.append(f"- {item['title']}: {item['link']}")
        return "\n".join(results[:5]) if results else None

    except Exception as e:
        return None

# Root health check
@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine!"}

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    # If question looks like “current/latest/today/now”
    if any(word in user_message.lower() for word in ["today", "current", "latest", "news", "2025", "now"]):
        search_results = get_google_results(user_message)
        if search_results:
            combined_input = f"User asked: {user_message}\nBased on these Google results:\n{search_results}\nGive the best summarized and updated answer."
        else:
            combined_input = f"User asked: {user_message}\nNo search results found. Try answering anyway."
    else:
        combined_input = user_message

    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(combined_input)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
