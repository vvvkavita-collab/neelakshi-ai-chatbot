# ==============================
#  Neelakshi AI Chatbot Backend (Gemini)
# ==============================

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai

# ------------------------------
# 1️⃣ Setup Gemini API Key
# ------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not set in environment variables.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# ------------------------------
# 2️⃣ Create FastAPI app
# ------------------------------
app = FastAPI()

# Enable CORS so your frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can replace * with your site link later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# 3️⃣ Serve frontend (optional)
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "public")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def home():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "🤖 Neelakshi AI Chatbot API is running!"}


@app.get("/status")
async def status():
    return {"status": "✅ Backend (Gemini) is running properly"}


# ------------------------------
# 4️⃣ Chat endpoint
# ------------------------------
@app.post("/chat")
async def chat(req: Request):
    """
    Receives { "messages": [{ "role": "user", "content": "..."}, ...] }
    Returns { "reply": "..." }
    """
    data = await req.json()
    messages = data.get("messages")

    if not messages:
        text = data.get("message") or data.get("content") or ""
        messages = [{"role": "user", "content": text}]

    # Extract the user’s latest message
    user_input = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_input = msg.get("content", "")

    if not user_input:
        return {"reply": "Please say something 😊"}

    # ------------------------------
    # 5️⃣ Generate reply using Gemini
    # ------------------------------
    if not GEMINI_API_KEY:
        return {"reply": "Gemini API key not configured on server 🛑"}

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_input)
        return {"reply": response.text.strip()}
    except Exception as e:
        print("Error:", e)
        return JSONResponse(
            {"reply": f"⚠️ Error while generating response: {str(e)}"},
            status_code=500,
        )


# ------------------------------
# 6️⃣ Run for local testing
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
