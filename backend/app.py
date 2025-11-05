from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from google.generativeai import configure, GenerativeModel

# Google AI Key
configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = GenerativeModel("gemini-pro")

app = FastAPI()

# ✅ CORS Fix
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
    prompt = req.message

    response = model.generate_content(prompt)
    ai_reply = response.text

    return {"reply": ai_reply}
