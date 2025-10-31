from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import feedparser
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Allow frontend connection (replace "*" with your actual frontend URL for security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Request model
class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "✅ Neelakshi AI Chatbot backend is running fine."}

@app.post("/chat")
async def chat(request: ChatRequest):
    user_msg = request.message.lower()

    # 📰 If user asks for news
    if "news" in user_msg or "खबर" in user_msg or "headline" in user_msg:
        try:
            feed = feedparser.parse("https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi")
            headlines = [entry.title for entry in feed.entries[:5]]

            if not headlines:
                return {"reply": "⚠️ फिलहाल कोई खबरें प्राप्त नहीं हुईं। कृपया कुछ समय बाद पुनः प्रयास करें।"}

            news_text = "\n".join([f"{i+1}. {headline}" for i, headline in enumerate(headlines)])
            return {
                "reply": f"🗞️ आज की टॉप 5 हिंदी खबरें ({datetime.now().strftime('%d %B %Y')}):\n\n{news_text}\n\nआप अधिक जानकारी के लिए Google News वेबसाइट पर जा सकते हैं।"
            }

        except Exception as e:
            return {"reply": f"⚠️ खबरें लोड करने में समस्या आई: {str(e)}"}

    # 💬 Otherwise, let Gemini answer normally with freshness and location awareness
    try:
        prompt = f"""
        You are Neelakshi AI, a Hindi-speaking assistant.
        Today is {datetime.now().strftime('%d %B %Y')}.
        If the user asks about a location (district/state), try to give relevant info.
        If the user asks about current events, respond with today's context.

        User: {request.message}
        """
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        return {"reply": response.text if hasattr(response, "text") else "⚠️ कोई उत्तर उपलब्ध नहीं है।"}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
