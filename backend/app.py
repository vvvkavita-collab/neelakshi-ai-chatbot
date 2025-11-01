from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str   # 'user' ya 'assistant'
    content: str  # actual chat message

class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/chat")
def chat(req: ChatRequest):
    last = req.messages[-1].content  # Yeh yahan correct hai

    # === Simple logic filhaal (aap yahan apne Gemini/GPT code bhi laga sakte hain) ===
    if "weather" in last.lower():
        reply = "Jaipur ka weather aaj 29°C hai, mostly sunny."
    elif "capital" in last.lower():
        reply = "India ki capital New Delhi hai."
    else:
        reply = "Aapka message mila: " + last

    return {"reply": reply}
