# ============================================
# Neelakshi AI Chatbot - FastAPI + Gemini + Google Search
# ============================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
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
genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL for better security
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
    return {"message": "Neelakshi AI backend is running!"}

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
            snippets = "No latest data found online."

        # --- STEP 2: Ask Gemini to summarize answer ---
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"User asked: {user_input}\nBased on web search: {snippets}\nAnswer in simple language."
        response = model.generate_content(prompt)

        return {"response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run the app (Render auto handles uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
