from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize FastAPI app
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- CHAT ENDPOINT -------------
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return {"reply": "Please type something first 😊"}

    try:
        # Step 1: Check if user is asking for today's news
        if "news" in user_message.lower() or "खबर" in user_message.lower():
            url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "xml")
            items = soup.find_all("item")[:5]

            headlines = "\n".join([f"{i+1}. {item.title.text}" for i, item in enumerate(items)])
            return {"reply": f"📰 आज की ताज़ा खबरें ({datetime.now().strftime('%d %B %Y')}):\n\n{headlines}"}

        # Step 2: Normal chat using Gemini
        current_date = datetime.now().strftime("%d %B %Y")
        context = f"Today’s date is {current_date}. Answer naturally and clearly."

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content([context, user_message])

        return {"reply": response.text}

    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}


# ----------- TEST ROUTE -------------
@app.get("/")
async def root():
    return {"message": "Neelakshi AI Chatbot backend is running fine ✅"}
