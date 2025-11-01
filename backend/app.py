import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if HAS_GENAI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Real ChatGPT-Style Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

def google_search(query):
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        return None
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_ENGINE_ID,
        "q": query,
        "num": 3
    }
    r = requests.get(url, params=params, timeout=8)
    data = r.json()
    if "items" in data:
        snippets = []
        for item in data["items"]:
            snippets.append(item.get("title", "") + ": " + item.get("snippet", ""))
        return "\n".join(snippets)
    return None

def ask_with_tools(messages, user_q):
    need_search = any(x in user_q.lower() for x in [
      'cricket', 'score', 'collector', 'cm', 'weather', 'news', 'latest', 'current', 'result', 'live', 'कलेक्टर', 'मौसम', 'स्कोर', 'न्यूज'
    ])
    system_info = ""
    if need_search:
        info = google_search(user_q)
        if info:
            system_info = f"\n\n[web search results]\n{info}\n"
    if not HAS_GENAI or not GEMINI_API_KEY:
        return "❌ Gemini or API Key missing"
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        all_msgs = messages[:]
        if system_info:
            all_msgs = [{"role": "system", "content": system_info}] + all_msgs
        formatted = [{"role": m["role"], "parts": [m["content"]]} for m in all_msgs]
        result = model.generate_content(formatted)
        if hasattr(result, "text") and result.text:
            return result.text
        return str(result)
    except Exception as e:
        return f"❌ error: {e}"

@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.messages or not isinstance(req.messages, list):
        raise HTTPException(status_code=400, detail="Send messages as list of [{role, content}]")
    last = req.messages[-1]["content"]
    ans = ask_with_tools([m.dict() for m in req.messages], last)
    return {"reply": ans}
