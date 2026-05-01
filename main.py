"""
Fetcher Service
---------------
Pulls articles from RSS feeds and sends them
to the AI Processor for summarization.
"""

import os
import feedparser
import requests
import json
from datetime import datetime

# ─────────────────────────────────────────
# Config from environment variables
# ─────────────────────────────────────────
RSS_FEEDS = os.getenv("RSS_FEEDS", "https://feeds.bbci.co.uk/news/rss.xml")
AI_PROCESSOR_URL = os.getenv("AI_PROCESSOR_URL", "http://ai-processor:8001/process")


def fetch_articles(feed_url: str) -> list[dict]:
    """Parse a single RSS feed and return a list of articles."""
    print(f"📡 Fetching feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed.entries[:10]:  # Limit to 10 articles per feed
        articles.append({
            "title": entry.get("title", "No title"),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", str(datetime.now())),
            "source": feed.feed.get("title", feed_url),
        })

    print(f"  ✅ Found {len(articles)} articles from {feed.feed.get('title', feed_url)}")
    return articles


def send_to_processor(articles: list[dict]):
    """Send articles to the AI Processor service."""
    try:
        response = requests.post(
            AI_PROCESSOR_URL,
            json={"articles": articles},
            timeout=60
        )
        response.raise_for_status()
        print(f"  📨 Sent {len(articles)} articles to AI Processor")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Failed to send articles: {e}")


def run():
    """Main entry point — fetch all feeds and forward articles."""
    print("\n🚀 Fetcher service started")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    feed_urls = [url.strip() for url in RSS_FEEDS.split(",")]
    all_articles = []

    for url in feed_urls:
        articles = fetch_articles(url)
        all_articles.extend(articles)

    print(f"\n📦 Total articles fetched: {len(all_articles)}")

    if all_articles:
        send_to_processor(all_articles)

    print("\n✅ Fetcher run complete\n")


if __name__ == "__main__":
    run()
