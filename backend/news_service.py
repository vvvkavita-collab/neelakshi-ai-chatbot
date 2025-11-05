import requests
from bs4 import BeautifulSoup
import pandas as pd

class NewsService:
    def __init__(self):
        self.locations = [
            "jaipur", "ajmer", "kota", "udaipur", "jodhpur", "alwar",
            "rajasthan", "delhi", "mumbai", "chennai", "kolkata", "india"
        ]

    def fetch_google_news(self, query):
        url = f"https://news.google.com/rss/search?q={query}+news+india&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "xml")
            items = soup.find_all("item")[:10]
            news_list = [
                {
                    "title": item.title.text,
                    "link": item.link.text
                } for item in items
            ]
            return news_list
        except:
            return []

    def analyze_query(self, user_msg):
        text = user_msg.lower()

        detected_location = None
        for loc in self.locations:
            if loc.lower() in text:
                detected_location = loc.title()
                break

        category = "General"
        if any(x in text for x in ["crime", "chor", "police"]):
            category = "Crime"
        elif any(x in text for x in ["sports", "match", "cricket"]):
            category = "Sports"
        elif any(x in text for x in ["barish", "weather"]):
            category = "Weather"
        elif any(x in text for x in ["siyasat", "politics", "modi", "bjp", "congress"]):
            category = "Politics"

        return detected_location, category

    def get_news(self, user_msg):
        location, category = self.analyze_query(user_msg)

        search_query = ""
        if location:
            search_query += location + " "
        if category != "General":
            search_query += category

        if search_query.strip() == "":
            search_query = "India news"

        news_items = self.fetch_google_news(search_query)

        if not news_items:
            return [{"title": "No news found", "link": ""}]

        return news_items
