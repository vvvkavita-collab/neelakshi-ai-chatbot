# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow all origins (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"message": "Neelakshi AI backend is running!"}

@app.post("/chat")
def chat(request: ChatRequest):
    user_input = request.message

    # Step 1: Search live data using Google Search API
    search_url = f"https://www.googleapis.com/customsearch/v1?q={user_input}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}"
    search_response = requests.get(search_url)
    data = search_response.json()

    snippets = ""
    if "items" in data:
        snippets = " ".join([item["snippet"] for item in data["items"][:3]])

    # Step 2: Generate response using Gemini
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Use the following info: {snippets}. Answer the user query clearly: {user_input}"
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"response": answer}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
