import requests
from bs4 import BeautifulSoup
import feedparser

class NewsService:

    def google_news(self, query, num=5):
        rss = f"https://news.google.com/rss/search?q={query}&hl=hi&gl=IN&ceid=IN:hi"
        feed = feedparser.parse(rss)
        results = []
        for item in feed.entries[:num]:
            results.append(item.title)
        return results

    def get_news(self, user_msg: str):
        user_msg = user_msg.lower()

        # State/City based logic
        places = ["jaipur", "delhi", "udaipur", "kota", "rajasthan", "mumbai"]
        for p in places:
            if p in user_msg:
                return self.google_news(f"{p} news")

        # General news
        if "news" in user_msg or "खबर" in user_msg:
            return self.google_news("India news")

        return ["❌ News not found. Please ask like: `Jaipur news`"]
