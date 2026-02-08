"""
RAG Service - Semantic Document Retrieval (Port 7002)
Uses OpenAI embeddings + cosine similarity for semantic search
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os
import numpy as np
from pathlib import Path

# Load .env from project root
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────────────────────
# DOCUMENT STORAGE + EMBEDDINGS
# ────────────────────────────────────────────────────────────────────────────

DOCUMENTS: List["Document"] = []
EMBEDDINGS: Optional[np.ndarray] = None  # (num_docs, embed_dim)
_openai_client = None

EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))

class Document:
    def __init__(self, source_file: str, text: str, chunk_id: int):
        self.source_file = source_file
        self.text = text
        self.chunk_id = chunk_id


def _get_openai():
    """Lazy-init OpenAI client"""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set — cannot create embeddings")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def embed_texts(texts: List[str]) -> np.ndarray:
    """Batch-embed texts via OpenAI and return (N, dim) numpy array."""
    client = _get_openai()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = [item.embedding for item in sorted(resp.data, key=lambda d: d.index)]
    return np.array(vecs, dtype=np.float32)


def cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Cosine similarity between a single query vector and a matrix of doc vectors."""
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-10)
    return doc_norms @ query_norm

# ────────────────────────────────────────────────────────────────────────────
# DOCUMENT LOADING
# ────────────────────────────────────────────────────────────────────────────

def load_documents():
    """Load markdown files from docs folder and split into chunks"""
    global DOCUMENTS
    
    docs_dir = Path(__file__).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Create sample docs if they don't exist
    sample_docs = {
        "products.md": """# Product Guide

## Headphones
We offer premium headphones from Sony and Apple. The Sony WH-1000XM5 features industry-leading noise cancellation for $399.99. AirPods Pro are compact and integrate seamlessly with Apple devices for $249.99.

## Laptops
Our laptop selection includes the MacBook Air M2, a thin and light laptop perfect for everyday use, priced at $1199.99.

## Tablets
The iPad Air combines power and portability at $599.99, ideal for creative work and entertainment.

## Accessories
Complete your setup with accessories like the Magic Mouse ($79.99) or upgrade your workspace with professional monitors like the LG UltraFine 5K ($1299.99).
""",
        "shipping.md": """# Shipping Information

## Delivery Times
Standard shipping takes 5-7 business days. Express shipping is available for 2-3 day delivery. Free shipping is available on orders over $50.

## Shipping Methods
We offer Standard (5-7 days, free over $50), Express (2-3 days, $9.99), and Overnight (next day, $19.99) shipping options. All orders are shipped from our warehouse in New York.

## Order Tracking
Track your order using the order ID (e.g. ORD-1001) provided in your confirmation email. You can check your order status anytime through our website or by contacting support.

## International Shipping
We ship to over 50 countries. International delivery takes 10-14 business days. Customs fees may apply depending on your country.
""",
        "returns.md": """# Return Policy & Refunds

## Return Policy
Our return policy allows you to return any product within 30 days of purchase for a full refund. Items must be in original condition with all packaging and accessories included. To start a return, contact our support team with your order ID.

## Refund Policy
Refunds are processed within 5-7 business days after we receive your returned item. The refund will be credited to your original payment method. Shipping costs are non-refundable unless the return is due to our error.

## Exchange Policy
Want a different size or color? We offer free exchanges within 30 days. Simply contact support and we will arrange the exchange at no extra cost.

## Warranty
All electronics come with a 1-year manufacturer warranty. Extended warranty options are available at checkout for an additional 2 years of coverage. Warranty covers defects in materials and workmanship but does not cover accidental damage.

## Damaged or Defective Items
If you receive a damaged or defective product, contact us within 48 hours of delivery. We will provide a prepaid return label and send a replacement or issue a full refund immediately.
""",
        "support.md": """# Customer Support

## Contact Us
Email: support@tweekysqueeky.com
Phone: 1-800-TWEEKY (1-800-893-3594)
Live Chat: Available on our website during business hours.

## Business Hours
Monday-Friday: 9AM - 6PM EST
Saturday: 10AM - 4PM EST
Sunday: Closed

## FAQ - Frequently Asked Questions
Q: How do I track my order? A: Use the order ID from your confirmation email on our tracking page or ask our chat assistant.
Q: What is the return policy? A: You can return items within 30 days for a full refund. Items must be in original condition.
Q: How long does shipping take? A: Standard shipping is 5-7 business days. Express is 2-3 days.
Q: Do you offer warranty? A: Yes, all electronics have a 1-year warranty with optional extended coverage.
Q: How do I contact support? A: Email support@tweekysqueeky.com, call 1-800-TWEEKY, or use live chat.

## Common Issues
- Order tracking: Use your order ID to check delivery status
- Product recommendations: Describe your needs and budget to our AI assistant
- Technical support: Available for all purchased products
- Payment issues: Contact support with your order details
"""
    }
    
    for filename, content in sample_docs.items():
        filepath = docs_dir / filename
        if not filepath.exists():
            filepath.write_text(content)
    
    # Load and chunk documents by ## headers for better retrieval
    DOCUMENTS = []
    for md_file in docs_dir.glob("*.md"):
        logger.info(f"Loading {md_file.name}")
        content = md_file.read_text()
        
        # Split by ## headers for meaningful chunks
        import re
        sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
        
        # Get the # title to prepend to first section if it's just a title
        title_prefix = ""
        
        for i, section in enumerate(sections):
            section = section.strip()
            # If this is the # title (no ## prefix), save it for prepending
            if section.startswith("# ") and not section.startswith("## "):
                title_prefix = section
                # If title has content after the first line, keep it as a chunk
                lines = section.split("\n", 1)
                if len(lines) > 1 and len(lines[1].strip()) > 30:
                    DOCUMENTS.append(Document(
                        source_file=md_file.name,
                        text=section,
                        chunk_id=i
                    ))
                continue
            
            # Prepend title context to each section for better matching
            if title_prefix and section.startswith("## "):
                section = f"{title_prefix}\n\n{section}"
            
            if len(section) > 50:  # Skip very short chunks
                DOCUMENTS.append(Document(
                    source_file=md_file.name,
                    text=section,
                    chunk_id=i
                ))
    
    logger.info(f"Loaded {len(DOCUMENTS)} document chunks")

