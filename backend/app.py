# ============================================
# Neelakshi AI Chatbot - FastAPI + Gemini + Google Search (Fixed)
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

# Configure Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# ✅ Create app FIRST (this was the missing part in your old file)
app = FastAPI()

# Allow CORS (Frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    message: str


# ✅ Health Check
@app.get("/")
def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is live on Render!"}


# ✅ Chat Endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        user_input = request.message.strip()

        # --- Step 1: Perform Google Search ---
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={user_input}"
        )

        search_response = requests.get(search_url)
        data = search_response.json()

        if "items" in data:
            snippets = " ".join([item["snippet"] for item in data["items"][:3]])
        else:
            snippets = "No fresh search results found."

        # --- Step 2: Ask Gemini ---
        prompt = f"""
        The user asked: {user_input}
        Based on the latest web search information: {snippets}
        Provide an updated answer for the year 2025 in simple and clear language.
        """

        result = client.models.generate_content(
            model="models/gemini-2.0-flash",  # ✅ confirmed working
            contents=prompt
        )

        return {"response": result.output_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ✅ Local run (Render handles automatically)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
