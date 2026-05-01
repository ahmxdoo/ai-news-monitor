"""
Notifier Service
----------------
Queries Qdrant for today's articles, builds a digest,
and sends it via Slack or Email.
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from fastapi import FastAPI
from qdrant_client import QdrantClient

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "news_articles")
NOTIFICATION_METHOD = os.getenv("NOTIFICATION_METHOD", "slack")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DIGEST_RECIPIENT = os.getenv("DIGEST_RECIPIENT", "")

# ─────────────────────────────────────────
# App setup
# ─────────────────────────────────────────
app = FastAPI(title="Notifier Service")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_todays_articles() -> list[dict]:
    """Retrieve all articles stored in Qdrant."""
    results = qdrant.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=20,
        with_payload=True,
        with_vectors=False,
    )
    articles = [point.payload for point in results[0]]
    print(f"📚 Retrieved {len(articles)} articles from Qdrant")
    return articles


def build_digest(articles: list[dict]) -> str:
    """Build a plain-text digest from the articles."""
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [
        f"🤖 AI News Digest — {today}",
        f"{'─' * 50}",
        f"📰 {len(articles)} articles collected today\n",
    ]

    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. {article.get('title', 'No title')}")
        lines.append(f"   📌 {article.get('summary', 'No summary available.')}")
        lines.append(f"   🔗 {article.get('url', '')}")
        lines.append(f"   📡 Source: {article.get('source', 'Unknown')}\n")

    lines.append("─" * 50)
    lines.append("Powered by LangChain + Qdrant + n8n")
    return "\n".join(lines)


def send_slack(digest: str):
    """Send digest to Slack via webhook."""
    if not SLACK_WEBHOOK_URL:
        print("❌ SLACK_WEBHOOK_URL not set")
        return

    payload = {"text": f"```{digest}```"}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    if response.status_code == 200:
        print("✅ Digest sent to Slack")
    else:
        print(f"❌ Slack error: {response.status_code}")


def send_email(digest: str):
    """Send digest via email (SMTP)."""
    if not SMTP_USER or not DIGEST_RECIPIENT:
        print("❌ Email config not set")
        return

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = DIGEST_RECIPIENT
    msg["Subject"] = f"🤖 AI News Digest — {datetime.now().strftime('%B %d, %Y')}"
    msg.attach(MIMEText(digest, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Digest sent to {DIGEST_RECIPIENT}")
    except Exception as e:
        print(f"❌ Email error: {e}")


# ─────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────
@app.post("/send-digest")
def send_digest():
    """Build and send the news digest."""
    print(f"\n📬 Sending digest at {datetime.now().strftime('%H:%M:%S')}")

    articles = get_todays_articles()
    if not articles:
        return {"status": "skipped", "reason": "No articles found"}

    digest = build_digest(articles)
    print(f"\n{digest}\n")

    if NOTIFICATION_METHOD == "slack":
        send_slack(digest)
    elif NOTIFICATION_METHOD == "email":
        send_email(digest)

    return {"status": "sent", "articles_count": len(articles)}


@app.get("/health")
def health():
    return {"status": "ok"}
