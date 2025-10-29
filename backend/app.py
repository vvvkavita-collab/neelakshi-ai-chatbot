# ============================================
# Neelakshi AI Chatbot - FastAPI Backend (Render)
# (Now supports live Hindi news updates)
# ============================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os, requests
import feedparser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message.lower()

    # ✅ If user asks for Hindi news
    if "news" in user_message or "खबर" in user_message:
        try:
            feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
            news_items = []
            for entry in feed.entries[:5]:
                news_items.append(entry.title)
            headlines = "\n".join([f"{i+1}. {n}" for i, n in enumerate(news_items)])

            return {
                "reply": f"🗞️ आज की टॉप 5 हिंदी खबरें इस प्रकार हैं:\n{headlines}\n\nआप और जानकारी के लिए गूगल न्यूज़ पर जा सकते हैं।"
            }
        except Exception as e:
            return {"reply": f"⚠️ खबरें लोड करने में समस्या आई: {str(e)}"}

    # ✅ Normal Gemini chat
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(request.message)

        if hasattr(response, "text") and response.text:
            return {"reply": response.text}
        else:
            return {"reply": "⚠️ Sorry, I couldn’t generate a valid reply."}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
