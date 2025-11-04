from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Allow CORS (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (you can restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correct path to frontend (public) folder
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "../public")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Serve the main index.html
@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found", "path_checked": index_path}, status_code=404)

# Health check route
@app.get("/status")
async def status():
    return {"status": "Backend is running fine ✅"}

# Chat endpoint
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
