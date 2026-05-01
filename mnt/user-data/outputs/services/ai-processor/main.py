"""
AI Processor Service
--------------------
Receives raw articles, summarizes them using LangChain + OpenAI,
generates vector embeddings, and stores them in Qdrant.
Deduplicates articles using semantic similarity search.
"""

import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "news_articles")
SIMILARITY_THRESHOLD = 0.92  # Articles above this score are considered duplicates

# ─────────────────────────────────────────
# App setup
# ─────────────────────────────────────────
app = FastAPI(title="AI Processor Service")

# LangChain setup
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Summarization prompt
summarize_prompt = PromptTemplate(
    input_variables=["title", "content"],
    template="""
    Summarize the following news article in exactly 3 sentences.
    Be concise and focus on the key facts.

    Title: {title}
    Content: {content}

    3-sentence summary:
    """
)
summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

# Qdrant client
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collection_exists():
    """Create Qdrant collection if it doesn't exist yet."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f"✅ Created Qdrant collection: {QDRANT_COLLECTION}")


def is_duplicate(embedding: list[float]) -> bool:
    """Check if a similar article already exists in Qdrant."""
    results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=1,
    )
    if results and results[0].score >= SIMILARITY_THRESHOLD:
        return True
    return False


def process_article(article: dict) -> dict | None:
    """Summarize an article, embed it, and store in Qdrant if not a duplicate."""
    title = article["title"]
    content = article.get("summary", title)

    # Step 1 — Summarize
    print(f"  🧠 Summarizing: {title[:60]}...")
    summary = summarize_chain.run(title=title, content=content)

    # Step 2 — Generate embedding
    embedding = embeddings.embed_query(summary)

    # Step 3 — Check for duplicates
    if is_duplicate(embedding):
        print(f"  ⚠️  Duplicate detected, skipping: {title[:60]}")
        return None

    # Step 4 — Store in Qdrant
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "title": title,
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published": article.get("published", ""),
            "summary": summary.strip(),
        }
    )
    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=[point])
    print(f"  ✅ Stored: {title[:60]}")

    return {**article, "summary": summary.strip()}


# ─────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────
class ArticleList(BaseModel):
    articles: list[dict]


@app.on_event("startup")
def startup():
    ensure_collection_exists()
    print("🚀 AI Processor service ready")


@app.post("/process")
def process_articles(payload: ArticleList):
    """Receive articles, summarize, embed, and store in Qdrant."""
    print(f"\n📥 Received {len(payload.articles)} articles to process")
    processed = []

    for article in payload.articles:
        result = process_article(article)
        if result:
            processed.append(result)

    print(f"\n✅ Processed {len(processed)} new articles (skipped duplicates)")
    return {"processed": len(processed), "articles": processed}


@app.get("/health")
def health():
    return {"status": "ok"}
