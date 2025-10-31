# ============================================
# Neelakshi AI Chatbot - FastAPI + Gemini + Google Search (Fixed & Compatible)
# ============================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai  # ✅ correct import for new SDK
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# ✅ Configure Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace * with frontend URL later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    message: str

# Health check route
@app.get("/")
def root():
    return {"message": "Neelakshi AI backend is running successfully!"}

# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        user_input = request.message.strip()

        # --- STEP 1: Get latest info from Google Search ---
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={user_input}"
        )
        search_response = requests.get(search_url)
        data = search_response.json()

        if "items" in data:
            snippets = " ".join([item["snippet"] for item in data["items"][:3]])
        else:
            snippets = "No fresh info found online."

        # --- STEP 2: Ask Gemini for answer ---
        prompt = f"""
        User question: {user_input}
        Latest info: {snippets}
        Please answer accurately for the year 2025.
        """

        result = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        return {"response": result.output_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run locally (Render auto runs this)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
