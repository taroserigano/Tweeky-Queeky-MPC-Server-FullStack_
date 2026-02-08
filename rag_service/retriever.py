"""
RAG Retriever - Semantic search and retrieval

Combines embedding generation and vector search for intelligent product discovery.
Includes reranking and filtering capabilities.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config.settings import settings
from rag_service.embeddings import EmbeddingService
from rag_service.vector_store import PineconeStore, SearchResult
from services.product_service import product_service

# Create local instances to avoid circular imports
_embedding_svc: Optional[EmbeddingService] = None
_pinecone_svc: Optional[PineconeStore] = None


def _get_embedding_service() -> EmbeddingService:
    global _embedding_svc
    if _embedding_svc is None:
        _embedding_svc = EmbeddingService()
    return _embedding_svc


def _get_pinecone_store() -> PineconeStore:
    global _pinecone_svc
    if _pinecone_svc is None:
        _pinecone_svc = PineconeStore()
    return _pinecone_svc


@dataclass
class RetrievalResult:
    """Enhanced search result with full product data"""
    product_id: str
    score: float
    product: Dict[str, Any]
    relevance_explanation: Optional[str] = None


class RAGRetriever:
    """
    RAG Retriever for semantic product search.
    
    Combines:
    - Embedding generation for queries
    - Vector similarity search in Pinecone
    - Optional reranking for better relevance
    - Filtering by price, category, availability
    
    Usage:
        retriever = RAGRetriever()
        results = await retriever.search("comfortable office chair under $300")
        results = await retriever.search_with_filters(
            query="gaming accessories",
            category="Electronics",
            max_price=200
        )
    """
    
    def __init__(
        self,
        embedding_svc: Optional[EmbeddingService] = None,
        vector_store: Optional[PineconeStore] = None,
    ):
        self._embeddings = embedding_svc or _get_embedding_service()
        self._store = vector_store or _get_pinecone_store()
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        min_score: float = None,
        include_products: bool = True,
    ) -> List[RetrievalResult]:
        """
        Semantic search for products.
        
        Args:
            query: Natural language search query
            top_k: Number of results (default from settings)
            min_score: Minimum similarity score (default from settings)
            include_products: Whether to fetch full product data
            
        Returns:
            List of RetrievalResult with matched products
        """
        top_k = top_k or settings.RAG_TOP_K
        min_score = min_score or settings.RAG_SIMILARITY_THRESHOLD
        
        # Generate query embedding
        query_embedding = await self._embeddings.embed(query)
        
        # Search Pinecone
        search_results = await self._store.search(
            query_vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        
        # Filter by minimum score
        filtered_results = [r for r in search_results if r.score >= min_score]
        
        # Build retrieval results
        results = []
        for sr in filtered_results:
            result = RetrievalResult(
                product_id=sr.id,
                score=sr.score,
                product=sr.metadata if not include_products else {},
            )
            
            # Fetch full product data if requested
            if include_products:
                product_data = await product_service.get_product(sr.id)
                if product_data:
                    result.product = product_data
                else:
                    # Use metadata as fallback
                    result.product = sr.metadata
            
            results.append(result)
        
        return results
    
    async def search_with_filters(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        in_stock_only: bool = False,
        top_k: int = None,
    ) -> List[RetrievalResult]:
        """
        Semantic search with metadata filters.
        
        Args:
            query: Natural language search query
            category: Filter by category
            min_price: Minimum price
            max_price: Maximum price
            min_rating: Minimum rating
            in_stock_only: Only return in-stock products
            top_k: Number of results
            
        Returns:
            List of filtered RetrievalResult
        """
        top_k = top_k or settings.RAG_TOP_K
        
        # Build Pinecone filter
        pinecone_filter = {}
        
        if category:
            pinecone_filter["category"] = {"$eq": category}
        
        if min_price is not None:
            pinecone_filter["price"] = pinecone_filter.get("price", {})
            pinecone_filter["price"]["$gte"] = min_price
        
        if max_price is not None:
            pinecone_filter["price"] = pinecone_filter.get("price", {})
            pinecone_filter["price"]["$lte"] = max_price
        
        if min_rating is not None:
            pinecone_filter["rating"] = {"$gte": min_rating}
        
        if in_stock_only:
            pinecone_filter["count_in_stock"] = {"$gt": 0}
        
        # Generate query embedding
        query_embedding = await self._embeddings.embed(query)
        
        # Search with filters
        search_results = await self._store.search(
            query_vector=query_embedding,
            top_k=top_k * 2,  # Fetch more for post-filtering
            filter=pinecone_filter if pinecone_filter else None,
            include_metadata=True,
        )
        
        # Build results with full product data
        results = []
        for sr in search_results[:top_k]:
            product_data = await product_service.get_product(sr.id)
            
            results.append(RetrievalResult(
                product_id=sr.id,
                score=sr.score,
                product=product_data or sr.metadata,
            ))
        
        return results
    
    async def find_similar_products(
        self,
        product_id: str,
        top_k: int = 5,
        same_category: bool = True,
    ) -> List[RetrievalResult]:
        """
        Find products similar to a given product.
        
        Args:
            product_id: Source product ID
            top_k: Number of similar products
            same_category: Only return products in same category
            
        Returns:
            List of similar products (excluding source)
        """
        # Get source product
        source_product = await product_service.get_product(product_id)
        if not source_product:
            raise ValueError(f"Product not found: {product_id}")
        
        # Fetch source embedding from Pinecone
        stored = await self._store.fetch([product_id])
        
        if product_id not in stored:
            # Product not indexed, generate embedding
            product_text = self._embeddings.create_product_text(
                name=source_product["name"],
                brand=source_product["brand"],
                category=source_product["category"],
                description=source_product.get("description", ""),
                price=source_product["price"],
                rating=source_product.get("rating", 0),
            )
            query_embedding = await self._embeddings.embed(product_text)
        else:
            query_embedding = stored[product_id]["values"]
        
        # Build filter
        pinecone_filter = None
        if same_category:
            pinecone_filter = {"category": {"$eq": source_product["category"]}}
        
        # Search for similar (fetch extra to exclude source)
        search_results = await self._store.search(
            query_vector=query_embedding,
            top_k=top_k + 1,
            filter=pinecone_filter,
            include_metadata=True,
        )
        
        # Build results, excluding source product
        results = []
        for sr in search_results:
            if sr.id == product_id:
                continue
            
            product_data = await product_service.get_product(sr.id)
            results.append(RetrievalResult(
                product_id=sr.id,
                score=sr.score,
                product=product_data or sr.metadata,
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
    ) -> List[RetrievalResult]:
        """
        Hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic results (0-1)
            
        Returns:
            Combined and reranked results
        """
        keyword_weight = 1 - semantic_weight
        
        # Get semantic results
        semantic_results = await self.search(query, top_k=top_k * 2)
        
        # Get keyword results from product service
        keyword_results = await product_service.search_products(query, limit=top_k * 2)
        
        # Combine scores
        combined_scores: Dict[str, float] = {}
        product_data: Dict[str, Dict] = {}
        
        # Add semantic scores
        for i, result in enumerate(semantic_results):
            # Normalize position-based score
            position_score = 1.0 - (i / len(semantic_results)) if semantic_results else 0
            combined_scores[result.product_id] = result.score * semantic_weight
            product_data[result.product_id] = result.product
        
        # Add keyword scores
        for i, product in enumerate(keyword_results):
            product_id = product["id"]
            position_score = 1.0 - (i / len(keyword_results)) if keyword_results else 0
            
            if product_id in combined_scores:
                combined_scores[product_id] += position_score * keyword_weight
            else:
                combined_scores[product_id] = position_score * keyword_weight
                product_data[product_id] = product
        
        # Sort by combined score
        sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
        
        # Build results
        results = []
        for product_id in sorted_ids[:top_k]:
            results.append(RetrievalResult(
                product_id=product_id,
                score=combined_scores[product_id],
                product=product_data[product_id],
            ))
        
        return results
    
    async def answer_product_question(
        self,
        product_id: str,
        question: str,
    ) -> Dict[str, Any]:
        """
        Answer a question about a specific product using RAG.
        
        Args:
            product_id: Product ID
            question: User's question
            
        Returns:
            Answer with source information
        """
        # Get product with reviews
        product = await product_service.get_product(product_id, include_reviews=True)
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        # Build context from product data and reviews
        context_parts = [
            f"Product: {product['name']}",
            f"Brand: {product['brand']}",
            f"Category: {product['category']}",
            f"Price: ${product['price']}",
            f"Rating: {product.get('rating', 0)}/5 ({product.get('num_reviews', 0)} reviews)",
            f"In Stock: {product.get('count_in_stock', 0)} units",
            f"Description: {product.get('description', 'N/A')}",
        ]
        
        # Add review context
        reviews = product.get("reviews", [])
        if reviews:
            context_parts.append("\nCustomer Reviews:")
            for review in reviews[:10]:  # Limit to 10 reviews
                context_parts.append(
                    f"- {review.get('name', 'Anonymous')} ({review.get('rating', 0)}/5): {review.get('comment', '')}"
                )
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=settings.openai_key)
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful shopping assistant. Answer the customer's question "
                        "based ONLY on the product information provided. If the information "
                        "doesn't contain the answer, say so politely. Be concise and helpful."
                    )
                },
                {
                    "role": "user",
                    "content": f"Product Information:\n{context}\n\nCustomer Question: {question}"
                }
            ],
            temperature=0.5,
            max_tokens=500,
        )
        
        return {
            "product_id": product_id,
            "product_name": product["name"],
            "question": question,
            "answer": response.choices[0].message.content.strip(),
            "sources": {
                "product_details": True,
                "reviews_used": len(reviews[:10]),
            }
        }


# Singleton instance
rag_retriever = RAGRetriever()
