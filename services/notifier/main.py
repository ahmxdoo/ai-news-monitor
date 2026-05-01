import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from fastapi import FastAPI
from qdrant_client import QdrantClient

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

app = FastAPI(title="Notifier")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def get_articles():
    results = qdrant.scroll(collection_name=QDRANT_COLLECTION, limit=20, with_payload=True, with_vectors=False)
    return [p.payload for p in results[0]]

def build_digest(articles):
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [f"AI News Digest — {today}", "="*50, f"{len(articles)} articles today\n"]
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a.get('title','')}")
        lines.append(f"   {a.get('summary','')}")
        lines.append(f"   {a.get('url','')}\n")
    return "\n".join(lines)

def send_slack(digest):
    if SLACK_WEBHOOK_URL:
        requests.post(SLACK_WEBHOOK_URL, json={"text": f"```{digest}```"}, timeout=10)
        print("Sent to Slack")

def send_email(digest):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = DIGEST_RECIPIENT
    msg["Subject"] = f"AI News Digest — {datetime.now().strftime('%B %d, %Y')}"
    msg.attach(MIMEText(digest, "plain"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)
    print(f"Sent email to {DIGEST_RECIPIENT}")

@app.post("/send-digest")
def send_digest():
    articles = get_articles()
    if not articles:
        return {"status": "skipped", "reason": "No articles"}
    digest = build_digest(articles)
    if NOTIFICATION_METHOD == "slack":
        send_slack(digest)
    elif NOTIFICATION_METHOD == "email":
        send_email(digest)
    return {"status": "sent", "count": len(articles)}

@app.get("/health")
def health():
    return {"status": "ok"}
