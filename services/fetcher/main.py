import os
import feedparser
import requests
from datetime import datetime
from fastapi import FastAPI

RSS_FEEDS = os.getenv("RSS_FEEDS", "https://feeds.bbci.co.uk/news/rss.xml")
AI_PROCESSOR_URL = os.getenv("AI_PROCESSOR_URL", "http://ai-processor:8001/process")

app = FastAPI(title="Fetcher Service")

def fetch_articles(feed_url):
    print(f"Fetching feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:10]:
        articles.append({
            "title": entry.get("title", "No title"),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", str(datetime.now())),
            "source": feed.feed.get("title", feed_url),
        })
    print(f"Found {len(articles)} articles")
    return articles

def send_to_processor(articles):
    try:
        response = requests.post(AI_PROCESSOR_URL, json={"articles": articles}, timeout=60)
        response.raise_for_status()
        print(f"Sent {len(articles)} articles to AI Processor")
    except requests.exceptions.RequestException as e:
        print(f"Failed: {e}")

@app.post("/run")
def run():
    print(f"\nFetcher triggered at {datetime.now()}")
    feed_urls = [url.strip() for url in RSS_FEEDS.split(",")]
    all_articles = []
    for url in feed_urls:
        all_articles.extend(fetch_articles(url))
    print(f"Total: {len(all_articles)} articles")
    if all_articles:
        send_to_processor(all_articles)
    return {"status": "ok", "articles_fetched": len(all_articles)}

@app.get("/health")
def health():
    return {"status": "ok"}
