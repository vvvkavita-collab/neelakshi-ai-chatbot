import requests
import feedparser
from urllib.parse import quote  # ✅ URL encode

class NewsService:

    def google_news(self, query, num=5):
        try:
            encoded_query = quote(query)  # encode spaces and special chars
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=hi&gl=IN&ceid=IN:hi"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/114.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(resp.content)
            results = [item.title for item in feed.entries[:num]]
            if not results:
                results = ["❌ No news found for this query."]
            return results
        except Exception as e:
            print("Error fetching Google News:", e)
            return ["❌ News service is currently unavailable."]

    def get_news(self, user_msg: str):
        user_msg = user_msg.lower()
        places = ["jaipur", "delhi", "udaipur", "kota", "rajasthan", "mumbai"]
        for p in places:
            if p in user_msg:
                return self.google_news(f"{p} news")

        if "news" in user_msg or "खबर" in user_msg:
            return self.google_news("India news")

        return ["❌ News not found. Please ask like: `Jaipur news`"]
