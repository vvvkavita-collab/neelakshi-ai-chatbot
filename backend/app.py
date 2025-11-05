from fastapi import FastAPI, Request
from news_service import NewsService
import uvicorn

app = FastAPI()
news_service = NewsService()

@app.get("/")
def home():
    return {"status": "✅ News Chatbot is Running Successfully"}

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_msg = body.get("message", "")

    news = news_service.get_news(user_msg)

    return {
        "query": user_msg,
        "results": news
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
