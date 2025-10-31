# ============================================
# Neelakshi AI Chatbot - FastAPI + Gemini + Google Search (2025 FIXED)
# ============================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Configure Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for public testing; later replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schema
class ChatRequest(BaseModel):
    message: str


# Health check
@app.get("/")
def root():
    return {"message": "✅ Neelakshi AI backend is running on Render!"}


# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        user_input = request.message.strip()

        # Step 1: Get fresh info from Google Search
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={user_input}"
        )
        search_response = requests.get(search_url)
        data = search_response.json()

        snippets = ""
        if "items" in data:
            snippets = " ".join([item["snippet"] for item in data["items"][:3]])
        else:
            snippets = "No recent results found online."

        # Step 2: Ask Gemini
        prompt = f"""
        Question: {user_input}
        Context (from Google Search): {snippets}
        Give a concise and accurate answer as of the year 2025.
        """

        result = client.models.generate_content(
            model="models/gemini-1.5-flash-latest",  # ✅ fixed name for new SDK
            contents=prompt
        )

        return {"response": result.output_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run locally (Render handles uvicorn automatically)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
