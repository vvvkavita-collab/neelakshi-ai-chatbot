import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai.types import Content

# Initialize FastAPI app
app = FastAPI()

# Allow frontend communication (important for your onrender frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class ChatRequest(BaseModel):
    message: str

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in Render Environment.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Google Search API keys
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


# 🔹 Function: Google Custom Search
def google_search(query):
    """Fetch top results using Google Programmable Search API"""
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


# 🔹 Main Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()

    # If user asks for current or real-time info
    live_keywords = ["today", "current", "present", "now", "latest", "news", "aaj", "abhi"]
    if any(word in user_message.lower() for word in live_keywords):
        search_results = google_search(user_message)
        return {"response": search_results}

    # Otherwise use Gemini for general AI chat
    try:
        prompt = f"You are Neelakshi AI Chatbot. Answer in a friendly and factual way.\nUser: {user_message}\nAnswer:"
        result = client.models.generate_content(
            model="models/gemini-1.5-flash-latest",
            contents=[Content(role="user", parts=[prompt])]
        )
        response_text = result.candidates[0].content.parts[0].text
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    return {"message": "Neelakshi AI Chatbot Backend is Running Successfully 🚀"}
