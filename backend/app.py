from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Allow all origins for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../public")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ✅ HEAD + GET for root
@app.head("/")
async def head_index():
    return JSONResponse({"status": "ok"})

@app.get("/")
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)

# ✅ Health check
@app.get("/status")
async def status():
    return {"status": "Backend is alive ✅"}

# ✅ Chat endpoint
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("messages", [{}])[0].get("content", "").lower()

    if "hello" in user_message:
        reply = "Hi there 👋! How can I help you today?"
    elif "bye" in user_message:
        reply = "Goodbye! 👋"
    else:
        reply = f"You said: {user_message}"

    return {"reply": reply}
