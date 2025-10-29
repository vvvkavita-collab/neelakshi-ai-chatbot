# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (with Live Web Search)
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define data model
class ChatRequest(BaseModel):
    message: str

# 🔹 Function: Google Search API (for current info)
def get_live_info(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("SEARCH_ENGINE_ID")  # Add this in .env (custom search engine ID)
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"
    try:
        response = requests.get(url)
        data = response.json()
        results = data.get("items", [])
        if results:
            snippet = results[0].get("snippet", "No live info found.")
            link = results[0].get("link", "")
            return f"{snippet}\n\n(Source: {link})"
        return "Sorry, no recent updates found online."
    except Exception as e:
        return f"⚠️ Error fetching live info: {str(e)}"

# Root
@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}

# Chat Endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    try:
        # Step 1: If message asks for current data, get live info
        keywords = ["today", "latest", "now", "news", "update", "2025", "current"]
        if any(word in user_message.lower() for word in keywords):
            live_data = get_live_info(user_message)
            prompt = f"User asked: {user_message}\nHere is recent info from the web:\n{live_data}\n\nWrite a helpful, accurate answer using this info."
        else:
            prompt = user_message

        # Step 2: Generate Gemini response
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        return {"reply": response.text}

    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
