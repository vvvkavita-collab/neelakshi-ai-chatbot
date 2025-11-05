from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from google.generativeai import configure, GenerativeModel
import news_service  # ✅ Same folder import

# Configure Google AI Key
configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = GenerativeModel("gemini-pro")
news_service_obj = news_service.NewsService()

app = FastAPI()

# ✅ CORS
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
def home():
    return {"message": "✅ Neelakshi AI Backend Running Successfully!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    user_msg = req.message
    ai_reply = ""

    try:
        # Check for news-related queries
        if any(word in user_msg.lower() for word in ["news", "खबर", "jaipur", "udaipur", "delhi", "mumbai", "rajasthan", "kota"]):
            news_list = news_service_obj.get_news(user_msg)
            ai_reply = "\n".join(news_list)
        else:
            # Generate AI response using Google Gemini
            response = model.generate_content(user_msg, timeout=10)
            ai_reply = response.text
    except Exception as e:
        print("Error in /chat:", e)
        # Fallback message
        ai_reply = (
            "⚠️ Sorry, I am unable to fetch live response right now.\n"
            "Example: The current Collector of Jaipur is Dr. Jitendra Kumar Soni (IAS 2010 batch)."
        )

    return {"reply": ai_reply}
