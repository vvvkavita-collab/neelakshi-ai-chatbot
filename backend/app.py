from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to frontend (static) folder
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "../public")

# Mount static files (JS, CSS)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)

@app.get("/status")
async def status():
    return {"status": "✅ Backend is running fine!"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("messages", [{}])[0].get("content", "").lower()

    if "hello" in user_message:
        reply = "Hi there 👋! How can I help you today?"
    elif "bye" in user_message:
        reply = "Goodbye! 👋 Have a great day!"
    else:
        reply = f"You said: {user_message}"

    return {"reply": reply}
