from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# ✅ Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to your frontend domain if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(__file__), "../public")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found"}, status_code=404)

# ✅ Simple backend check
@app.get("/status")
def status():
    return {"status": "Backend is running fine ✅"}

# ✅ Chat endpoint
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("messages", [{}])[0].get("content", "").lower()

    if "hello" in user_message:
        reply = "Hi there 👋! How can I help you?"
    elif "bye" in user_message:
        reply = "Goodbye! 👋"
    else:
        reply = f"You said: {user_message}"

    return {"reply": reply}
