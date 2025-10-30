# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# With Google CSE (Live News & Search Integration)
# ============================================

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests

# Load .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to your frontend URL if you want security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Environment Variables for Google Search
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

# Schema
class ChatRequest(BaseModel):
    message: str

# Health check route
@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine"}

# Chat endpoint (Gemini + optional Google Search)
@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.message

    # Try to use Google Search for recent queries
    if "news" in user_input.lower() or "आज" in user_input or "latest" in user_input.lower():
        try:
            search_url = (
                f"https://www.googleapis.com/customsearch/v1?q={user_input}"
                f"&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}"
            )
            res = requests.get(search_url)
            data = res.json()

            if "items" in data:
                top_results = "\n".join(
                    [f"{i+1}. {item['title']} - {item['link']}" for i, item in enumerate(data["items"][:5])]
                )
                return {"reply": f"Here are the top search results:\n\n{top_results}"}
            else:
                return {"reply": "No recent results found on Google search."}
        except Exception as e:
            return {"reply": f"Google Search Error: {str(e)}"}

    # Normal Gemini AI reply
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(user_input)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
