"""
LangChain-based RAG Service

Uses LangChain ecosystem for:
- OpenAI embeddings
- Pinecone vector store
- Retrieval chains
- Document processing
"""

from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from pinecone import Pinecone, ServerlessSpec
import asyncio
from functools import lru_cache

from config.settings import settings


# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDINGS
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache()
def get_embeddings() -> OpenAIEmbeddings:
    """Get cached OpenAI embeddings instance"""
    return OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        dimensions=settings.EMBEDDING_DIMENSION,
    )


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR STORE
# ─────────────────────────────────────────────────────────────────────────────

class ProductVectorStore:
    """
    LangChain Pinecone Vector Store for products.
    
    Handles:
    - Index initialization
    - Document upsert with metadata
    - Similarity search with filters
    """
    
    _instance: Optional["ProductVectorStore"] = None
    
    def __init__(self):
        self.embeddings = get_embeddings()
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX
        self.namespace = settings.PINECONE_NAMESPACE
        self._vector_store: Optional[PineconeVectorStore] = None
    
    @classmethod
    def get_instance(cls) -> "ProductVectorStore":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _ensure_index(self) -> None:
        """Ensure Pinecone index exists"""
        existing = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing:
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION,
                ),
            )
            # Wait for index to be ready
            import time
            while not self.pc.describe_index(self.index_name).status.ready:
                time.sleep(1)
    
    def initialize(self) -> PineconeVectorStore:
        """Initialize and return the vector store"""
        if self._vector_store is None:
            self._ensure_index()
            self._vector_store = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=self.namespace,
                pinecone_api_key=settings.PINECONE_API_KEY,
            )
        return self._vector_store
    
    @property
    def store(self) -> PineconeVectorStore:
        """Get the vector store, initializing if needed"""
        return self.initialize()
    
    def index_products(self, products: List[Dict[str, Any]]) -> int:
        """
        Index products into the vector store.
        
        Args:
            products: List of product dicts with _id, name, description, etc.
            
        Returns:
            Number of products indexed
        """
        documents = []
        
        for product in products:
            # Create rich text for embedding
            text = self._create_product_text(product)
            
            # Create metadata for filtering
            metadata = {
                "product_id": str(product.get("_id", "")),
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "price": float(product.get("price", 0)),
                "rating": float(product.get("rating", 0)),
                "count_in_stock": int(product.get("countInStock", 0)),
            }
            
            doc = Document(
                page_content=text,
                metadata=metadata,
            )
            documents.append(doc)
        
        if documents:
            # Use add_documents for batch upsert
            self.store.add_documents(documents)
        
        return len(documents)
    
    def _create_product_text(self, product: Dict[str, Any]) -> str:
        """Create searchable text from product data"""
        parts = [
            f"Product: {product.get('name', '')}",
            f"Brand: {product.get('brand', '')}",
            f"Category: {product.get('category', '')}",
            f"Description: {product.get('description', '')}",
            f"Price: ${product.get('price', 0):.2f}",
        ]
        
        # Add review highlights if available
        reviews = product.get("reviews", [])
        if reviews:
            review_texts = [r.get("comment", "") for r in reviews[:3]]
            if review_texts:
                parts.append(f"Reviews: {' | '.join(review_texts)}")
        
        return "\n".join(parts)
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Search for similar products.
        
        Args:
            query: Natural language search query
            k: Number of results
            filter_dict: Pinecone metadata filters
            
        Returns:
            List of matching documents with metadata
        """
        return self.store.similarity_search(
            query=query,
            k=k,
            filter=filter_dict,
        )
    
    def search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[Document, float]]:
        """Search with relevance scores"""
        return self.store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict,
        )
    
    def get_retriever(self, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None):
        """Get a retriever for use in chains"""
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        return self.store.as_retriever(search_kwargs=search_kwargs)
    
    def delete_by_ids(self, ids: List[str]) -> None:
        """Delete documents by ID"""
        self.store.delete(ids=ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        index = self.pc.Index(self.index_name)
        stats = index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "namespaces": dict(stats.namespaces) if stats.namespaces else {},
            "dimension": stats.dimension,
        }


# ─────────────────────────────────────────────────────────────────────────────
# RAG CHAINS
# ─────────────────────────────────────────────────────────────────────────────

def _format_docs(docs: List[Document]) -> str:
    """Format documents for context"""
    return "\n\n".join(doc.page_content for doc in docs)


class ProductRAGChain:
    """
    LangChain RAG chains for product Q&A using LCEL.
    
    Provides:
    - Simple retrieval
    - Q&A with context
    - Conversational retrieval
    """
    
    def __init__(self, vector_store: ProductVectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY,
        )
    
    def _create_qa_chain(self, retriever):
        """Create a Q&A chain using LCEL"""
        system_prompt = """You are a helpful shopping assistant for TweekySqueeky Shop.
