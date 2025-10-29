from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model
class Message(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Welcome to Neelakshi AI Chatbot Backend"}

@app.post("/chat")
def chat(data: Message):
    user_message = data.message.lower()

    # Simple reply logic
    if "capital" in user_message and "india" in user_message:
        reply = "The capital of India is New Delhi."
    elif "hello" in user_message or "hi" in user_message:
        reply = "Hello Neelakshi! 👋 How are you today?"
    elif "your name" in user_message:
        reply = "I’m Neelakshi AI Chatbot 🤖, your smart assistant!"
    else:
        reply = "I'm not sure about that, but I’ll try to learn it soon 💡."

    return {"reply": reply}
