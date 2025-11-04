from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create the FastAPI app
app = FastAPI()

# Allow your frontend (e.g., your chatbot UI) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can later replace "*" with your frontend URL for safety
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route (for testing if backend is live)
@app.get("/")
def root():
    return {"status": "Backend is running fine ✅"}

# Example chatbot endpoint (you can modify this as you like)
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    # Simple example logic — you can replace this with your chatbot code
    if "hello" in user_message.lower():
        reply = "Hi there 👋! How can I help you today?"
    elif "how are you" in user_message.lower():
        reply = "I'm just a bot, but I’m doing great! 😄"
    else:
        reply = f"You said: {user_message}"

    return {"reply": reply}


# Run locally (Render will ignore this since it uses the Start Command)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
