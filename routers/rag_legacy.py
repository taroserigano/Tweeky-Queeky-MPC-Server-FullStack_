"""
RAG Router - REST API endpoints for RAG functionality

Exposes semantic search, product Q&A, and indexing endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field

from rag_service import rag_retriever, product_indexer
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
    in_stock_only: bool = Field(default=False, description="Only show in-stock products")


class ProductQuestionRequest(BaseModel):
    product_id: str = Field(..., description="Product ID to ask about")
    question: str = Field(..., min_length=1, description="Question about the product")


class SimilarProductsRequest(BaseModel):
    product_id: str = Field(..., description="Source product ID")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar products")
    same_category: bool = Field(default=True, description="Only same category")


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    semantic_weight: float = Field(default=0.7, ge=0, le=1, description="Weight for semantic vs keyword")


class IndexProductsRequest(BaseModel):
    product_ids: List[str] = Field(..., min_items=1, description="Product IDs to index")


# ──────────────────────────────────────────────────────────────────────────────
# Search Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search for products using natural language.
    
    Uses vector embeddings to find products that match the meaning of your query,
    not just keyword matches. Supports filtering by category, price, rating, and stock.
    
    Examples:
    - "comfortable office chair for long work sessions"
    - "wireless headphones with good bass"
    - "gifts for music lovers under $100"
    """
    try:
        if request.category or request.min_price or request.max_price or request.min_rating or request.in_stock_only:
            results = await rag_retriever.search_with_filters(
                query=request.query,
                category=request.category,
                min_price=request.min_price,
                max_price=request.max_price,
                min_rating=request.min_rating,
                in_stock_only=request.in_stock_only,
                top_k=request.top_k,
            )
        else:
            results = await rag_retriever.search(
                query=request.query,
                top_k=request.top_k,
            )
        
        return {
            "query": request.query,
            "count": len(results),
            "results": [
                {
                    "product_id": r.product_id,
                    "score": round(r.score, 4),
                    "product": r.product,
                }
                for r in results
            ],
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
    in_stock: bool = Query(default=False),
):
    """
    GET version of semantic search for easier testing.
    """
    request = SemanticSearchRequest(
        query=q,
        top_k=top_k,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock,
    )
    return await semantic_search(request)


@router.post("/hybrid-search")
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid search combining semantic and keyword matching.
    
    Adjusts the balance between semantic understanding and exact keyword matches
    using the semantic_weight parameter (0 = keywords only, 1 = semantic only).
    """
    try:
        results = await rag_retriever.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            semantic_weight=request.semantic_weight,
        )
        
        return {
            "query": request.query,
            "semantic_weight": request.semantic_weight,
            "count": len(results),
            "results": [
                {
                    "product_id": r.product_id,
                    "score": round(r.score, 4),
                    "product": r.product,
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar_products(request: SimilarProductsRequest):
    """
    Find products similar to a given product.
    
    Uses vector similarity to find products with similar characteristics,
    descriptions, and features.
    """
    try:
        results = await rag_retriever.find_similar_products(
            product_id=request.product_id,
            top_k=request.top_k,
            same_category=request.same_category,
        )
        
        return {
            "source_product_id": request.product_id,
            "count": len(results),
            "similar_products": [
                {
                    "product_id": r.product_id,
                    "score": round(r.score, 4),
                    "product": r.product,
                }
                for r in results
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{product_id}")
async def find_similar_products_get(
    product_id: str,
    top_k: int = Query(default=5, ge=1, le=20),
    same_category: bool = Query(default=True),
):
    """GET version of similar products endpoint."""
    request = SimilarProductsRequest(
        product_id=product_id,
        top_k=top_k,
        same_category=same_category,
    )
    return await find_similar_products(request)


# ──────────────────────────────────────────────────────────────────────────────
# Q&A Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/ask")
async def ask_product_question(request: ProductQuestionRequest):
    """
    Ask a question about a specific product.
    
    Uses RAG to answer questions based on product details and customer reviews.
    The AI will only use information from the product data, not external knowledge.
    
    Examples:
    - "Is this good for gaming?"
    - "What do customers say about the build quality?"
    - "Is it compatible with Mac?"
    """
    try:
        result = await rag_retriever.answer_product_question(
            product_id=request.product_id,
            question=request.question,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Indexing Endpoints (Admin)
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/index/all")
async def index_all_products(
    background_tasks: BackgroundTasks,
    clear_existing: bool = Query(default=False, description="Clear existing index first"),
    run_async: bool = Query(default=True, description="Run in background"),
):
    """
    Index all products into Pinecone.
    
    This should be run initially to populate the vector index, and periodically
    to ensure new products are indexed.
    
    Admin-only endpoint.
    """
    if run_async:
        background_tasks.add_task(
            product_indexer.index_all_products,
            clear_existing=clear_existing,
        )
        return {
            "status": "started",
            "message": "Indexing started in background. Check /api/rag/index/stats for progress.",
        }
    else:
        result = await product_indexer.index_all_products(clear_existing=clear_existing)
        return result


@router.post("/index/products")
async def index_specific_products(request: IndexProductsRequest):
    """
    Index specific products by ID.
    
    Useful for indexing newly added products or updating changed products.
    """
    try:
        result = await product_indexer.index_products_batch(request.product_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/product/{product_id}")
async def index_single_product(product_id: str):
    """
    Index or update a single product.
    """
    try:
        result = await product_indexer.index_product(product_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/product/{product_id}")
async def remove_product_from_index(product_id: str):
    """
    Remove a product from the vector index.
    """
    try:
        result = await product_indexer.remove_product(product_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/stats")
async def get_index_stats():
    """
    Get indexing statistics.
    
    Shows the number of products in MongoDB vs indexed in Pinecone,
    and sync status.
    """
    try:
        stats = await product_indexer.get_index_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/sync")
async def sync_index(background_tasks: BackgroundTasks):
    """
    Sync the vector index with MongoDB.
    
    Ensures all products are indexed. Runs in background.
    """
    background_tasks.add_task(product_indexer.sync_index)
    return {
        "status": "started",
        "message": "Index sync started in background.",
    }
