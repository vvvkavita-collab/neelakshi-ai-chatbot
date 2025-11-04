# app.py
import os
import openai
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not set. Set it in .env or environment.")
else:
    openai.api_key = OPENAI_API_KEY

app = FastAPI()

# Allow frontend requests (for dev you can allow all)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to explicit origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend from ./public
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "public")
if not os.path.exists(FRONTEND_DIR):
    print("Warning: public folder not found at", FRONTEND_DIR)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# respond to HEAD (some hosts probe with HEAD)
@app.head("/")
async def head_root():
    return JSONResponse({"status": "ok"})

@app.get("/")
async def read_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html not found", "path_checked": index_path}, status_code=404)

@app.get("/status")
async def status():
    return {"status": "✅ Backend is running"}

# Chat endpoint: expects JSON { "messages": [{ "role": "user", "content": "..."}, ...] }
@app.post("/chat")
async def chat(req: Request):
    payload = await req.json()
    messages = payload.get("messages")
    # If frontend sends { message: "text" } support that too:
    if messages is None:
        text = payload.get("message") or payload.get("content") or ""
        messages = [{"role": "user", "content": text}]

    # Build chat history for OpenAI
    openai_messages = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        openai_messages.append({"role": role, "content": content})

    # Basic safety: if no API key, return canned reply
    if not OPENAI_API_KEY:
        return {"reply": "OpenAI API key not configured on the server. Set OPENAI_API_KEY."}

    try:
        # Use gpt-3.5-turbo for example (change model as desired)
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=512,
            temperature=0.7,
        )
        # Extract assistant text (concatenate choices if needed)
        assistant_text = ""
        if resp and "choices" in resp and len(resp["choices"]) > 0:
            assistant_text = resp["choices"][0]["message"]["content"].strip()
        else:
            assistant_text = "Sorry, I couldn't generate a reply."

        return {"reply": assistant_text}
    except openai.error.OpenAIError as e:
        return JSONResponse({"reply": f"[OpenAI error] {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"reply": f"[Server error] {str(e)}"}, status_code=500)
