# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (With Live Google Search)
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}

@app.post("/chat")
def chat(req: ChatRequest):
    user_query = req.message.strip()

    # 1️⃣ Try Google Search for live info
    try:
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?q={user_query}"
            f"&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}"
        )
        results = requests.get(search_url).json()
        if "items" in results:
            summary = "\n".join([item["snippet"] for item in results["items"][:3]])
            context = f"Live search results:\n{summary}"
        else:
            context = "No live results found."
    except Exception as e:
        context = f"Error fetching live data: {e}"

    # 2️⃣ Ask Gemini to summarize/answer using context
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        prompt = f"Use the following data to answer the question clearly:\n{context}\n\nQuestion: {user_query}"
        response = model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Error: {e}"}
