import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "news_articles")

app = FastAPI(title="AI Processor")
llm = ChatOllama(model="llama3.2:1b", base_url=OLLAMA_HOST)
embeddings = OllamaEmbeddings(model="llama3.2:1b")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

summarize_prompt = PromptTemplate(
    input_variables=["title", "content"],
    template="Summarize this news article in 3 sentences.\nTitle: {title}\nContent: {content}\nSummary:"
)
summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)

def ensure_collection():
    collections = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        qdrant.create_collection(QDRANT_COLLECTION, vectors_config=VectorParams(size=2048, distance=Distance.COSINE))
        print(f"Created collection: {QDRANT_COLLECTION}")

def is_duplicate(embedding):
    results = qdrant.search(collection_name=QDRANT_COLLECTION, query_vector=embedding, limit=1)
    return results and results[0].score >= 0.92

def process_article(article):
    title = article["title"]
    content = article.get("summary", title)
    print(f"Processing: {title[:60]}")
    summary = summarize_chain.run(title=title, content=content)
    embedding = embeddings.embed_query(summary)
    if is_duplicate(embedding):
        print(f"Duplicate skipped: {title[:60]}")
        return None
    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=[
        PointStruct(id=str(uuid.uuid4()), vector=embedding,
                    payload={"title": title, "url": article.get("url",""),
                             "source": article.get("source",""), "summary": summary.strip()})
    ])
    print(f"Stored: {title[:60]}")
    return {**article, "summary": summary.strip()}

class ArticleList(BaseModel):
    articles: list[dict]

@app.on_event("startup")
def startup():
    ensure_collection()
    print("AI Processor ready")

@app.post("/process")
def process_articles(payload: ArticleList):
    processed = [r for a in payload.articles if (r := process_article(a))]
    return {"processed": len(processed)}

@app.get("/health")
def health():
    return {"status": "ok"}