# ────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ────────────────────────────────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 3

class PassageResult(BaseModel):
    sourceFile: str
    text: str
    score: float

class RAGResponse(BaseModel):
    passages: List[PassageResult]
    query: str

# ────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────

@app.post("/rag/query", response_model=RAGResponse)
async def rag_query(req: RAGQueryRequest):
    """Retrieve relevant document passages via semantic similarity"""
    try:
        if not DOCUMENTS or EMBEDDINGS is None:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        # Embed the query
        query_vec = embed_texts([req.question])[0]
        
        # Compute cosine similarity against all doc embeddings
        scores = cosine_similarity(query_vec, EMBEDDINGS)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:req.top_k]
        
        passages = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.20:  # minimum relevance threshold
                doc = DOCUMENTS[idx]
                passages.append(PassageResult(
                    sourceFile=doc.source_file,
                    text=doc.text,
                    score=round(score, 4),
                ))
        
        logger.info(f"Query: '{req.question}' → {len(passages)} passages (top score: {scores[top_indices[0]]:.3f})")
        return RAGResponse(passages=passages, query=req.question)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "rag",
        "engine": "openai-embeddings",
        "model": EMBED_MODEL,
        "documents_loaded": len(DOCUMENTS),
        "embeddings_shape": list(EMBEDDINGS.shape) if EMBEDDINGS is not None else None,
    }


@app.on_event("startup")
async def startup_event():
    """Load documents and compute embeddings on startup"""
    global EMBEDDINGS
    load_documents()

    if DOCUMENTS:
        logger.info(f"Embedding {len(DOCUMENTS)} chunks with {EMBED_MODEL}...")
        texts = [doc.text for doc in DOCUMENTS]
        EMBEDDINGS = embed_texts(texts)
        logger.info(f"Embeddings ready: shape={EMBEDDINGS.shape}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7002)
