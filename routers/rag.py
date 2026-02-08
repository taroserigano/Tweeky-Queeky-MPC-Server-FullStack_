"""
RAG Router - REST API endpoints for LangChain RAG functionality

Exposes semantic search, product Q&A, and indexing endpoints
using the LangChain-based RAG service.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field

from rag_service import get_vector_store, get_rag_chain, index_all_products
from config.settings import settings


router = APIRouter(prefix="/api/rag", tags=["rag"])


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ──────────────────────────────────────────────────────────────────────────────

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    category: Optional[str] = Field(default=None, description="Filter by category")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    min_rating: Optional[float] = Field(default=None, ge=0, le=5, description="Minimum rating")


class ProductQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about products")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context documents")


class SimilarProductsRequest(BaseModel):
    product_id: str = Field(..., description="Source product ID")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar products")


# ──────────────────────────────────────────────────────────────────────────────
# Search Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search for products using LangChain + Pinecone.
    
    Uses OpenAI embeddings and Pinecone vector store to find products 
    that match the semantic meaning of your query.
    
    Examples:
    - "comfortable office chair for long work sessions"
    - "wireless headphones with good bass"
    - "gifts for music lovers under $100"
    """
    try:
        rag_chain = get_rag_chain()
        results = rag_chain.search_products(
            query=request.query,
            k=request.top_k,
            min_price=request.min_price,
            max_price=request.max_price,
            category=request.category,
            min_rating=request.min_rating,
        )
        
        return {
            "query": request.query,
            "count": len(results),
            "framework": "langchain",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def semantic_search_get(
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(default=10, ge=1, le=50),
    category: Optional[str] = Query(default=None),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    min_rating: Optional[float] = Query(default=None, ge=0, le=5),
):
    """GET version of semantic search for easier testing."""
    request = SemanticSearchRequest(
        query=q,
        top_k=top_k,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
    )
    return await semantic_search(request)


# ──────────────────────────────────────────────────────────────────────────────
# Q&A Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/ask")
async def ask_about_products(request: ProductQuestionRequest):
    """
    Ask a question about products using RAG.
    
    Uses LangChain retrieval chain to:
    1. Embed the question
    2. Retrieve relevant product documents
    3. Generate an answer using GPT with product context
    
    Examples:
    - "What headphones have the best noise cancellation?"
    - "Which laptop is best for video editing?"
    - "Compare the Sony and Apple headphones"
    """
    try:
        rag_chain = get_rag_chain()
        result = await rag_chain.ask(
            question=request.question,
            k=request.top_k,
        )
        
        return {
            "question": request.question,
            "answer": result["answer"],
            "source_count": len(result.get("source_documents", [])),
            "sources": result.get("source_documents", []),
            "framework": "langchain",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ask")
async def ask_about_products_get(
    q: str = Query(..., min_length=1, description="Question about products"),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """GET version of ask endpoint."""
    request = ProductQuestionRequest(question=q, top_k=top_k)
    return await ask_about_products(request)


# ──────────────────────────────────────────────────────────────────────────────
# Similar Products
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/similar")
async def find_similar_products(request: SimilarProductsRequest):
    """
    Find products similar to a given product.
    
    Uses the product's embedding to find semantically similar items.
    """
    try:
        from bson import ObjectId
        from bson.errors import InvalidId
        from pymongo import MongoClient
        
        # Validate product_id
        try:
            oid = ObjectId(request.product_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid product ID format")
        
        # Get product using PyMongo (sync, reuses connection pool)
        from config.database import get_sync_db
        db = get_sync_db()
        product = db.products.find_one({"_id": oid})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Search using product name and description as query
        search_query = f"{product['name']} {product.get('description', '')}"
        
        rag_chain = get_rag_chain()
        results = rag_chain.search_products(
            query=search_query,
            k=request.top_k + 1,  # +1 to exclude self
        )
        
        # Filter out the source product
        similar = [
            r for r in results 
            if r.get("product_id") != request.product_id
        ][:request.top_k]
        
        return {
            "source_product": product["name"],
            "count": len(similar),
            "similar_products": similar,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{product_id}")
async def find_similar_products_get(
    product_id: str,
    top_k: int = Query(default=5, ge=1, le=20),
):
    """GET version of similar products."""
    request = SimilarProductsRequest(product_id=product_id, top_k=top_k)
    return await find_similar_products(request)


# ──────────────────────────────────────────────────────────────────────────────
# Indexing Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/index/all")
async def index_all_products_endpoint(background_tasks: BackgroundTasks):
    """
    Index all products into the Pinecone vector store.
    
    This creates embeddings for all products and upserts them
    into Pinecone for semantic search.
    """
    try:
        result = await index_all_products()
        return {
            "status": result["status"],
            "products_indexed": result.get("products_indexed", 0),
            "total_vectors": result.get("total_vectors", 0),
            "index_name": result.get("index_name"),
            "namespace": result.get("namespace"),
            "framework": "langchain",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/stats")
async def get_index_stats():
    """
    Get statistics about the Pinecone vector index.
    """
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        return {
            "index_name": vector_store.index_name,
            "namespace": vector_store.namespace,
            "stats": stats,
            "framework": "langchain",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/health")
async def rag_health_check():
    """Check RAG service health."""
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        
        return {
            "status": "healthy",
            "vector_store": "pinecone",
            "index": vector_store.index_name,
            "total_vectors": stats.get("total_vectors", 0),
            "framework": "langchain",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
