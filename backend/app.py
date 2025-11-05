from fastapi import FastAPI, Request
from news_service import NewsService

app = FastAPI()
news_service = NewsService()

@app.get("/")
def home():
    return {"status": "✅ Backend Running Fine"}

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message", "")

    news = news_service.get_news(user_msg)

    return {"query": user_msg, "results": news}
