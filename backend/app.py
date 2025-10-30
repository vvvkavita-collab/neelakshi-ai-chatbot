import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai  # ✅ Correct import

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str

# Load API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Function to get live data via Google Search
def google_search(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": query,
            "num": 5
        }
        response = requests.get(url, params=params)
        data = response.json()

        results = []
        if "items" in data:
            for item in data["items"]:
                results.append(f"{item['title']}: {item['link']}")
        return "\n".join(results) if results else "No fresh info found online right now."
    except Exception as e:
        return f"Error fetching live data: {e}"

# Chat endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()

    live_keywords = ["today", "current", "present", "now", "latest", "news", "aaj", "abhi"]
    if any(word in user_message.lower() for word in live_keywords):
        search_results = google_search(user_message)
        return {"response": search_results}

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Neelakshi AI Chatbot Backend is Running Successfully 🚀"}
