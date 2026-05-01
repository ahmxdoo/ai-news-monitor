# AI News & Trend Monitor

> A fully automated AI-powered pipeline that monitors live news feeds, summarizes content using a local LLM (Ollama), detects trending topics with semantic search, and delivers smart digests — all containerized and production-ready.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestrated-326CE5?logo=kubernetes)
![LangChain](https://img.shields.io/badge/LangChain-LLM%20Framework-1C3C3C)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C)
![n8n](https://img.shields.io/badge/n8n-Workflow%20Automation-EA4B71)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [n8n Workflow](#n8n-workflow)
- [Service Endpoints](#service-endpoints)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Roadmap](#roadmap)

---

## Overview

This project is a fully automated AI news monitoring pipeline built to demonstrate real-world usage of modern AI engineering tools. It ingests RSS/news feeds on a schedule, uses a locally running LLM (Llama 3.2 via Ollama) to summarize articles and generate vector embeddings, stores them in a vector database for semantic deduplication and trend detection, and delivers a curated digest via Slack or Email.

The entire AI layer runs 100% locally — no OpenAI API key or cloud costs required. The LLM and embeddings are served by Ollama running inside Docker, making this fully self-contained.

---

## Architecture

```
+------------------------------------------------------------------+
|                        n8n Scheduler                            |
|          Cron trigger every 6 hours -> HTTP POST /run            |
+-----------------------------+------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    Fetcher Service  :8000                        |
|          Python/FastAPI -- pulls BBC, CNN RSS feeds              |
+-----------------------------+------------------------------------+
                              |  Raw articles (title, url, content)
                              v
+------------------------------------------------------------------+
|                 AI Processor Service  :8001                      |
|    LangChain + Ollama -- summarizes & generates embeddings       |
+---------------+----------------------------------+---------------+
                |  Store vectors                   |  Summaries
                v                                  v
+------------------------+            +---------------------------+
|      Qdrant  :6333     |            |   Notifier Service :8002  |
|    Vector Database     |<-similarity|   Builds & sends digest   |
|    Semantic search     |   search   |   via Slack or Email      |
|    Deduplication       |            +---------------------------+
+------------------------+
                ^
                |  Embeddings & Summarization
+------------------------+
|      Ollama  :11434    |
|   Llama 3.2 1B model   |
|   Runs 100% locally    |
+------------------------+

      All services run in Docker, orchestrated by Kubernetes
```

---

## Tech Stack

| Tool | Role | Why |
|------|------|-----|
| **Python 3.11** | Core language | Clean, readable, great AI ecosystem |
| **FastAPI** | Service framework | Fast async APIs for each microservice |
| **LangChain** | LLM orchestration | Chains, prompts, embeddings management |
| **Ollama** | Local LLM server | Run Llama 3.2 locally — zero API costs |
| **Llama 3.2 1B** | Language model | Summarization + embeddings, runs on consumer hardware |
| **Qdrant** | Vector database | Fast semantic search & similarity matching |
| **n8n** | Workflow automation | Visual scheduling, triggers, integrations |
| **Docker** | Containerization | All 6 services isolated and reproducible |
| **Kubernetes** | Orchestration | Scalability, self-healing, production-ready |

---

## Features

- Scheduled ingestion — n8n cron triggers the pipeline every 6 hours automatically
- Local AI summarization — LangChain + Llama 3.2 via Ollama, zero API costs
- Semantic deduplication — Qdrant prevents storing near-identical articles using cosine similarity
- Trend detection — clusters semantically similar articles to surface trending topics
- Smart digest delivery — sends curated summary via Slack or Email
- Fully containerized — all 6 services run in Docker with a single command
- Kubernetes-ready — includes K8s manifests for production deployment
- Privacy-first — no data leaves your machine, LLM runs entirely locally

---

## Project Structure

```
ai-news-monitor/
|
+-- README.md
+-- .gitignore
+-- .env.example
+-- docker-compose.yml          # 6 services: qdrant, ollama, n8n, fetcher, ai-processor, notifier
|
+-- services/
|   +-- fetcher/                # RSS feed ingestion service
|   |   +-- main.py             # FastAPI app -- /run and /health endpoints
|   |   +-- requirements.txt
|   |   +-- Dockerfile
|   |
|   +-- ai-processor/           # LangChain summarizer + Qdrant storage
|   |   +-- main.py             # FastAPI app -- /process endpoint
|   |   +-- requirements.txt
|   |   +-- Dockerfile
|   |
|   +-- notifier/               # Digest builder + Slack/Email sender
|       +-- main.py             # FastAPI app -- /send-digest endpoint
|       +-- requirements.txt
|       +-- Dockerfile
|
+-- n8n/
|   +-- workflows/
|       +-- news-monitor.json   # Exportable n8n workflow
|
+-- k8s/                        # Kubernetes manifests
    +-- namespace.yaml
    +-- qdrant-deployment.yaml
    +-- ollama-deployment.yaml
    +-- fetcher-deployment.yaml
    +-- ai-processor-deployment.yaml
    +-- notifier-deployment.yaml
    +-- services.yaml
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — use Apple Silicon version for M1/M2/M3 Macs
- [Git](https://git-scm.com/)
- 8GB RAM recommended (Ollama runs the LLM locally inside Docker)

### 1. Clone the repository

```bash
git clone https://github.com/ahmxdoo/ai-news-monitor.git
cd ai-news-monitor
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Slack webhook URL or email settings.

### 3. Start all services

```bash
docker-compose up --build
```

First run takes 5-10 minutes — Docker pulls images and builds all containers.

### 4. Pull the AI model

Open a new terminal tab while services are starting:

```bash
docker exec ollama ollama pull llama3.2:1b
```

Downloads the ~800MB Llama 3.2 model into the Ollama container.

### 5. Import the n8n workflow

1. Open n8n at `http://localhost:5678`
2. Login: `admin` / `changeme123`
3. Go to Workflows -> Import
4. Upload `n8n/workflows/news-monitor.json`
5. Toggle Active to enable the schedule

### 6. Test manually

```bash
# Trigger the full pipeline
curl -X POST http://localhost:8000/run

# Check articles stored in Qdrant
open http://localhost:6333/dashboard

# Send a digest immediately
curl -X POST http://localhost:8002/send-digest
```

---

## Configuration

```env
# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=news_articles

# Ollama (automatically set via docker-compose)
OLLAMA_HOST=http://ollama:11434

# News Sources (comma-separated RSS URLs)
RSS_FEEDS=https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss

# Notifications -- choose: slack or email
NOTIFICATION_METHOD=slack
SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# Email (if NOTIFICATION_METHOD=email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
DIGEST_RECIPIENT=recipient@email.com

# n8n
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=changeme123
```

---

## How It Works

### Step 1 - Fetch
The Fetcher service polls BBC News and CNN RSS feeds and returns raw article data (title, URL, content, source).

### Step 2 - Summarize and Embed
The AI Processor uses LangChain to:
1. Summarize each article into 3 sentences using Llama 3.2 running locally via Ollama
2. Generate a vector embedding of the summary
3. Query Qdrant for similar articles (semantic deduplication)
4. Store new unique articles with embeddings in Qdrant

### Step 3 - Detect Trends
Qdrant's cosine similarity search groups semantically related articles together, surfacing trending topics across multiple sources without keyword matching.

### Step 4 - Notify
The Notifier queries today's articles from Qdrant, builds a human-readable digest, and delivers it via Slack or Email.

### Step 5 - Automate
n8n orchestrates the entire pipeline on a schedule:
```
Schedule Trigger (every 6h) -> POST /run -> POST /send-digest
```

---

## n8n Workflow

```
[Schedule Trigger] --> [Trigger Fetcher] --> [Send Digest]
  Every 6 hours          POST :8000/run      POST :8002/send-digest
```

To set it up manually:
1. Add a Schedule Trigger node — interval: 6 hours
2. Add an HTTP Request node — `POST http://fetcher:8000/run`
3. Add an HTTP Request node — `POST http://notifier:8002/send-digest`
4. Connect in sequence and toggle Active

---

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **n8n** | `http://localhost:5678` | Workflow automation UI |
| **Qdrant** | `http://localhost:6333/dashboard` | Vector DB dashboard |
| **Fetcher** | `http://localhost:8000/health` | Health check |
| **AI Processor** | `http://localhost:8001/health` | Health check |
| **Notifier** | `http://localhost:8002/health` | Health check |
| **Ollama** | `http://localhost:11434` | Local LLM server |

---

## Kubernetes Deployment

```bash
# Deploy everything
kubectl apply -f k8s/

# Check pods are running
kubectl get pods -n ai-news-monitor

# Access services locally
kubectl port-forward svc/n8n 5678:5678 -n ai-news-monitor
kubectl port-forward svc/qdrant 6333:6333 -n ai-news-monitor
```

---

## Roadmap

- [x] RSS feed ingestion with FastAPI
- [x] Local LLM summarization via Ollama + Llama 3.2
- [x] LangChain pipeline integration
- [x] Qdrant vector storage & semantic deduplication
- [x] n8n workflow automation (6h schedule)
- [x] Slack digest delivery
- [x] Docker Compose setup (6 services)
- [x] Kubernetes manifests
- [ ] Web dashboard to browse stored articles
- [ ] Support for Reddit, HackerNews, Twitter/X
- [ ] Custom topic filtering per user
- [ ] Multi-language article support
- [ ] Upgrade to Llama 3 8B for better summaries

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by **Ahmad Daoud** as a portfolio project demonstrating AI engineering skills including RAG pipelines, vector databases, local LLMs, microservices, workflow automation, and container orchestration.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin)](https://www.linkedin.com/in/ahmad-daoud-b9677219a/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github)](https://github.com/ahmxdoo)
