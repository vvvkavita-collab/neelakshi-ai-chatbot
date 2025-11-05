import requests
import spacy

nlp = spacy.load("en_core_web_sm")
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

def extract_location(query):
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            return ent.text
    
    hindi_locations = {
        "राजस्थान": "Rajasthan",
        "जयपुर": "Jaipur",
        "कोटा": "Kota",
        "उदयपुर": "Udaipur",
        "जोधपुर": "Jodhpur",
    }
    for hi, en in hindi_locations.items():
        if hi in query:
            return en
    return None

def get_news_by_location(loc=None):
    if loc:
        url = f"https://newsapi.org/v2/everything?q={loc}&language=hi&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    else:
        url = f"https://newsapi.org/v2/top-headlines?country=in&language=hi&apiKey={NEWS_API_KEY}"

    data = requests.get(url).json()
    return data.get("articles", [])[:5]

def format_news(user_text):
    loc = extract_location(user_text)
    if loc:
        articles = get_news_by_location(loc)
        if not articles:
            return f"'{loc}' se sambandhit news nahi mili 😔"
        response = f"📰 {loc} ki Top 5 Hindi News:\n\n"
    else:
        articles = get_news_by_location()
        response = "📰 Aaj ki Top 5 Hindi News:\n\n"

    for i, item in enumerate(articles, start=1):
        response += f"{i}. {item['title']}\n"
    return response
