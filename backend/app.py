from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

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
async def root():
    return {"message": "✅ Gemini Chatbot backend is running!"}

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        res = model.generate_content(req.message)
        return {"reply": res.text if hasattr(res, "text") else "⚠️ कोई उत्तर नहीं मिला।"}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}
