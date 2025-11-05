import feedparser

class NewsService:

    def google_news(self, query, num=5):
        try:
            rss = f"https://news.google.com/rss/search?q={query}&hl=hi&gl=IN&ceid=IN:hi"
            feed = feedparser.parse(rss)
            results = [item.title for item in feed.entries[:num]]
            if not results:
                results = ["❌ No news found for this query."]
            return results
        except Exception as e:
            print("Error fetching Google News:", e)
            return ["❌ News service is currently unavailable."]

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