Answer the question based ONLY on the following product information.
If you cannot answer from the context, say so politely.

Product Context:
{context}

Guidelines:
- Be concise and helpful
- Include specific product details (price, brand, features)
- If comparing products, create a clear comparison
- Recommend products that match the user's needs
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}"),
        ])
        
        # LCEL chain: retrieve docs -> format -> prompt -> llm -> parse
        chain = (
            RunnableParallel(
                context=retriever | _format_docs,
                question=RunnablePassthrough(),
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    async def ask(
        self,
        question: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ask a question about products.
        
        Returns:
            Dict with 'answer' and 'source_documents'
        """
        retriever = self.vector_store.get_retriever(k=k, filter_dict=filter_dict)
        
        # Get documents first for source tracking
        docs = await asyncio.to_thread(
            retriever.invoke,
            question
        )
        
        # Create and run chain
        chain = self._create_qa_chain(retriever)
        answer = await asyncio.to_thread(
            chain.invoke,
            question
        )
        
        return {
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in docs
            ],
        }
    
    def search_products(
        self,
        query: str,
        k: int = 5,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search products with optional filters.
        
        Returns product metadata and relevance scores.
        """
        # Build Pinecone filter
        filter_conditions = []
        
        if min_price is not None:
            filter_conditions.append({"price": {"$gte": min_price}})
        if max_price is not None:
            filter_conditions.append({"price": {"$lte": max_price}})
        if category:
            filter_conditions.append({"category": {"$eq": category}})
        if min_rating is not None:
            filter_conditions.append({"rating": {"$gte": min_rating}})
        
        filter_dict = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                filter_dict = filter_conditions[0]
            else:
                filter_dict = {"$and": filter_conditions}
        
        # Search with scores
        results = self.vector_store.search_with_scores(
            query=query,
            k=k,
            filter_dict=filter_dict,
        )
        
        return [
            {
                "product_id": doc.metadata.get("product_id"),
                "name": doc.metadata.get("name"),
                "brand": doc.metadata.get("brand"),
                "category": doc.metadata.get("category"),
                "price": doc.metadata.get("price"),
                "rating": doc.metadata.get("rating"),
                "score": 1 - score,  # Convert distance to similarity
                "content": doc.page_content,
            }
            for doc, score in results
        ]


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_vector_store() -> ProductVectorStore:
    """Get the singleton vector store instance"""
    return ProductVectorStore.get_instance()


def get_rag_chain() -> ProductRAGChain:
    """Get a RAG chain instance"""
    return ProductRAGChain(get_vector_store())


# ─────────────────────────────────────────────────────────────────────────────
# INDEXING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

async def index_all_products() -> Dict[str, Any]:
    """
    Index all products from the database into the vector store.
    
    Returns:
        Stats about the indexing operation
    """
    from services.product_service import product_service
    
    # Get all products as Beanie documents
    products_raw = await product_service.get_all_products_raw()
    
    if not products_raw:
        return {"status": "error", "message": "No products found"}
    
    # Convert Beanie documents to dicts
    products = []
    for p in products_raw:
        try:
            # Use model_dump for proper serialization
            p_dict = p.model_dump()
            product_dict = {
                "_id": str(p.id),
                "name": p_dict.get("name", ""),
                "brand": p_dict.get("brand", ""),
                "category": p_dict.get("category", ""),
                "description": p_dict.get("description", ""),
                "price": p_dict.get("price", 0),
                "rating": p_dict.get("rating", 0),
                "numReviews": p_dict.get("num_reviews", 0),
                "countInStock": p_dict.get("count_in_stock", 0),
                "reviews": [],  # Skip reviews for now
            }
            products.append(product_dict)
        except Exception as e:
            print(f"Warning: Could not convert product {p.id}: {e}")
            continue
    
    if not products:
        return {"status": "error", "message": "No products found"}
    
    # Index them
    vector_store = get_vector_store()
    count = await asyncio.to_thread(
        vector_store.index_products,
        products
    )
    
    # Get stats
    stats = vector_store.get_stats()
    
    return {
        "status": "success",
        "products_indexed": count,
        "total_vectors": stats.get("total_vectors", 0),
        "index_name": vector_store.index_name,
        "namespace": vector_store.namespace,
    }


async def index_single_product(product: Dict[str, Any]) -> bool:
    """Index a single product (for real-time updates)"""
    vector_store = get_vector_store()
    count = await asyncio.to_thread(
        vector_store.index_products,
        [product]
    )
    return count == 1
