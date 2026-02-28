import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

TELEGRAM_TOKEN = "PUT_YOUR_TOKEN_HERE"
CHAT_ID = "PUT_YOUR_CHAT_ID"

bot = Bot(token=TELEGRAM_TOKEN)

summarizer = pipeline("summarization")
classifier = pipeline("zero-shot-classification")
sentiment = pipeline("sentiment-analysis")

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=business",
    "https://www.france24.com/en/rss"
]

CATEGORIES = ["Politics","Economy","Energy","Security","Diplomacy","Infrastructure"]

processed_links = set()

def fetch_content(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return " ".join(p.get_text() for p in soup.find_all("p"))
    except:
        return ""

def process_news():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.link in processed_links:
                continue

            if "algeria" in entry.title.lower() or "algeria" in entry.summary.lower():
                article = fetch_content(entry.link)
                if len(article) < 300:
                    continue

                classification = classifier(article[:1000], CATEGORIES)
                category = classification["labels"][0]

                sent = sentiment(article[:512])[0]

                summary = summarizer(article[:1000], max_length=120, min_length=40, do_sample=False)[0]["summary_text"]

                message = f"""
🇩🇿 ALGERIA ALERT

📰 {entry.title}

📂 {category}
📊 {sent['label']}

📝 {summary}

🔗 {entry.link}
"""
                bot.send_message(chat_id=CHAT_ID, text=message)
                processed_links.add(entry.link)

scheduler = BlockingScheduler()
scheduler.add_job(process_news, "interval", minutes=15)
scheduler.start()
