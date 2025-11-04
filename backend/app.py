from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Allow all frontend origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 Absolute path to frontend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "public"))

# Debug print
print("Frontend path:", FRONTEND_DIR)

# 🟢 Mount static folder (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 🟢 Serve index.html for root route
@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return JSONResponse(
            {"error": "index.html not found", "checked_path": index_file},
            status_code=404,
        )

# 🟢 Health check route
@app.get("/status")
async def status():
    return {"status": "Backend is running fine ✅"}

# 🟢 Chat route
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
