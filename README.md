# 🤖 AI News & Trend Monitor

> An automated AI-powered pipeline that monitors news feeds, summarizes content using LLMs, detects trending topics with semantic search, and delivers smart digests — all containerized and production-ready.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-326CE5?logo=kubernetes)
![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-1C3C3C?logo=chainlink)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C)
![n8n](https://img.shields.io/badge/n8n-Workflow%20Automation-EA4B71?logo=n8n)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Roadmap](#roadmap)

---

## Overview

This project is a fully automated **AI news monitoring pipeline** built to demonstrate real-world usage of modern AI engineering tools. It ingests RSS/news feeds on a schedule, uses a Large Language Model (LLM) to summarize articles and generate vector embeddings, stores them in a vector database for semantic deduplication and trend detection, and delivers a curated digest via email or Slack.

**Why this project?**
Traditional news aggregators show you everything. This system understands content — it groups similar articles, surfaces emerging trends, and filters out noise using semantic similarity rather than simple keyword matching.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        n8n Scheduler                            │
│              (Triggers every N hours via cron)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Fetcher Service                             │
│           (Python — pulls RSS / News API feeds)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │  Raw articles (title, url, content)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI Processor Service                          │
│     LangChain — Summarizes articles + generates embeddings      │
└──────────┬──────────────────────────────────────────┬──────────┘
           │  Store embeddings                        │  Summaries
           ▼                                          ▼
┌─────────────────────┐                  ┌────────────────────────┐
│       Qdrant        │                  │    Notifier Service    │
│  (Vector Database)  │◄─── similarity ──│  Builds digest, sends  │
│  Semantic search &  │     search       │  via Email / Slack     │
│  deduplication      │                  └────────────────────────┘
└─────────────────────┘

        All services run in Docker containers, orchestrated by Kubernetes
```

---

## Tech Stack

| Tool | Role | Why |
|------|------|-----|
| **Python 3.11** | Core language | Clean, readable, great AI ecosystem |
| **LangChain** | LLM orchestration | Chains, prompts, embeddings management |
| **Qdrant** | Vector database | Fast semantic search & similarity matching |
| **n8n** | Workflow automation | Visual scheduling, triggers, integrations |
| **Docker** | Containerization | Consistent environments across machines |
| **Kubernetes** | Orchestration | Scalability, self-healing, production-ready |
| **OpenAI API** | LLM & embeddings | Summarization + text-embedding-ada-002 |

---

## Features

- ⏱️ **Scheduled ingestion** — Automatically fetches news every few hours via n8n cron
- 🧠 **AI summarization** — LangChain + LLM condenses articles into 3-sentence summaries
- 🔍 **Semantic deduplication** — Qdrant prevents storing near-identical articles
- 📈 **Trend detection** — Clusters semantically similar articles to surface trending topics
- 📬 **Smart digest delivery** — Sends curated summary via Email or Slack
- 🐳 **Fully containerized** — Every service runs in Docker
- ☸️ **Kubernetes-ready** — Includes K8s manifests for production deployment

---

## Project Structure

```
ai-news-monitor/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── services/
│   ├── fetcher/                  # RSS feed fetcher
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── ai-processor/             # LangChain summarizer + embeddings
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── notifier/                 # Digest builder + sender
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── n8n/
│   └── workflows/
│       └── news-monitor.json     # Exported n8n workflow
│
└── k8s/                          # Kubernetes manifests
    ├── namespace.yaml
    ├── qdrant-deployment.yaml
    ├── fetcher-deployment.yaml
    ├── ai-processor-deployment.yaml
    ├── notifier-deployment.yaml
    └── services.yaml
```

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.11+](https://www.python.org/downloads/)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-news-monitor.git
cd ai-news-monitor
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see [Configuration](#configuration)).

### 3. Start all services with Docker Compose

```bash
docker-compose up --build
```

This will start:
- **Qdrant** on `http://localhost:6333`
- **n8n** on `http://localhost:5678`
- **Fetcher**, **AI Processor**, and **Notifier** services

### 4. Import the n8n workflow

1. Open n8n at `http://localhost:5678`
2. Go to **Workflows → Import**
3. Upload `n8n/workflows/news-monitor.json`
4. Activate the workflow

### 5. Trigger a manual run

```bash
# Or trigger via n8n UI, or wait for the cron schedule
curl -X POST http://localhost:5678/webhook/trigger-news-fetch
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the following:

```env
# LLM
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=news_articles

# News Sources (comma-separated RSS URLs)
RSS_FEEDS=https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss

# Notifications
NOTIFICATION_METHOD=slack          # Options: slack, email
SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# Email (if NOTIFICATION_METHOD=email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
DIGEST_RECIPIENT=recipient@email.com

# n8n
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=changeme
```

---

## How It Works

### Step 1 — Fetch
The **Fetcher** service polls configured RSS feeds and returns raw article data (title, URL, published date, raw content).

### Step 2 — Process
The **AI Processor** service uses **LangChain** to:
1. Summarize each article into 3 concise sentences using an LLM
2. Generate a vector embedding using `text-embedding-ada-002`
3. Query **Qdrant** to check if a similar article already exists (deduplication)
4. Store new articles with their embeddings in Qdrant

### Step 3 — Detect Trends
Qdrant's similarity search groups semantically related articles together, identifying trending topics across multiple sources.

### Step 4 — Notify
The **Notifier** service builds a digest from today's top articles and trending topics, then sends it via Slack or Email.

### Step 5 — Orchestrate
**n8n** runs the entire pipeline on a cron schedule, connecting the services together with a visual workflow — no code required for the orchestration layer.

---

## Kubernetes Deployment

For production deployment on a Kubernetes cluster:

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Qdrant
kubectl apply -f k8s/qdrant-deployment.yaml

# Deploy services
kubectl apply -f k8s/fetcher-deployment.yaml
kubectl apply -f k8s/ai-processor-deployment.yaml
kubectl apply -f k8s/notifier-deployment.yaml

# Expose services
kubectl apply -f k8s/services.yaml

# Check pods are running
kubectl get pods -n ai-news-monitor
```

---

## Roadmap

- [x] RSS feed ingestion
- [x] LangChain summarization pipeline
- [x] Qdrant vector storage & deduplication
- [x] n8n workflow orchestration
- [x] Docker Compose setup
- [x] Kubernetes manifests
- [ ] Web dashboard to browse articles
- [ ] Support for more sources (Twitter/X, Reddit, HackerNews)
- [ ] Custom topic filtering per user
- [ ] Multi-language support

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙋 Author

Built by **[Your Name]** as a portfolio project demonstrating AI engineering skills.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin)](https://linkedin.com/in/YOUR_PROFILE)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github)](https://github.com/YOUR_USERNAME)
