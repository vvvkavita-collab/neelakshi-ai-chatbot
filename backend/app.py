# backend/app.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class Query(BaseModel):
    question: str

def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}"
    response = requests.get(url)
    data = response.json()

    results = []
    if "items" in data:
        for item in data["items"][:3]:
            results.append(item["snippet"])
    return " ".join(results) if results else "No recent info found online."

@app.post("/chat")
async def chat_with_ai(request: Request):
    body = await request.json()
    question = body.get("question")

    # Step 1: Fetch latest info from Google
    search_data = google_search(question)

    # Step 2: Ask Gemini to summarize
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Use this recent information and answer: {question}\n\nData: {search_data}"
    response = model.generate_content(prompt)

    return {"answer": response.text}

@app.get("/")
def home():
    return {"message": "Neelakshi AI backend is running!"}
